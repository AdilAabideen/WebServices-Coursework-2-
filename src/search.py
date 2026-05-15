"""Search helpers for the inverted index."""

from __future__ import annotations

from collections.abc import Mapping

from src.indexer import tokenize
from src.models import InvertedIndex, Quote, TermInfo


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


def find_matching_quotes(
    document_metadata: Mapping[str, object],
    terms: list[str],
    *,
    limit: int = 2,
) -> list[Quote]:
    """Return up to `limit` quote snippets that match a query."""
    raw_quotes = document_metadata.get("quotes")
    if not isinstance(raw_quotes, list) or not terms:
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
        quote_terms = set(tokenize(searchable_text))

        if all(term in quote_terms for term in terms):
            exact_matches.append(quote)
        elif any(term in quote_terms for term in terms):
            partial_matches.append(quote)

    snippets = exact_matches if exact_matches else partial_matches
    return snippets[:limit]
