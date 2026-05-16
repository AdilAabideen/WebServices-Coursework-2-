"""Tests for advanced query parsing.

Test type: unit tests for query parsing syntax, normalization, and parser error handling.
"""

from __future__ import annotations

import pytest

from src.exceptions import QuerySyntaxError
from src.query_parser import parse_query


# Unit test for phrase query is parsed as phrase clause.
def test_phrase_query_is_parsed_as_phrase_clause() -> None:
    parsed = parse_query('"good friends"')

    assert parsed.mode == "and"
    assert parsed.phrases == [["good", "friends"]]
    assert parsed.terms == []


# Unit test for or query is parsed as union mode.
def test_or_query_is_parsed_as_union_mode() -> None:
    parsed = parse_query("good OR friends")

    assert parsed.mode == "or"
    assert parsed.terms == ["good", "friends"]


# Unit test for exclusion query is parsed.
def test_exclusion_query_is_parsed() -> None:
    parsed = parse_query("good -friends")

    assert parsed.mode == "and"
    assert parsed.terms == ["good"]
    assert parsed.excluded_terms == ["friends"]


# Unit test for author and tag filters are parsed.
def test_author_and_tag_filters_are_parsed() -> None:
    parsed = parse_query("author:einstein tag:life")

    assert parsed.author_filters == [["einstein"]]
    assert parsed.tag_filters == [["life"]]


# Unit test for invalid or syntax raises helpful error.
def test_invalid_or_syntax_raises_helpful_error() -> None:
    with pytest.raises(QuerySyntaxError, match="OR must appear between valid query clauses."):
        parse_query("good OR OR friends")


# Unit test for unmatched quote raises helpful error.
def test_unmatched_quote_raises_helpful_error() -> None:
    with pytest.raises(QuerySyntaxError, match="unmatched quote"):
        parse_query('"good friends')


# Unit test for empty author filter raises helpful error.
def test_empty_author_filter_raises_helpful_error() -> None:
    with pytest.raises(QuerySyntaxError, match="Author filter must include a value."):
        parse_query("author:")


# Unit test for empty tag filter raises helpful error.
def test_empty_tag_filter_raises_helpful_error() -> None:
    with pytest.raises(QuerySyntaxError, match="Tag filter must include a value."):
        parse_query("tag:")


# Unit test for exclusion only query raises helpful error.
def test_exclusion_only_query_raises_helpful_error() -> None:
    with pytest.raises(QuerySyntaxError, match="Please provide at least one searchable term or filter."):
        parse_query("-friends")
