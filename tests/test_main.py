"""Tests for build and load CLI commands."""

from __future__ import annotations

from pathlib import Path

from src.main import main
from src.models import PageContent, Quote


def test_build_command_crawls_indexes_and_saves(tmp_path: Path, monkeypatch, capsys) -> None:
    class FakeCrawler:
        def __init__(self, start_url: str, delay_seconds: float) -> None:
            self.start_url = start_url
            self.delay_seconds = delay_seconds

        def crawl(self, *, max_pages: int | None = None) -> list[PageContent]:
            assert max_pages == 1
            return [
                PageContent(
                    url="https://quotes.toscrape.com/",
                    quotes=[
                        Quote(
                            text="Test quote",
                            author="Author One",
                            tags=["tag-a", "tag-b"],
                        )
                    ],
                    next_page=None,
                )
            ]

    output_path = tmp_path / "index.json"
    monkeypatch.setattr("src.main.Crawler", FakeCrawler)

    exit_code = main(["build", "--max-pages", "1", "--output", str(output_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert output_path.exists()
    assert "Saved index" in captured.out
    assert "Documents indexed: 1" in captured.out


def test_load_command_loads_saved_index(tmp_path: Path, capsys) -> None:
    from src.indexer import Document, build_inverted_index
    from src.storage import save_index

    path = tmp_path / "index.json"
    index = build_inverted_index([Document(document_id="doc-1", text="alpha beta")])
    save_index(index, path)

    exit_code = main(["load", "--path", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Loaded index" in captured.out
    assert "Documents indexed: 1" in captured.out
    assert "Terms indexed: 2" in captured.out


def test_load_command_handles_missing_file(tmp_path: Path, capsys) -> None:
    missing_path = tmp_path / "missing.json"

    exit_code = main(["load", "--path", str(missing_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Index file not found" in captured.err


def test_load_command_handles_corrupt_file(tmp_path: Path, capsys) -> None:
    corrupt_path = tmp_path / "corrupt.json"
    corrupt_path.write_text("{bad-json", encoding="utf-8")

    exit_code = main(["load", "--path", str(corrupt_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Index file is corrupt" in captured.err


def test_main_handles_empty_command(capsys) -> None:
    exit_code = main([])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "usage: python -m src.main" in captured.err


def test_main_handles_unknown_command(capsys) -> None:
    exit_code = main(["unknown-command"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "invalid choice" in captured.err
