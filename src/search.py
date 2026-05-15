"""Search helpers for the inverted index."""

from __future__ import annotations

from src.indexer import tokenize
from src.models import InvertedIndex, TermInfo


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
