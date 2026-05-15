"""Tests for the benchmark module."""

from __future__ import annotations

from pathlib import Path

from src.benchmark import (
    BenchmarkMetric,
    benchmark_build_from_documents,
    benchmark_build_from_pages_metric,
    benchmark_crawl,
    benchmark_index_size,
    benchmark_query_latency,
    benchmark_suggestion_latency,
    benchmark_tfidf_latency,
    build_parser,
    format_bytes,
    format_metric_value,
    main,
    measure_operation,
    reconstruct_document_text,
    reconstruct_documents,
)
from src.indexer import Document, build_inverted_index
from src.models import PageContent, Quote
from src.storage import save_index


def build_sample_index():
    """Create a small index for benchmark tests."""
    return build_inverted_index(
        [
            Document(
                document_id="doc-1",
                text="Love friends life Alpha Author alpha beta",
                metadata={
                    "url": "https://quotes.toscrape.com/page/1/",
                    "quote_count": 1,
                    "quotes": [
                        {
                            "text": "Love friends life",
                            "author": "Alpha Author",
                            "tags": ["alpha", "beta"],
                        }
                    ],
                },
            ),
            Document(
                document_id="doc-2",
                text="Friendship kindness life Beta Writer support",
                metadata={
                    "url": "https://quotes.toscrape.com/page/2/",
                    "quote_count": 1,
                    "authors": ["Beta Writer"],
                    "tags": ["support"],
                },
            ),
        ]
    )


def test_build_parser_uses_politeness_default() -> None:
    args = build_parser().parse_args([])

    assert args.crawl_delay == 6.0
    assert args.iterations == 250


def test_main_skip_crawl_runs_against_saved_index(tmp_path: Path, capsys) -> None:
    index_path = tmp_path / "index.json"
    save_index(build_sample_index(), index_path)

    exit_code = main(["--skip-crawl", "--iterations", "1", "--index-path", str(index_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Benchmark Summary" in captured.out
    assert "| crawl_time | n/a | skipped by command-line flag |" in captured.out
    assert "query_latency" in captured.out
    assert "suggestion_latency" in captured.out


def test_benchmark_crawl_uses_fake_crawler(monkeypatch) -> None:
    pages = [
        PageContent(
            url="https://quotes.toscrape.com/",
            quotes=[Quote(text="Example", author="Author", tags=["tag"])],
            next_page=None,
        )
    ]

    class FakeCrawler:
        def __init__(self, start_url: str, delay_seconds: float) -> None:
            assert start_url == "https://quotes.toscrape.com/"
            assert delay_seconds == 6.0

        def crawl(self, *, max_pages: int | None = None):
            assert max_pages == 1
            return pages

    ticks = iter([10.0, 13.5])
    monkeypatch.setattr("src.benchmark.Crawler", FakeCrawler)
    monkeypatch.setattr("src.benchmark.perf_counter", lambda: next(ticks))

    crawled_pages, metric = benchmark_crawl(max_pages=1, delay_seconds=6.0)

    assert crawled_pages == pages
    assert metric.name == "crawl_time"
    assert metric.value == 3.5
    assert "1 pages crawled" in metric.notes


def test_benchmark_build_helpers_return_metrics() -> None:
    index = build_sample_index()
    documents = reconstruct_documents(index)
    pages = [
        PageContent(
            url="https://quotes.toscrape.com/",
            quotes=[Quote(text="Example", author="Author", tags=["tag"])],
            next_page=None,
        )
    ]

    document_metric = benchmark_build_from_documents(documents)
    page_metric = benchmark_build_from_pages_metric(pages)

    assert document_metric.name == "build_index_time"
    assert document_metric.unit == "ms"
    assert document_metric.value is not None and document_metric.value >= 0.0
    assert page_metric.name == "build_index_from_pages"
    assert page_metric.value is not None and page_metric.value >= 0.0


def test_benchmark_latency_helpers_return_metrics() -> None:
    index = build_sample_index()

    query_metric = benchmark_query_latency(index, raw_query="love", iterations=2)
    tfidf_metric = benchmark_tfidf_latency(index, raw_query="love", iterations=2)
    suggestion_metric = benchmark_suggestion_latency(index, raw_query="frends", iterations=2)

    assert query_metric.name == "query_latency"
    assert query_metric.value is not None and query_metric.value >= 0.0
    assert tfidf_metric.name == "tfidf_latency"
    assert tfidf_metric.value is not None and tfidf_metric.value >= 0.0
    assert suggestion_metric.name == "suggestion_latency"
    assert suggestion_metric.value is not None and suggestion_metric.value >= 0.0


def test_benchmark_index_size_uses_file_size(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    save_index(build_sample_index(), index_path)

    metric = benchmark_index_size(index_path)

    assert metric.name == "index_size"
    assert metric.unit == "bytes"
    assert metric.value == float(index_path.stat().st_size)


def test_reconstruct_document_text_prefers_quote_metadata() -> None:
    metadata = {
        "quotes": [
            {
                "text": "Love life",
                "author": "Author One",
                "tags": ["hope", "joy"],
            }
        ],
        "authors": ["Ignored Author"],
        "tags": ["ignored"],
    }

    text = reconstruct_document_text(metadata)

    assert text == "Love life Author One hope joy"


def test_reconstruct_document_text_falls_back_to_authors_and_tags() -> None:
    metadata = {"authors": ["Author One"], "tags": ["alpha", "beta"]}

    text = reconstruct_document_text(metadata)

    assert text == "Author One alpha beta"


def test_reconstruct_documents_removes_internal_fields() -> None:
    index = build_sample_index()

    documents = reconstruct_documents(index)

    assert len(documents) == 2
    assert "document_id" not in documents[0].metadata
    assert "token_count" not in documents[0].metadata


def test_format_helpers_cover_bytes_and_units() -> None:
    assert format_bytes(512) == "512 B"
    assert format_bytes(2048) == "2.00 KiB"
    assert format_metric_value(BenchmarkMetric("crawl", None, "s", "skipped")) == "n/a"
    assert format_metric_value(BenchmarkMetric("size", 2048.0, "bytes", "size")) == "2048 bytes"
    assert format_metric_value(BenchmarkMetric("query", 1.23456, "ms", "latency")) == "1.235 ms"
    assert format_metric_value(BenchmarkMetric("crawl", 2.5, "s", "live")) == "2.500 s"


def test_measure_operation_returns_non_negative_mean() -> None:
    elapsed = measure_operation(lambda: None, iterations=3)

    assert elapsed >= 0.0
