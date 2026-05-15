"""Command-line entry point for the WebServices2 project."""

from __future__ import annotations

import argparse

from src.crawler import Crawler


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


def main(argv: list[str] | None = None) -> int:
    """Run the command-line entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "crawl":
        return run_crawl(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
