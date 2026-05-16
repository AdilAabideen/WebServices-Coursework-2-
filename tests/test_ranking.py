"""Tests for TF-IDF ranking behavior.

Test type: unit tests for ranking math, scoring order, and IDF weighting behavior.
"""

from __future__ import annotations

from src.indexer import Document, build_inverted_index
from src.ranking import (
    inverse_document_frequency,
    rank_documents,
    score_document,
    term_frequency,
)


def build_rank_index():
    return build_inverted_index(
        [
            Document(document_id="doc-1", text="common common rare"),
            Document(document_id="doc-2", text="common common common"),
            Document(document_id="doc-3", text="common"),
        ]
    )


# Unit test for higher term frequency gives higher score.
def test_higher_term_frequency_gives_higher_score() -> None:
    index = build_rank_index()

    assert term_frequency(index, "common", "doc-2") > term_frequency(index, "common", "doc-1")
    assert score_document(index, "doc-2", ["common"]) > score_document(index, "doc-1", ["common"])


# Unit test for rare terms get higher idf.
def test_rare_terms_get_higher_idf() -> None:
    index = build_rank_index()

    assert inverse_document_frequency(index, "rare") > inverse_document_frequency(index, "common")


# Unit test for smoothed idf formula is used.
def test_smoothed_idf_formula_is_used() -> None:
    index = build_rank_index()

    assert inverse_document_frequency(index, "rare") == 1.6931471805599454


# Unit test for documents are sorted by descending score.
def test_documents_are_sorted_by_descending_score() -> None:
    index = build_rank_index()

    ranked = rank_documents(index, ["doc-1", "doc-2", "doc-3"], ["common"])

    assert [result.document_id for result in ranked] == ["doc-2", "doc-1", "doc-3"]


# Unit test for missing terms do not crash ranker.
def test_missing_terms_do_not_crash_ranker() -> None:
    index = build_rank_index()

    ranked = rank_documents(index, ["doc-1", "doc-2"], ["missing"])

    assert [result.document_id for result in ranked] == ["doc-1", "doc-2"]
    assert all(result.score == 0.0 for result in ranked)


# Unit test for document with rare term can beat raw frequency only order.
def test_document_with_rare_term_can_beat_raw_frequency_only_order() -> None:
    index = build_rank_index()

    assert score_document(index, "doc-1", ["common", "rare"]) > score_document(
        index, "doc-2", ["common", "rare"]
    )
