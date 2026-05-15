"""Command-line entry point for the WebServices2 project."""

from __future__ import annotations

import argparse
import sys
from typing import NoReturn

from src.config import DEFAULT_DELAY_SECONDS, DEFAULT_INDEX_PATH, DEFAULT_START_URL
from src.crawler import Crawler
from src.exceptions import CliUsageError, IndexStorageError, ProjectError
from src.indexer import build_index_from_pages
from src.ranking import rank_documents
from src.search import find_matching_documents, get_term_info, normalize_query_terms
from src.storage import load_index, save_index


class CliArgumentParser(argparse.ArgumentParser):
    """Argument parser that reports errors without exiting the process."""

    def error(self, message: str) -> NoReturn:
        """Raise a CLI usage error instead of exiting the interpreter."""
        raise CliUsageError(message)


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = CliArgumentParser(prog="python -m src.main")
    subparsers = parser.add_subparsers(dest="command")

    crawl_parser = subparsers.add_parser(
        "crawl",
        help="Run the quotes crawler against a target site.",
    )
    crawl_parser.add_argument(
        "--start-url",
        default=DEFAULT_START_URL,
        help="Starting URL for the crawl.",
    )
    crawl_parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY_SECONDS,
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
        default=DEFAULT_START_URL,
        help="Starting URL for the crawl.",
    )
    build_parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY_SECONDS,
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

    print_parser = subparsers.add_parser(
        "print",
        help="Print postings for a single indexed word.",
    )
    print_parser.add_argument(
        "word",
        nargs="?",
        help="Word to inspect in the inverted index.",
    )
    print_parser.add_argument(
        "--path",
        default=str(DEFAULT_INDEX_PATH),
        help="Path to the JSON index file to load.",
    )

    find_parser = subparsers.add_parser(
        "find",
        help="Find documents containing all terms in a query.",
    )
    find_parser.add_argument(
        "query",
        nargs="*",
        help="One or more query terms.",
    )
    find_parser.add_argument(
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


def run_print_term(args: argparse.Namespace) -> int:
    """Print postings information for a single term."""
    if not args.word:
        print("Please provide a word to print.", file=sys.stderr)
        return 1

    try:
        index = load_index(args.path)
    except IndexStorageError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    normalized_terms = normalize_query_terms(args.word)
    if not normalized_terms:
        print("Please provide a non-empty word to print.", file=sys.stderr)
        return 1

    term = normalized_terms[0]
    term_info = get_term_info(index, term)
    if term_info is None:
        print(f'No postings found for "{term}".')
        return 0

    print(f'Term: "{term}"')
    print(f"Document frequency: {term_info.document_frequency}")
    print(f"Total frequency: {term_info.total_frequency}")
    for document_id in sorted(term_info.postings):
        posting = term_info.postings[document_id]
        print(
            f"- {document_id} | frequency={posting.frequency} | positions={posting.positions}"
        )
    return 0


def run_find(args: argparse.Namespace) -> int:
    """Find documents containing all terms from a query."""
    query = " ".join(args.query)
    normalized_terms = normalize_query_terms(query)
    if not normalized_terms:
        print("Please provide a non-empty query.", file=sys.stderr)
        return 1

    try:
        index = load_index(args.path)
    except IndexStorageError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    matches = find_matching_documents(index, query)
    if not matches:
        print(f'No results found for query: "{" ".join(normalized_terms)}".')
        return 0

    print(f'Results for query: "{" ".join(normalized_terms)}"')
    for result in rank_documents(index, matches, normalized_terms):
        metadata = index.documents.get(result.document_id, {})
        url = metadata.get("url", result.document_id)
        quote_count = metadata.get("quote_count", "unknown")
        print(f"- {url} | quotes={quote_count} | score={result.score}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the command-line entry point."""
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except CliUsageError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        parser.print_help(sys.stderr)
        return 1
    except ProjectError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.command == "crawl":
        return run_crawl(args)
    if args.command == "build":
        return run_build(args)
    if args.command == "load":
        return run_load(args)
    if args.command == "print":
        return run_print_term(args)
    if args.command == "find":
        return run_find(args)

    parser.print_help(sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
