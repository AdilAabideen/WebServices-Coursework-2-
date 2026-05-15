"""Ranking helpers for search results."""

from __future__ import annotations

import math

from src.models import InvertedIndex, RankedDocument


def term_frequency(index: InvertedIndex, term: str, document_id: str) -> float:
    """Return the raw term frequency for a term in a document."""
    term_info = index.terms.get(term)
    if term_info is None:
        return 0.0

    posting = term_info.postings.get(document_id)
    if posting is None:
        return 0.0

    return float(posting.frequency)


def inverse_document_frequency(index: InvertedIndex, term: str) -> float:
    """Return the smoothed inverse document frequency for a term."""
    term_info = index.terms.get(term)
    if term_info is None or term_info.document_frequency == 0:
        return 0.0

    return math.log(index.document_count / term_info.document_frequency) + 1.0


def score_document(index: InvertedIndex, document_id: str, terms: list[str]) -> float:
    """Compute a TF-IDF score for a document against the query terms."""
    return sum(
        term_frequency(index, term, document_id) * inverse_document_frequency(index, term)
        for term in terms
    )


def rank_documents(
    index: InvertedIndex,
    document_ids: list[str],
    terms: list[str],
) -> list[RankedDocument]:
    """Rank documents by descending TF-IDF score for the query terms."""
    ranked = []
    for document_id in document_ids:
        score = score_document(index, document_id, terms)
        ranked.append(RankedDocument(document_id=document_id, score=score))

    return sorted(ranked, key=lambda item: (-item.score, item.document_id))
