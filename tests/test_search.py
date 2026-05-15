"""Tests for print and find CLI commands."""

from __future__ import annotations

from pathlib import Path

from src.indexer import Document, build_inverted_index
from src.main import build_highlight_targets, highlight_terms, main
from src.models import Quote
from src.query_parser import ParsedQuery, parse_query
from src.search import execute_query, find_matching_documents, find_matching_quotes
from src.storage import save_index


def build_search_index(path: Path) -> None:
    index = build_inverted_index(
        [
            Document(
                document_id="doc-1",
                text=(
                    "Good friends, good books, and a sleepy conscience: this is the ideal life. "
                    "Mark Twain books contentment friends friendship life "
                    "Indifference and neglect often do much more damage than outright dislike. "
                    "J.K. Rowling indifference opposite love"
                ),
                metadata={
                    "url": "https://quotes.toscrape.com/page/2/",
                    "quote_count": 2,
                    "authors": ["J.K. Rowling", "Mark Twain"],
                    "tags": [
                        "books",
                        "contentment",
                        "friends",
                        "friendship",
                        "indifference",
                        "life",
                        "love",
                        "opposite",
                    ],
                    "quotes": [
                        {
                            "text": "Good friends, good books, and a sleepy conscience: this is the ideal life.",
                            "author": "Mark Twain",
                            "tags": ["books", "contentment", "friends", "friendship", "life"],
                        },
                        {
                            "text": "Indifference and neglect often do much more damage than outright dislike.",
                            "author": "J.K. Rowling",
                            "tags": ["indifference", "opposite", "love"],
                        },
                    ],
                },
            ),
            Document(
                document_id="doc-2",
                text="Good habits matter more than good intentions. Example Author habits good",
                metadata={
                    "url": "https://quotes.toscrape.com/page/5/",
                    "quote_count": 1,
                    "authors": ["Example Author"],
                    "tags": ["good", "habits"],
                    "quotes": [
                        {
                            "text": "Good habits matter more than good intentions.",
                            "author": "Example Author",
                            "tags": ["habits", "good"],
                        }
                    ],
                },
            ),
            Document(
                document_id="doc-3",
                text="Friends help in difficult times. Example Author Two friends support",
                metadata={
                    "url": "https://quotes.toscrape.com/page/8/",
                    "quote_count": 3,
                    "authors": ["Example Author Two"],
                    "tags": ["friends", "support"],
                    "quotes": [
                        {
                            "text": "Friends help in difficult times.",
                            "author": "Example Author Two",
                            "tags": ["friends", "support"],
                        }
                    ],
                },
            ),
            Document(
                document_id="doc-4",
                text="Life rewards curiosity and patient thinking. Albert Einstein life science",
                metadata={
                    "url": "https://quotes.toscrape.com/page/9/",
                    "quote_count": 1,
                    "authors": ["Albert Einstein"],
                    "tags": ["life", "science"],
                    "quotes": [
                        {
                            "text": "Life rewards curiosity and patient thinking.",
                            "author": "Albert Einstein",
                            "tags": ["life", "science"],
                        }
                    ],
                },
            ),
        ]
    )
    save_index(index, path)


def test_print_existing_word(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    build_search_index(path)

    exit_code = main(["print", "good", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert 'Term: "good"' in captured.out
    assert "Document frequency: 2" in captured.out
    assert "doc-1" in captured.out
    assert "doc-2" in captured.out


def test_print_missing_word(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    build_search_index(path)

    exit_code = main(["print", "nonsense", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert 'No postings found for "nonsense".' in captured.out


def test_print_uppercase_word_normalizes_case(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    build_search_index(path)

    exit_code = main(["print", "GOOD", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert 'Term: "good"' in captured.out


def test_print_punctuation_only_word_is_handled(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    build_search_index(path)

    exit_code = main(["print", "!!!", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Please provide a non-empty word to print." in captured.err


def test_print_missing_index_file(tmp_path: Path, capsys) -> None:
    path = tmp_path / "missing.json"

    exit_code = main(["print", "good", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Index file not found" in captured.err


def test_print_corrupt_index_file(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    path.write_text("{bad-json", encoding="utf-8")

    exit_code = main(["print", "good", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Index file is corrupt" in captured.err


def test_find_single_word(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    build_search_index(path)

    exit_code = main(["find", "indifference", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert 'Results for query: "indifference"' in captured.out
    assert "https://quotes.toscrape.com/page/2/" in captured.out
    assert "Indifference and neglect often do much more damage than outright dislike." in captured.out
    assert "https://quotes.toscrape.com/page/5/" not in captured.out


def test_find_multi_word_query(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    build_search_index(path)

    exit_code = main(["find", "good", "friends", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert 'Results for query: "good friends"' in captured.out
    assert "https://quotes.toscrape.com/page/2/" in captured.out
    assert "Good friends, good books, and a sleepy conscience: this is the ideal life." in captured.out
    assert "Author: Mark Twain" in captured.out
    assert "https://quotes.toscrape.com/page/5/" not in captured.out
    assert "https://quotes.toscrape.com/page/8/" not in captured.out


def test_find_exact_phrase_query_uses_adjacent_positions(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    build_search_index(path)

    exit_code = main(["find", "good friends", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert 'Results for query: "good friends"' in captured.out
    assert "https://quotes.toscrape.com/page/2/" in captured.out
    assert "Good friends, good books, and a sleepy conscience: this is the ideal life." in captured.out
    assert "https://quotes.toscrape.com/page/5/" not in captured.out
    assert "https://quotes.toscrape.com/page/8/" not in captured.out
    assert "https://quotes.toscrape.com/page/9/" not in captured.out


def test_phrase_query_rejects_non_adjacent_terms() -> None:
    index = build_inverted_index(
        [
            Document(document_id="doc-1", text="good friends make life better"),
            Document(document_id="doc-2", text="good habits build strong friends"),
        ]
    )

    matches = execute_query(index, parse_query('"good friends"'))

    assert matches == ["doc-1"]


def test_find_matching_documents_handles_empty_and_missing_terms() -> None:
    index = build_inverted_index([Document(document_id="doc-1", text="good friends")])

    assert find_matching_documents(index, "") == []
    assert find_matching_documents(index, "missing") == []


def test_find_matching_documents_returns_and_matches() -> None:
    index = build_inverted_index(
        [
            Document(document_id="doc-1", text="good friends"),
            Document(document_id="doc-2", text="good habits"),
        ]
    )

    assert find_matching_documents(index, "good friends") == ["doc-1"]


def test_execute_query_handles_no_positive_clauses() -> None:
    index = build_inverted_index([Document(document_id="doc-1", text="good friends")])
    empty_query = ParsedQuery(
        mode="and",
        terms=[],
        phrases=[],
        excluded_terms=[],
        author_filters=[],
        tag_filters=[],
    )

    assert execute_query(index, empty_query) == []


def test_find_or_query_returns_union_of_results(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    build_search_index(path)

    exit_code = main(["find", "good", "OR", "friends", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert 'Results for query: "good OR friends"' in captured.out
    assert "https://quotes.toscrape.com/page/2/" in captured.out
    assert "https://quotes.toscrape.com/page/5/" in captured.out
    assert "https://quotes.toscrape.com/page/8/" in captured.out


def test_find_exclusion_query_removes_matching_pages(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    build_search_index(path)

    exit_code = main(["find", "good", "-friends", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert 'Results for query: "good -friends"' in captured.out
    assert "https://quotes.toscrape.com/page/5/" in captured.out
    assert "https://quotes.toscrape.com/page/2/" not in captured.out


def test_find_author_filter_uses_document_metadata(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    build_search_index(path)

    exit_code = main(["find", "author:einstein", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert 'Results for query: "author:einstein"' in captured.out
    assert "https://quotes.toscrape.com/page/9/" in captured.out
    assert "Albert Einstein" in captured.out
    assert "score=N/A" in captured.out
    assert "score=0.0000" not in captured.out
    assert "https://quotes.toscrape.com/page/2/" not in captured.out


def test_find_tag_filter_uses_document_metadata(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    build_search_index(path)

    exit_code = main(["find", "tag:life", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert 'Results for query: "tag:life"' in captured.out
    assert "https://quotes.toscrape.com/page/2/" in captured.out
    assert "https://quotes.toscrape.com/page/9/" in captured.out
    assert "score=N/A" in captured.out


def test_find_uppercase_query_is_case_insensitive(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    build_search_index(path)

    exit_code = main(["find", "GOOD", "FRIENDS", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert 'Results for query: "good friends"' in captured.out
    assert "https://quotes.toscrape.com/page/2/" in captured.out


def test_find_single_term_results_are_ranked(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    build_search_index(path)

    exit_code = main(["find", "good", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "score=" in captured.out
    assert captured.out.index("https://quotes.toscrape.com/page/5/") < captured.out.index(
        "https://quotes.toscrape.com/page/2/"
    )


def test_find_love_still_returns_results(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    build_search_index(path)

    exit_code = main(["find", "love", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert 'Results for query: "love"' in captured.out
    assert "https://quotes.toscrape.com/page/2/" in captured.out


def test_find_missing_quote_metadata_does_not_crash_output(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    index = build_inverted_index(
        [
            Document(
                document_id="doc-1",
                text="love friendship",
                metadata={"url": "https://quotes.toscrape.com/page/2/", "quote_count": 1},
            )
        ]
    )
    save_index(index, path)

    exit_code = main(["find", "love", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "https://quotes.toscrape.com/page/2/" in captured.out
    assert "score=" in captured.out


def test_find_matching_quotes_skips_malformed_payloads_and_returns_partial_matches() -> None:
    metadata = {
        "quotes": [
            "bad-payload",
            {
                "text": "Friendship matters most",
                "author": "Author One",
                "tags": ["support"],
            },
        ]
    }

    matches = find_matching_quotes(metadata, parse_query("support"))

    assert len(matches) == 1
    assert matches[0] == Quote(
        text="Friendship matters most",
        author="Author One",
        tags=["support"],
    )


def test_find_matching_quotes_handles_invalid_quote_structure() -> None:
    metadata = {"quotes": [{"text": "Love", "author": "Author One"}]}

    matches = find_matching_quotes(metadata, parse_query("love"))

    assert matches == []


def test_find_missing_word(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    build_search_index(path)

    exit_code = main(["find", "missing", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert 'No results found for query: "missing".' in captured.out


def test_find_missing_word_shows_suggestion_when_available(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    build_search_index(path)

    exit_code = main(["find", "frends", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert 'No results found for query: "frends".' in captured.out
    assert 'Did you mean: "friends"?' in captured.out


def test_highlight_terms_single_term() -> None:
    highlighted = highlight_terms("Love is beautiful", ["love"], use_colour=False)

    assert "[Love]" in highlighted


def test_highlight_terms_is_case_insensitive() -> None:
    highlighted = highlight_terms("Good friends", ["good"], use_colour=False)

    assert "[Good]" in highlighted


def test_highlight_terms_multi_word() -> None:
    highlighted = highlight_terms(
        "Good friends are good",
        ["good", "friends"],
        use_colour=False,
    )

    assert "[Good]" in highlighted
    assert "[friends]" in highlighted


def test_boolean_operator_is_not_highlighted() -> None:
    query = parse_query("good OR friends")
    highlighted = highlight_terms(
        "Good friends are good",
        build_highlight_targets(query),
        use_colour=False,
    )

    assert "[Good]" in highlighted
    assert "[friends]" in highlighted
    assert "[OR]" not in highlighted


def test_exclusion_term_is_not_highlighted() -> None:
    query = parse_query("good -friends")
    highlighted = highlight_terms(
        "Good friends are good",
        build_highlight_targets(query),
        use_colour=False,
    )

    assert "[Good]" in highlighted
    assert "[friends]" not in highlighted


def test_metadata_filter_terms_are_not_highlighted() -> None:
    query = parse_query("author:einstein")
    highlighted = highlight_terms(
        "Albert Einstein wrote about life",
        build_highlight_targets(query),
        use_colour=False,
    )

    assert highlighted == "Albert Einstein wrote about life"


def test_phrase_query_prefers_phrase_highlighting() -> None:
    query = parse_query('"good friends"')
    highlighted = highlight_terms(
        "Good friends, good books",
        build_highlight_targets(query),
        use_colour=False,
    )

    assert "[Good friends]" in highlighted


def test_find_empty_query(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    build_search_index(path)

    exit_code = main(["find", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Please provide a non-empty query." in captured.err


def test_find_punctuation_only_query(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    build_search_index(path)

    exit_code = main(["find", "!!!", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Query term must contain at least one searchable character." in captured.err


def test_find_invalid_or_syntax_is_handled_gracefully(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    build_search_index(path)

    exit_code = main(["find", "good", "OR", "OR", "friends", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "OR must appear between valid query clauses." in captured.err


def test_find_unmatched_quote_is_handled_gracefully(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    build_search_index(path)

    exit_code = main(["find", '"good friends', "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "unmatched quote" in captured.err


def test_find_leading_or_is_handled_gracefully(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    build_search_index(path)

    exit_code = main(["find", "OR", "friends", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "OR must appear between valid query clauses." in captured.err


def test_find_empty_author_filter_is_handled_gracefully(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    build_search_index(path)

    exit_code = main(["find", "author:", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Author filter must include a value." in captured.err


def test_find_empty_tag_filter_is_handled_gracefully(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    build_search_index(path)

    exit_code = main(["find", "tag:", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Tag filter must include a value." in captured.err


def test_find_trailing_or_is_handled_gracefully(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    build_search_index(path)

    exit_code = main(["find", "good", "OR", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "OR must appear between valid query clauses." in captured.err


def test_find_exclusion_only_is_handled_gracefully(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    build_search_index(path)

    exit_code = main(["find", "-friends", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Please provide at least one searchable term or filter." in captured.err


def test_find_long_snippets_are_truncated_in_output(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    long_quote = (
        "This life is what you make it and good friends help you keep going even when the road is long "
        "because the people who stay with you through difficult seasons matter more than temporary noise "
        "and the story keeps unfolding with patience, humor, and courage."
    )
    index = build_inverted_index(
        [
            Document(
                document_id="doc-long",
                text=f"{long_quote} Long Author life friendship courage",
                metadata={
                    "url": "https://quotes.toscrape.com/page/long/",
                    "quote_count": 1,
                    "authors": ["Long Author"],
                    "tags": ["life", "friendship", "courage"],
                    "quotes": [
                        {
                            "text": long_quote,
                            "author": "Long Author",
                            "tags": ["life", "friendship", "courage"],
                        }
                    ],
                },
            )
        ]
    )
    save_index(index, path)

    exit_code = main(["find", "life", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "..." in captured.out
    assert long_quote not in captured.out


def test_find_missing_index_file(tmp_path: Path, capsys) -> None:
    path = tmp_path / "missing.json"

    exit_code = main(["find", "good", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Index file not found" in captured.err


def test_find_corrupt_index_file(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    path.write_text("{bad-json", encoding="utf-8")

    exit_code = main(["find", "good", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Index file is corrupt" in captured.err
