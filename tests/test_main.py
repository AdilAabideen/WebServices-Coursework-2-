"""Tests for build and load CLI commands.

Test type: integration-style CLI tests with mocked crawler orchestration and regression checks.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from src.exceptions import ProjectError
from src.main import (
    build_find_results,
    format_relevance_label,
    format_snippet_for_display,
    main,
    render_query_for_output,
    run_crawl,
)
from src.models import PageContent, Quote
from src.query_parser import parse_query


# Integration-style test for build command crawls indexes and saves.
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


# Integration-style test for load command loads saved index.
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


# Integration-style test for load command handles missing file.
def test_load_command_handles_missing_file(tmp_path: Path, capsys) -> None:
    missing_path = tmp_path / "missing.json"

    exit_code = main(["load", "--path", str(missing_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Index file not found" in captured.err


# Integration-style test for load command handles corrupt file.
def test_load_command_handles_corrupt_file(tmp_path: Path, capsys) -> None:
    corrupt_path = tmp_path / "corrupt.json"
    corrupt_path.write_text("{bad-json", encoding="utf-8")

    exit_code = main(["load", "--path", str(corrupt_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Index file is corrupt" in captured.err


# Integration-style test for main handles empty command.
def test_main_handles_empty_command(capsys) -> None:
    exit_code = main([])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "usage: python -m src.main" in captured.err


# Integration-style test for main handles unknown command.
def test_main_handles_unknown_command(capsys) -> None:
    exit_code = main(["unknown-command"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "invalid choice" in captured.err


# Integration-style test for run crawl prints first quote.
def test_run_crawl_prints_first_quote(monkeypatch, capsys) -> None:
    class FakeCrawler:
        def __init__(self, start_url: str, delay_seconds: float) -> None:
            self.start_url = start_url
            self.delay_seconds = delay_seconds
            self.visited_urls = {"https://quotes.toscrape.com/"}

        def crawl(self, *, max_pages: int | None = None) -> list[PageContent]:
            assert max_pages == 1
            return [
                PageContent(
                    url="https://quotes.toscrape.com/",
                    quotes=[
                        Quote(
                            text="First quote",
                            author="Author One",
                            tags=["tag-a"],
                        )
                    ],
                    next_page=None,
                )
            ]

    monkeypatch.setattr("src.main.Crawler", FakeCrawler)
    args = argparse.Namespace(
        start_url="https://quotes.toscrape.com/",
        delay=6.0,
        max_pages=1,
    )

    exit_code = run_crawl(args)
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Pages crawled: 1" in captured.out
    assert "First page: https://quotes.toscrape.com/" in captured.out
    assert "First quote: First quote - Author One" in captured.out


# Integration-style test for build find results metadata only returns zero scores.
def test_build_find_results_metadata_only_returns_zero_scores() -> None:
    from src.indexer import Document, build_inverted_index

    index = build_inverted_index([Document(document_id="doc-1", text="alpha beta")])

    results = build_find_results(index, ["doc-1"], [])

    assert len(results) == 1
    assert results[0].document_id == "doc-1"
    assert results[0].score == 0.0


# Integration-style test for render query for output preserves quoted text.
def test_render_query_for_output_preserves_quoted_text() -> None:
    assert render_query_for_output('"good friends"') == '"good friends"'


# Integration-style test for format relevance label covers ranked and unranked output.
def test_format_relevance_label_covers_ranked_and_unranked_output() -> None:
    assert format_relevance_label(0.0, has_term_ranking=False) == "score=N/A"
    assert format_relevance_label(1.23456, has_term_ranking=True) == "score=1.2346"


# Integration-style test for format snippet for display handles no targets and plain mode.
def test_format_snippet_for_display_handles_no_targets_and_plain_mode() -> None:
    metadata_only_query = parse_query("author:einstein")
    text_query = parse_query("love")

    assert format_snippet_for_display("Albert Einstein quote", metadata_only_query) == "Albert Einstein quote"
    assert (
        format_snippet_for_display("Love is beautiful", text_query, use_colour=False)
        == "Love is beautiful"
    )


# Integration-style test for main handles unknown argument for print.
def test_main_handles_unknown_argument_for_print(capsys) -> None:
    exit_code = main(["print", "love", "--bogus"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "unrecognized arguments: --bogus" in captured.err


# Integration-style test for main handles unknown argument for load.
def test_main_handles_unknown_argument_for_load(capsys) -> None:
    exit_code = main(["load", "--bogus"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "unrecognized arguments: --bogus" in captured.err


# Integration-style test for main handles project error from parser.
def test_main_handles_project_error_from_parser(monkeypatch, capsys) -> None:
    class BrokenParser:
        def parse_known_args(self, argv):
            raise ProjectError("broken parser")

    monkeypatch.setattr("src.main.build_parser", lambda: BrokenParser())

    exit_code = main(["load"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error: broken parser" in captured.err
