"""Benchmarking helpers for crawl, indexing, search, ranking, and suggestion latency."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from time import perf_counter

from src.config import DEFAULT_DELAY_SECONDS, DEFAULT_INDEX_PATH, DEFAULT_START_URL
from src.crawler import Crawler
from src.indexer import Document, build_index_from_pages, build_inverted_index
from src.models import InvertedIndex
from src.query_parser import parse_query
from src.ranking import rank_documents
from src.search import execute_query
from src.storage import load_index
from src.suggest import suggest_query


@dataclass(frozen=True)
class BenchmarkMetric:
    """A single benchmark measurement."""

    name: str
    value: float | None
    unit: str
    notes: str


def build_parser() -> argparse.ArgumentParser:
    """Create the benchmark command-line parser."""
    parser = argparse.ArgumentParser(prog="python -m src.benchmark")
    parser.add_argument(
        "--index-path",
        default=str(DEFAULT_INDEX_PATH),
        help="Path to an existing saved index.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=250,
        help="Iterations for latency-focused microbenchmarks.",
    )
    parser.add_argument(
        "--crawl-pages",
        type=int,
        default=10,
        help="Maximum number of pages to crawl for the crawl benchmark.",
    )
    parser.add_argument(
        "--crawl-delay",
        type=float,
        default=DEFAULT_DELAY_SECONDS,
        help="Delay used during the live crawl benchmark.",
    )
    parser.add_argument(
        "--skip-crawl",
        action="store_true",
        help="Skip the live crawl benchmark and reuse the saved index only.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the benchmark suite and print a compact report."""
    args = build_parser().parse_args(argv)
    index_path = Path(args.index_path)
    index = load_index(index_path)
    documents = reconstruct_documents(index)

    metrics: list[BenchmarkMetric] = []
    pages = None

    if args.skip_crawl:
        metrics.append(
            BenchmarkMetric(
                name="crawl_time",
                value=None,
                unit="s",
                notes="skipped by command-line flag",
            )
        )
    else:
        pages, crawl_metric = benchmark_crawl(
            max_pages=args.crawl_pages,
            delay_seconds=args.crawl_delay,
        )
        metrics.append(crawl_metric)

    metrics.append(benchmark_build_from_documents(documents))
    metrics.append(benchmark_index_size(index_path))
    metrics.append(
        benchmark_query_latency(index, raw_query="love", iterations=args.iterations)
    )
    metrics.append(
        benchmark_tfidf_latency(index, raw_query="love", iterations=args.iterations)
    )
    metrics.append(
        benchmark_suggestion_latency(index, raw_query="frends", iterations=args.iterations)
    )

    if pages is not None:
        metrics.append(
            benchmark_build_from_pages_metric(pages)
        )

    print("Benchmark Summary")
    print(f"Index path: {index_path}")
    print(f"Documents: {index.document_count}")
    print(f"Terms: {index.term_count}")
    print(f"Iterations: {args.iterations}")
    print("")
    print("| Metric | Value | Notes |")
    print("| --- | --- | --- |")
    for metric in metrics:
        print(
            f"| {metric.name} | {format_metric_value(metric)} | {metric.notes} |"
        )

    return 0


def benchmark_crawl(*, max_pages: int, delay_seconds: float) -> tuple[list, BenchmarkMetric]:
    """Measure live crawl time for the configured number of pages."""
    crawler = Crawler(
        start_url=DEFAULT_START_URL,
        delay_seconds=delay_seconds,
    )
    started = perf_counter()
    pages = crawler.crawl(max_pages=max_pages)
    elapsed = perf_counter() - started

    notes = f"{len(pages)} pages crawled with delay={delay_seconds:.1f}s"
    if not pages:
        notes = "crawl completed but returned no pages"
    return pages, BenchmarkMetric("crawl_time", elapsed, "s", notes)


def benchmark_build_from_pages_metric(pages: list) -> BenchmarkMetric:
    """Measure index build time directly from crawled pages."""
    elapsed = measure_operation(lambda: build_index_from_pages(pages), iterations=25)
    return BenchmarkMetric(
        "build_index_from_pages",
        elapsed,
        "ms",
        f"{len(pages)} crawled pages reused in-memory",
    )


def benchmark_build_from_documents(documents: list[Document]) -> BenchmarkMetric:
    """Measure index build time from reconstructed document payloads."""
    elapsed = measure_operation(
        lambda: build_inverted_index(documents),
        iterations=25,
    )
    total_tokens = sum(len(document.text.split()) for document in documents)
    return BenchmarkMetric(
        "build_index_time",
        elapsed,
        "ms",
        f"{len(documents)} documents reconstructed from metadata (~{total_tokens} whitespace tokens)",
    )


def benchmark_index_size(index_path: Path) -> BenchmarkMetric:
    """Measure the size of the persisted JSON index."""
    size_bytes = index_path.stat().st_size
    return BenchmarkMetric(
        "index_size",
        float(size_bytes),
        "bytes",
        format_bytes(size_bytes),
    )


def benchmark_query_latency(
    index: InvertedIndex,
    *,
    raw_query: str,
    iterations: int,
) -> BenchmarkMetric:
    """Measure parse + execute + rank latency for a normal text query."""
    elapsed = measure_operation(
        lambda: run_ranked_query(index, raw_query),
        iterations=iterations,
    )
    return BenchmarkMetric(
        "query_latency",
        elapsed,
        "ms",
        f'end-to-end search path for query "{raw_query}"',
    )


def benchmark_tfidf_latency(
    index: InvertedIndex,
    *,
    raw_query: str,
    iterations: int,
) -> BenchmarkMetric:
    """Measure TF-IDF ranking latency for an already matched candidate set."""
    parsed_query = parse_query(raw_query)
    matches = execute_query(index, parsed_query)
    elapsed = measure_operation(
        lambda: rank_documents(index, matches, parsed_query.scoring_terms()),
        iterations=iterations,
    )
    return BenchmarkMetric(
        "tfidf_latency",
        elapsed,
        "ms",
        f'{len(matches)} candidate documents for query "{raw_query}"',
    )


def benchmark_suggestion_latency(
    index: InvertedIndex,
    *,
    raw_query: str,
    iterations: int,
) -> BenchmarkMetric:
    """Measure latency for the misspelling suggestion path."""
    parsed_query = parse_query(raw_query)
    elapsed = measure_operation(
        lambda: suggest_query(index, parsed_query),
        iterations=iterations,
    )
    return BenchmarkMetric(
        "suggestion_latency",
        elapsed,
        "ms",
        f'misspelling suggestion path for query "{raw_query}"',
    )


def run_ranked_query(index: InvertedIndex, raw_query: str) -> None:
    """Execute the internal find pipeline without terminal output."""
    parsed_query = parse_query(raw_query)
    matches = execute_query(index, parsed_query)
    rank_documents(index, matches, parsed_query.scoring_terms())


def measure_operation(operation: Callable[[], object], *, iterations: int) -> float:
    """Return the mean runtime in milliseconds for an operation."""
    samples: list[float] = []
    for _ in range(iterations):
        started = perf_counter()
        operation()
        samples.append((perf_counter() - started) * 1000.0)
    return mean(samples)


def reconstruct_documents(index: InvertedIndex) -> list[Document]:
    """Reconstruct indexable document text from saved metadata."""
    documents: list[Document] = []
    for document_id, metadata in index.documents.items():
        sanitized_metadata = {
            key: value
            for key, value in metadata.items()
            if key not in {"document_id", "token_count"}
        }
        text = reconstruct_document_text(metadata)
        documents.append(
            Document(
                document_id=document_id,
                text=text,
                metadata=sanitized_metadata,
            )
        )
    return documents


def reconstruct_document_text(metadata: dict[str, object]) -> str:
    """Rebuild searchable text from persisted quote metadata."""
    raw_quotes = metadata.get("quotes")
    if isinstance(raw_quotes, list):
        lines: list[str] = []
        for payload in raw_quotes:
            if not isinstance(payload, dict):
                continue
            text = str(payload.get("text", ""))
            author = str(payload.get("author", ""))
            raw_tags = payload.get("tags", [])
            tags = [str(tag) for tag in raw_tags] if isinstance(raw_tags, list) else []
            line = " ".join([text, author, *tags]).strip()
            if line:
                lines.append(line)
        if lines:
            return "\n".join(lines)

    fallback_parts: list[str] = []
    for key in ("authors", "tags"):
        raw_values = metadata.get(key, [])
        if isinstance(raw_values, list):
            fallback_parts.extend(str(value) for value in raw_values)
    return " ".join(fallback_parts)


def format_metric_value(metric: BenchmarkMetric) -> str:
    """Return a formatted metric value with units."""
    if metric.value is None:
        return "n/a"

    if metric.unit == "bytes":
        return f"{int(metric.value)} bytes"
    if metric.unit == "s":
        return f"{metric.value:.3f} s"
    return f"{metric.value:.3f} {metric.unit}"


def format_bytes(size_bytes: int) -> str:
    """Return a readable size string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KiB"
    return f"{size_bytes / (1024 * 1024):.2f} MiB"


if __name__ == "__main__":
    raise SystemExit(main())
