"""Command-line entry point for the WebServices2 project."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from src.crawler import Crawler
from src.indexer import build_index_from_pages
from src.storage import IndexStorageError, load_index, save_index


DEFAULT_INDEX_PATH = Path("data/index.json")


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(prog="python -m src.main")
    subparsers = parser.add_subparsers(dest="command")

    crawl_parser = subparsers.add_parser(
        "crawl",
        help="Run the quotes crawler against a target site.",
    )
    crawl_parser.add_argument(
        "--start-url",
        default="https://quotes.toscrape.com/",
        help="Starting URL for the crawl.",
    )
    crawl_parser.add_argument(
        "--delay",
        type=float,
        default=6.0,
        help="Minimum delay in seconds between requests.",
    )
    crawl_parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Optional limit for the number of pages to crawl.",
    )

    build_parser = subparsers.add_parser(
        "build",
        help="Crawl pages, build an index, and save it to disk.",
    )
    build_parser.add_argument(
        "--start-url",
        default="https://quotes.toscrape.com/",
        help="Starting URL for the crawl.",
    )
    build_parser.add_argument(
        "--delay",
        type=float,
        default=6.0,
        help="Minimum delay in seconds between requests.",
    )
    build_parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Optional limit for the number of pages to crawl.",
    )
    build_parser.add_argument(
        "--output",
        default=str(DEFAULT_INDEX_PATH),
        help="Path to the JSON index output file.",
    )

    load_parser = subparsers.add_parser(
        "load",
        help="Load a saved index and print a summary.",
    )
    load_parser.add_argument(
        "--path",
        default=str(DEFAULT_INDEX_PATH),
        help="Path to the JSON index file to load.",
    )

    return parser


def run_crawl(args: argparse.Namespace) -> int:
    """Execute a crawl and print a concise summary."""
    crawler = Crawler(start_url=args.start_url, delay_seconds=args.delay)
    pages = crawler.crawl(max_pages=args.max_pages)
    total_quotes = sum(len(page.quotes) for page in pages)

    print(f"Pages crawled: {len(pages)}")
    print(f"Visited URLs: {len(crawler.visited_urls)}")
    print(f"Total quotes: {total_quotes}")

    if pages and pages[0].quotes:
        first_quote = pages[0].quotes[0]
        print(f"First page: {pages[0].url}")
        print(f'First quote: {first_quote.text} - {first_quote.author}')

    return 0


def run_build(args: argparse.Namespace) -> int:
    """Crawl pages, build an index, and save it."""
    crawler = Crawler(start_url=args.start_url, delay_seconds=args.delay)
    pages = crawler.crawl(max_pages=args.max_pages)
    index = build_index_from_pages(pages)
    save_index(index, args.output)

    total_quotes = sum(len(page.quotes) for page in pages)
    print(f"Saved index: {args.output}")
    print(f"Pages crawled: {len(pages)}")
    print(f"Documents indexed: {index.document_count}")
    print(f"Terms indexed: {index.term_count}")
    print(f"Total quotes: {total_quotes}")
    return 0


def run_load(args: argparse.Namespace) -> int:
    """Load an index file and print its summary."""
    try:
        index = load_index(args.path)
    except IndexStorageError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Loaded index: {args.path}")
    print(f"Documents indexed: {index.document_count}")
    print(f"Terms indexed: {index.term_count}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the command-line entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "crawl":
        return run_crawl(args)
    if args.command == "build":
        return run_build(args)
    if args.command == "load":
        return run_load(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
