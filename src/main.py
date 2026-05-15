"""Command-line entry point for the WebServices2 project."""

from __future__ import annotations

import argparse
import sys
from typing import NoReturn

from src.config import (
    DEFAULT_DELAY_SECONDS,
    DEFAULT_INDEX_PATH,
    DEFAULT_START_URL,
    MAX_SNIPPET_LENGTH,
)
from src.crawler import Crawler
from src.exceptions import CliUsageError, IndexStorageError, ProjectError, QuerySyntaxError
from src.indexer import build_index_from_pages
from src.models import InvertedIndex, RankedDocument
from src.query_parser import parse_query
from src.ranking import rank_documents
from src.search import (
    execute_query,
    find_matching_quotes,
    get_term_info,
    normalize_query_terms,
)
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
    query = reconstruct_query(args.query)
    try:
        parsed_query = parse_query(query)
    except QuerySyntaxError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    try:
        index = load_index(args.path)
    except IndexStorageError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    matches = execute_query(index, parsed_query)
    rendered_query = render_query_for_output(parsed_query.display_text())
    if not matches:
        print(f"No results found for query: {rendered_query}.")
        return 0

    ranking_terms = parsed_query.scoring_terms()
    ranked_results = build_find_results(index, matches, ranking_terms)
    print(f"Results for query: {rendered_query}")
    for rank, result in enumerate(ranked_results, start=1):
        metadata = index.documents.get(result.document_id, {})
        url = metadata.get("url", result.document_id)
        quote_count = metadata.get("quote_count", "unknown")
        relevance = format_relevance_label(result.score, has_term_ranking=bool(ranking_terms))
        print(f"{rank}. {url} | quotes={quote_count} | {relevance}")

        snippets = find_matching_quotes(metadata, parsed_query)
        for snippet in snippets:
            print(f'   Match: "{truncate_snippet(snippet.text)}"')
            print(f"   Author: {snippet.author}")
            print(f"   Tags: {', '.join(snippet.tags)}")
    return 0


def reconstruct_query(parts: list[str]) -> str:
    """Rebuild a raw query string while preserving shell-quoted phrases."""
    reconstructed: list[str] = []
    for part in parts:
        if (
            any(character.isspace() for character in part)
            and not part.startswith(("author:", "tag:", "-"))
            and not (part.startswith('"') and part.endswith('"'))
        ):
            reconstructed.append(f'"{part}"')
        else:
            reconstructed.append(part)
    return " ".join(reconstructed)


def render_query_for_output(query_text: str) -> str:
    """Format a normalized query string for user-facing CLI output."""
    if query_text.startswith('"') and query_text.endswith('"'):
        return query_text
    return f'"{query_text}"'


def build_find_results(
    index: InvertedIndex,
    matches: list[str],
    ranking_terms: list[str],
) -> list[RankedDocument]:
    """Return ranked find results, or stable unranked results for metadata-only queries."""
    if not ranking_terms:
        return [RankedDocument(document_id=document_id, score=0.0) for document_id in matches]
    return rank_documents(index, matches, ranking_terms)


def format_relevance_label(score: float, *, has_term_ranking: bool) -> str:
    """Format the result relevance label for text and metadata-only queries."""
    if not has_term_ranking:
        return "score=N/A"
    return f"score={score:.4f}"


def truncate_snippet(text: str, *, max_length: int = MAX_SNIPPET_LENGTH) -> str:
    """Truncate a quote snippet for terminal display without altering stored metadata."""
    if len(text) <= max_length:
        return text

    trimmed = text[: max_length - 3].rstrip()
    if " " in trimmed:
        trimmed = trimmed.rsplit(" ", 1)[0]
    return f"{trimmed}..."


def main(argv: list[str] | None = None) -> int:
    """Run the command-line entry point."""
    parser = build_parser()
    raw_args = list(sys.argv[1:] if argv is None else argv)
    try:
        args, unknown = parser.parse_known_args(argv)
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
        if unknown:
            print(f"Error: unrecognized arguments: {' '.join(unknown)}", file=sys.stderr)
            parser.print_help(sys.stderr)
            return 1
        return run_print_term(args)
    if args.command == "find":
        args.query = extract_find_query_args(raw_args[1:]) if raw_args else args.query
        return run_find(args)
    if unknown:
        print(f"Error: unrecognized arguments: {' '.join(unknown)}", file=sys.stderr)
        parser.print_help(sys.stderr)
        return 1

    parser.print_help(sys.stderr)
    return 1


def extract_find_query_args(raw_args: list[str]) -> list[str]:
    """Extract raw find-query tokens while preserving exclusion terms."""
    query_parts: list[str] = []
    skip_next = False
    for index, token in enumerate(raw_args):
        if skip_next:
            skip_next = False
            continue
        if token == "--path":
            if index + 1 < len(raw_args):
                skip_next = True
            continue
        query_parts.append(token)
    return query_parts


if __name__ == "__main__":
    raise SystemExit(main())
