"""Tests for print and find CLI commands."""

from __future__ import annotations

from pathlib import Path

from src.indexer import Document, build_inverted_index
from src.main import main
from src.storage import save_index


def build_search_index(path: Path) -> None:
    index = build_inverted_index(
        [
            Document(
                document_id="doc-1",
                text="Good friends show kindness and indifference fades.",
                metadata={
                    "url": "https://quotes.toscrape.com/page/2/",
                    "quote_count": 2,
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
                text="Good habits matter more than good intentions.",
                metadata={
                    "url": "https://quotes.toscrape.com/page/5/",
                    "quote_count": 1,
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
                text="Friends help in difficult times.",
                metadata={
                    "url": "https://quotes.toscrape.com/page/8/",
                    "quote_count": 3,
                    "quotes": [
                        {
                            "text": "Friends help in difficult times.",
                            "author": "Example Author Two",
                            "tags": ["friends", "support"],
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


def test_find_missing_word(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    build_search_index(path)

    exit_code = main(["find", "missing", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert 'No results found for query: "missing".' in captured.out


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
    assert "Please provide a non-empty query." in captured.err


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
