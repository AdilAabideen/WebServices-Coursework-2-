"""Tests for query suggestions.

Test type: unit tests for edit-distance suggestions, ranking, and correction rebuilding.
"""

from __future__ import annotations

from src.indexer import Document, build_inverted_index
from src.query_parser import parse_query
from src.suggest import levenshtein_distance, suggest_query, suggest_terms


def build_suggest_index():
    """Create a compact index for suggestion tests."""
    return build_inverted_index(
        [
            Document(document_id="doc-1", text="friends friends friends friendship"),
            Document(document_id="doc-2", text="friendship friendly life"),
            Document(document_id="doc-3", text="indifference love life"),
        ]
    )


# Unit test for typo returns nearest word.
def test_typo_returns_nearest_word() -> None:
    index = build_suggest_index()

    suggestions = suggest_terms(index, "frends")

    assert suggestions
    assert suggestions[0].term == "friends"


# Unit test for exact word returns no suggestion needed.
def test_exact_word_returns_no_suggestion_needed() -> None:
    index = build_suggest_index()

    assert suggest_terms(index, "friends") == []


# Unit test for unrelated word returns no suggestion.
def test_unrelated_word_returns_no_suggestion() -> None:
    index = build_suggest_index()

    assert suggest_terms(index, "xylophone") == []


# Unit test for suggestions are sorted by edit distance and frequency.
def test_suggestions_are_sorted_by_edit_distance_and_frequency() -> None:
    index = build_suggest_index()

    suggestions = suggest_terms(index, "friendsip", limit=3)

    assert [suggestion.term for suggestion in suggestions][:2] == ["friendship", "friends"]


# Unit test for levenshtein distance counts basic edits.
def test_levenshtein_distance_counts_basic_edits() -> None:
    assert levenshtein_distance("friends", "frends") == 1
    assert levenshtein_distance("love", "life") == 2
    assert levenshtein_distance("", "abc") == 3
    assert levenshtein_distance("abc", "") == 3
    assert levenshtein_distance("same", "same") == 0


# Unit test for query suggestion rebuilds multi term query.
def test_query_suggestion_rebuilds_multi_term_query() -> None:
    index = build_suggest_index()

    suggested = suggest_query(index, parse_query("good frends"))

    assert suggested == "good friends"


# Unit test for query suggestion handles phrase and filters.
def test_query_suggestion_handles_phrase_and_filters() -> None:
    index = build_suggest_index()

    suggested = suggest_query(index, parse_query('"frends life" author:einstein tag:life -missing'))

    assert suggested == '"friends life" author:einstein tag:life -missing'


# Unit test for query suggestion returns none when nothing changes.
def test_query_suggestion_returns_none_when_nothing_changes() -> None:
    index = build_suggest_index()

    assert suggest_query(index, parse_query("friends")) is None


# Unit test for query suggestion preserves or separator.
def test_query_suggestion_preserves_or_separator() -> None:
    index = build_suggest_index()

    suggested = suggest_query(index, parse_query("frends OR life"))

    assert suggested == "friends OR life"
