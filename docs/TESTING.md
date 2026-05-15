# Testing

## Overview

The project uses automated tests to cover the crawler, indexer, storage, CLI commands, advanced query processing, suggestion logic, and benchmarking helpers.

The goal of the test suite is not just to execute lines, but to validate the main coursework behaviors:

- polite crawling logic
- safe parsing of malformed HTML
- correct indexing and positional statistics
- reliable JSON persistence
- usable CLI behavior
- ranked search correctness
- advanced query support
- suggestion fallback behavior

## Main Commands

Run the full suite:

```bash
pytest
```

Run coverage:

```bash
pytest --cov=src --cov-report=term-missing
```

Run linting:

```bash
ruff check src tests
```

Run static typing:

```bash
mypy src
```

## Current Coverage

Current measured result:

- `95 passed`
- `91%` total coverage

The benchmark module was a major coverage gap until dedicated tests were added in `tests/test_benchmark.py`.

## Test File Breakdown

### `tests/test_crawler.py`

Covers:

- next-page extraction
- quote extraction
- duplicate URL handling
- failed request handling
- politeness delay behavior
- malformed real-page fixture handling

### `tests/test_indexer.py`

Covers:

- case-insensitive tokenization
- punctuation normalization
- term frequencies
- token positions
- document frequency
- empty input handling

### `tests/test_storage.py`

Covers:

- saving JSON
- loading saved JSON
- structural equality after load
- missing file handling
- corrupt file handling
- invalid structure handling

### `tests/test_main.py`

Covers:

- build command behavior
- load command behavior
- empty command handling
- unknown command handling

### `tests/test_search.py`

Covers:

- `print` and `find`
- ranking order
- metadata snippet output
- phrase queries
- `OR`
- exclusion queries
- author and tag filters
- syntax error handling
- truncated snippet output
- suggestion display

### `tests/test_query_parser.py`

Covers:

- phrase parsing
- `OR` parsing
- exclusion parsing
- author/tag filters
- invalid syntax cases

### `tests/test_ranking.py`

Covers:

- TF-IDF behavior
- smoothed IDF
- ranking order
- missing-term safety

### `tests/test_suggest.py`

Covers:

- edit-distance typo correction
- exact-hit no-suggestion case
- unrelated-word rejection
- suggestion ranking order
- query-level suggestion rebuilding

### `tests/test_benchmark.py`

Covers:

- benchmark parser defaults
- benchmark report generation with `--skip-crawl`
- crawl benchmark helper with a fake crawler
- build/query/ranking/suggestion timing helpers
- reconstructed document helpers
- formatting helpers

## CI

The repository now includes GitHub Actions workflows that run automated checks on pushes and pull requests.

The dedicated testing workflow in `.github/workflows/tests.yml` runs:

- `ruff check src tests`
- `python -m src.benchmark --skip-crawl --iterations 1`
- `pytest --cov=src --cov-report=term-missing`

This makes test and lint status visible on PRs before merge.

## Testing Strategy Notes

### Mocking over live network

Unit tests use mocked responses or local fixtures rather than live web requests. That keeps the suite deterministic and fast.

### Realistic fixtures where needed

The crawler includes a fixture based on the actual `quotes.toscrape.com` page structure, including malformed HTML quirks. This gives stronger evidence than only using idealized sample markup.

### Coverage with judgment

Coverage is used as a quality indicator, but not as the only indicator. The more important point is that the tests assert real behavior around retrieval, indexing, parsing, and failure handling.
