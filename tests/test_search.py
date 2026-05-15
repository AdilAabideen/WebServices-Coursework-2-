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
                metadata={"url": "https://example.com/doc-1", "quote_count": 2},
            ),
            Document(
                document_id="doc-2",
                text="Good habits matter more than good intentions.",
                metadata={"url": "https://example.com/doc-2", "quote_count": 1},
            ),
            Document(
                document_id="doc-3",
                text="Friends help in difficult times.",
                metadata={"url": "https://example.com/doc-3", "quote_count": 3},
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
    assert "https://example.com/doc-1" in captured.out
    assert "https://example.com/doc-2" not in captured.out


def test_find_multi_word_query(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    build_search_index(path)

    exit_code = main(["find", "good", "friends", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert 'Results for query: "good friends"' in captured.out
    assert "https://example.com/doc-1" in captured.out
    assert "https://example.com/doc-2" not in captured.out
    assert "https://example.com/doc-3" not in captured.out


def test_find_uppercase_query_is_case_insensitive(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    build_search_index(path)

    exit_code = main(["find", "GOOD", "FRIENDS", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert 'Results for query: "good friends"' in captured.out
    assert "https://example.com/doc-1" in captured.out


def test_find_single_term_results_are_ranked(tmp_path: Path, capsys) -> None:
    path = tmp_path / "index.json"
    build_search_index(path)

    exit_code = main(["find", "good", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "score=" in captured.out
    assert captured.out.index("https://example.com/doc-2") < captured.out.index(
        "https://example.com/doc-1"
    )


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
