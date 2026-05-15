"""Search helpers for the inverted index."""

from __future__ import annotations

from collections.abc import Mapping

from src.indexer import tokenize
from src.models import InvertedIndex, Quote, TermInfo
from src.query_parser import ParsedQuery


def normalize_query_terms(query: str) -> list[str]:
    """Normalize a query string into searchable terms."""
    return tokenize(query)


def get_term_info(index: InvertedIndex, term: str) -> TermInfo | None:
    """Return term information for a normalized lookup term."""
    normalized_terms = normalize_query_terms(term)
    if not normalized_terms:
        return None
    return index.terms.get(normalized_terms[0])


def find_matching_documents(index: InvertedIndex, query: str) -> list[str]:
    """Return documents that contain all normalized query terms."""
    terms = normalize_query_terms(query)
    if not terms:
        return []

    postings_sets = []
    for term in terms:
        term_info = index.terms.get(term)
        if term_info is None:
            return []
        postings_sets.append(set(term_info.postings))

    matching_ids = set.intersection(*postings_sets)
    return sorted(matching_ids)


def execute_query(index: InvertedIndex, query: ParsedQuery) -> list[str]:
    """Evaluate a parsed query against the inverted index."""
    clause_sets: list[set[str]] = []

    clause_sets.extend(_term_clause_sets(index, query.terms))
    clause_sets.extend(_phrase_clause_sets(index, query.phrases))
    clause_sets.extend(_author_filter_sets(index, query.author_filters))
    clause_sets.extend(_tag_filter_sets(index, query.tag_filters))

    if not clause_sets:
        return []

    if query.mode == "or":
        matches = set().union(*clause_sets)
    else:
        matches = set.intersection(*clause_sets)

    for excluded_term in query.excluded_terms:
        term_info = index.terms.get(excluded_term)
        if term_info is not None:
            matches.difference_update(term_info.postings.keys())

    return sorted(matches)


def find_matching_quotes(
    document_metadata: Mapping[str, object],
    query: ParsedQuery,
    *,
    limit: int = 2,
) -> list[Quote]:
    """Return up to `limit` quote snippets that match a query."""
    raw_quotes = document_metadata.get("quotes")
    if not isinstance(raw_quotes, list):
        return []

    exact_matches: list[Quote] = []
    partial_matches: list[Quote] = []

    for payload in raw_quotes:
        if not isinstance(payload, Mapping):
            continue
        try:
            quote = Quote.from_dict(payload)
        except Exception:
            continue

        searchable_text = " ".join([quote.text, quote.author, *quote.tags])
        quote_tokens = tokenize(searchable_text)
        if _quote_matches_query(quote, quote_tokens, query):
            exact_matches.append(quote)
        elif _quote_matches_any_positive_clause(quote, quote_tokens, query):
            partial_matches.append(quote)

    snippets = exact_matches if exact_matches else partial_matches
    return snippets[:limit]


def _term_clause_sets(index: InvertedIndex, terms: list[str]) -> list[set[str]]:
    """Return document sets for basic term clauses."""
    clause_sets: list[set[str]] = []
    for term in terms:
        term_info = index.terms.get(term)
        clause_sets.append(set(term_info.postings) if term_info is not None else set())
    return clause_sets


def _phrase_clause_sets(index: InvertedIndex, phrases: list[list[str]]) -> list[set[str]]:
    """Return document sets for exact phrase clauses using positional postings."""
    return [_documents_matching_phrase(index, phrase) for phrase in phrases]


def _documents_matching_phrase(index: InvertedIndex, phrase_terms: list[str]) -> set[str]:
    """Return documents whose postings contain the phrase at adjacent positions."""
    if not phrase_terms:
        return set()

    term_infos = [index.terms.get(term) for term in phrase_terms]
    if any(term_info is None for term_info in term_infos):
        return set()

    resolved_term_infos = [term_info for term_info in term_infos if term_info is not None]
    if len(resolved_term_infos) != len(term_infos):
        return set()

    common_docs = set(resolved_term_infos[0].postings)
    for term_info in resolved_term_infos[1:]:
        common_docs.intersection_update(term_info.postings)

    matches: set[str] = set()
    for document_id in common_docs:
        base_positions = set(resolved_term_infos[0].postings[document_id].positions)
        candidate_positions = set(base_positions)
        for offset, term_info in enumerate(resolved_term_infos[1:], start=1):
            positions = set(term_info.postings[document_id].positions)
            candidate_positions = {
                position for position in candidate_positions if (position + offset) in positions
            }
            if not candidate_positions:
                break
        if candidate_positions:
            matches.add(document_id)

    return matches


def _author_filter_sets(index: InvertedIndex, filters: list[list[str]]) -> list[set[str]]:
    """Return document sets matching author metadata filters."""
    return [_documents_matching_author_filter(index, tokens) for tokens in filters]


def _documents_matching_author_filter(index: InvertedIndex, tokens: list[str]) -> set[str]:
    """Return documents whose author metadata matches all filter tokens."""
    matches: set[str] = set()
    for document_id, metadata in index.documents.items():
        raw_authors = metadata.get("authors", [])
        if not isinstance(raw_authors, list):
            continue
        if any(_tokens_match_text(tokens, str(author)) for author in raw_authors):
            matches.add(document_id)
    return matches


def _tag_filter_sets(index: InvertedIndex, filters: list[list[str]]) -> list[set[str]]:
    """Return document sets matching tag metadata filters."""
    return [_documents_matching_tag_filter(index, tokens) for tokens in filters]


def _documents_matching_tag_filter(index: InvertedIndex, tokens: list[str]) -> set[str]:
    """Return documents whose tag metadata matches all filter tokens."""
    matches: set[str] = set()
    for document_id, metadata in index.documents.items():
        raw_tags = metadata.get("tags", [])
        if not isinstance(raw_tags, list):
            continue
        if any(_tokens_match_text(tokens, str(tag)) for tag in raw_tags):
            matches.add(document_id)
    return matches


def _tokens_match_text(tokens: list[str], value: str) -> bool:
    """Return whether all tokens appear in the normalized text value."""
    normalized = set(tokenize(value))
    return all(token in normalized for token in tokens)


def _quote_matches_query(quote: Quote, quote_tokens: list[str], query: ParsedQuery) -> bool:
    """Return whether a quote satisfies all positive query clauses."""
    if query.mode == "or":
        matched = _quote_matches_any_positive_clause(quote, quote_tokens, query)
    else:
        matched = (
            all(term in set(quote_tokens) for term in query.terms)
            and all(_quote_matches_phrase(quote_tokens, phrase) for phrase in query.phrases)
            and all(_tokens_match_text(tokens, quote.author) for tokens in query.author_filters)
            and all(any(_tokens_match_text(tokens, tag) for tag in quote.tags) for tokens in query.tag_filters)
        )

    if not matched:
        return False

    return not any(excluded in set(quote_tokens) for excluded in query.excluded_terms)


def _quote_matches_any_positive_clause(quote: Quote, quote_tokens: list[str], query: ParsedQuery) -> bool:
    """Return whether a quote satisfies any positive clause in an OR query."""
    token_set = set(quote_tokens)

    return (
        any(term in token_set for term in query.terms)
        or any(_quote_matches_phrase(quote_tokens, phrase) for phrase in query.phrases)
        or any(_tokens_match_text(tokens, quote.author) for tokens in query.author_filters)
        or any(any(_tokens_match_text(tokens, tag) for tag in quote.tags) for tokens in query.tag_filters)
    )


def _quote_matches_phrase(quote_tokens: list[str], phrase_terms: list[str]) -> bool:
    """Return whether phrase terms appear adjacently in quote tokens."""
    if not phrase_terms or len(phrase_terms) > len(quote_tokens):
        return False

    window = len(phrase_terms)
    return any(quote_tokens[index:index + window] == phrase_terms for index in range(len(quote_tokens) - window + 1))
