"""Ranking helpers for search results."""

from __future__ import annotations

from src.models import InvertedIndex, RankedDocument


def rank_documents(
    index: InvertedIndex,
    document_ids: list[str],
    terms: list[str],
) -> list[RankedDocument]:
    """Rank documents by summed term frequency for the query terms."""
    ranked = []
    for document_id in document_ids:
        score = sum(
            index.terms[term].postings[document_id].frequency
            for term in terms
            if document_id in index.terms[term].postings
        )
        ranked.append(RankedDocument(document_id=document_id, score=score))

    return sorted(ranked, key=lambda item: (-item.score, item.document_id))
