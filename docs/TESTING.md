# Testing

## Overview

This project uses a layered testing strategy rather than one single style of test.
That is important because the coursework is not only about whether the commands
work once on happy-path input. It also needs evidence that the crawler, indexer,
storage layer, query parser, ranking logic, suggestion system, and CLI all behave
correctly across normal inputs, edge cases, malformed inputs, and previously fixed
bugs.

The current strategy combines:

- unit tests for isolated algorithms and helpers
- integration-style tests for command and module interaction
- mocked network tests for crawler reliability
- regression tests for previously fixed edge cases
- benchmark smoke tests for tooling and measurement helpers
- automated verification in GitHub Actions

## Main Commands

Run the full automated suite:

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

Run the benchmark smoke check without live crawling:

```bash
python3 -m src.benchmark --skip-crawl --iterations 1
```

## Current Quality Status

Current measured result:

- `123 passed`
- `97%` total coverage

This is a high coverage figure, but the more important point is that the suite is
structured around behavior and failure modes rather than only touching lines for
coverage numbers.

## Test Strategy Split

## 1. Unit Tests

Unit tests target small pieces of logic in isolation without needing the whole CLI
pipeline to run.

These are mainly:

- [tests/test_indexer.py](/Users/adil/Documents/University/WebServices2/tests/test_indexer.py:1)
- [tests/test_ranking.py](/Users/adil/Documents/University/WebServices2/tests/test_ranking.py:1)
- [tests/test_query_parser.py](/Users/adil/Documents/University/WebServices2/tests/test_query_parser.py:1)
- [tests/test_suggest.py](/Users/adil/Documents/University/WebServices2/tests/test_suggest.py:1)
- [tests/test_benchmark.py](/Users/adil/Documents/University/WebServices2/tests/test_benchmark.py:1)

### What the unit tests cover

**Indexer**

[tests/test_indexer.py](/Users/adil/Documents/University/WebServices2/tests/test_indexer.py:1) checks:

- case-insensitive tokenisation
- punctuation handling
- correct term frequency
- correct token positions
- correct document frequency
- empty text handling
- quote metadata preservation in indexed documents

**Ranking**

[tests/test_ranking.py](/Users/adil/Documents/University/WebServices2/tests/test_ranking.py:1) checks:

- term frequency behavior
- smoothed IDF behavior
- ranking order
- rare-term weighting
- missing-term safety
- scoring behavior for multi-term queries

**Query parser**

[tests/test_query_parser.py](/Users/adil/Documents/University/WebServices2/tests/test_query_parser.py:1) checks:

- phrase parsing
- `OR` parsing
- exclusion parsing
- author filter parsing
- tag filter parsing
- malformed syntax handling

**Suggestions**

[tests/test_suggest.py](/Users/adil/Documents/University/WebServices2/tests/test_suggest.py:1) checks:

- Levenshtein distance behavior
- suggestion ranking by edit distance and frequency
- exact-hit no-suggestion path
- unrelated-word rejection
- phrase and `OR` preservation when rebuilding suggestion text
- filter-preserving suggestion behavior

**Benchmark helpers**

[tests/test_benchmark.py](/Users/adil/Documents/University/WebServices2/tests/test_benchmark.py:1) checks:

- parser defaults
- metric formatting
- document reconstruction helpers
- query / TF-IDF / suggestion latency helpers
- index size measurement
- fake-crawler benchmark behavior

These unit tests are the core evidence for algorithmic correctness.

## 2. Integration-Style Tests

Integration-style tests validate that multiple modules work together correctly in
realistic workflows.

These are mainly:

- [tests/test_main.py](/Users/adil/Documents/University/WebServices2/tests/test_main.py:1)
- [tests/test_search.py](/Users/adil/Documents/University/WebServices2/tests/test_search.py:1)
- [tests/test_storage.py](/Users/adil/Documents/University/WebServices2/tests/test_storage.py:1)
- [tests/test_smoke.py](/Users/adil/Documents/University/WebServices2/tests/test_smoke.py:1)

### What the integration-style tests cover

**CLI command integration**

[tests/test_main.py](/Users/adil/Documents/University/WebServices2/tests/test_main.py:1) checks:

- `build` command behavior
- `load` command behavior
- `crawl` command output
- empty command handling
- unknown command handling
- unknown-argument handling
- output formatting helper branches
- CLI-level project error handling

This file is effectively the CLI integration layer.

**Search workflow integration**

[tests/test_search.py](/Users/adil/Documents/University/WebServices2/tests/test_search.py:1) checks the full `find` / `print` path across:

- parser behavior
- query execution
- ranking
- snippet selection
- snippet truncation
- snippet highlighting
- output formatting
- suggestion display

It also covers:

- single-term search
- multi-word search
- exact phrase search
- `OR`
- exclusion queries
- author and tag filters
- metadata-only result formatting

This is one of the most important integration files in the repository because it
tests the user-visible search behavior end to end inside the application.

**Storage round-trip integration**

[tests/test_storage.py](/Users/adil/Documents/University/WebServices2/tests/test_storage.py:1) checks:

- save JSON
- load saved JSON
- loaded index equals saved index
- missing file handling
- corrupt JSON handling
- invalid structure handling
- quote metadata preservation through save/load

This validates persistence as a real round-trip rather than only isolated
serialization helpers.

**Smoke tests**

[tests/test_smoke.py](/Users/adil/Documents/University/WebServices2/tests/test_smoke.py:1) checks:

- importability
- basic module execution sanity

Smoke tests are intentionally lightweight, but they catch packaging and entry-point
breakage early.

## 3. Crawler Tests

Crawler testing deserves its own category because it mixes HTML parsing, duplicate
handling, politeness logic, and simulated network failures.

This is mainly:

- [tests/test_crawler.py](/Users/adil/Documents/University/WebServices2/tests/test_crawler.py:1)

### What crawler tests cover

- next-page extraction
- quote text extraction
- author extraction
- tag extraction
- malformed HTML handling
- duplicate URL avoidance
- crawl stopping with `max_pages`
- failed request handling
- timeout handling
- politeness-delay behavior
- constructor validation
- URL normalization validation

The crawler tests are important because they show that the crawl loop is not just
functionally correct, but also defensive and polite.

## 4. Mocked Network and Mocked Crawler Tests

Some tests intentionally simulate network or crawler behavior instead of using the
real website. This keeps the test suite deterministic, fast, and suitable for CI.

### Mocked network tests

In [tests/test_crawler.py](/Users/adil/Documents/University/WebServices2/tests/test_crawler.py:1):

- mocked `requests` session objects are used
- connection errors are simulated
- timeout errors are simulated
- politeness timing is tested without real sleeping
- fixed HTML fixtures are used for parser behavior

This means crawler reliability can be tested without depending on live network
conditions.

### Mocked crawler tests

In [tests/test_main.py](/Users/adil/Documents/University/WebServices2/tests/test_main.py:1):

- fake crawler classes are injected into `src.main`
- `build` and `crawl` command behavior is tested without real HTTP requests
- CLI orchestration can be verified independently from crawler internals

This is useful because it separates:

- whether the crawler works
- whether the CLI uses the crawler correctly

## 5. Query Parser and Advanced Query Tests

Advanced query processing is tested separately from ranking and storage so it is
easy to reason about.

Relevant files:

- [tests/test_query_parser.py](/Users/adil/Documents/University/WebServices2/tests/test_query_parser.py:1)
- [tests/test_search.py](/Users/adil/Documents/University/WebServices2/tests/test_search.py:1)

### What is covered

- exact phrase parsing
- phrase execution using positional postings
- rejection of non-adjacent phrase matches
- `OR` query unions
- exclusion logic
- author filters
- tag filters
- malformed syntax handling
- metadata-only result formatting
- highlighted snippet formatting for positive terms only

This split is intentional:

- `test_query_parser.py` proves the query is interpreted correctly
- `test_search.py` proves the parsed query is executed correctly

## 6. Regression Tests

A large part of the suite also acts as regression protection. These are tests added
after a feature or edge case was implemented so the same bug cannot silently return
later.

Examples include:

- malformed quote HTML parsing
- corrupted index-file handling
- metadata-only search results showing `score=N/A`
- snippet truncation behavior
- snippet highlighting behavior
- query suggestion output
- invalid advanced query syntax
- CLI unknown-argument rejection

Regression tests are valuable because they lock in fixes from earlier tickets.

## 7. Performance and Tooling Tests

The project also includes testing around measurement and tooling, not only core
search correctness.

This is mainly in:

- [tests/test_benchmark.py](/Users/adil/Documents/University/WebServices2/tests/test_benchmark.py:1)

These tests do not benchmark the system for marks by themselves, but they verify
that the benchmark tooling works correctly and safely in automation.

## Test Suite By File

This section is useful when explaining the project in a video or viva.

### [tests/test_crawler.py](/Users/adil/Documents/University/WebServices2/tests/test_crawler.py:1)

Focus:

- crawler behavior
- parser robustness
- mocked network failures
- politeness timing

### [tests/test_indexer.py](/Users/adil/Documents/University/WebServices2/tests/test_indexer.py:1)

Focus:

- tokenisation
- positions
- frequencies
- document statistics
- empty input behavior

### [tests/test_storage.py](/Users/adil/Documents/University/WebServices2/tests/test_storage.py:1)

Focus:

- save/load round-trip
- invalid file handling
- metadata preservation

### [tests/test_main.py](/Users/adil/Documents/University/WebServices2/tests/test_main.py:1)

Focus:

- CLI command behavior
- parser-level errors
- build/load/crawl orchestration
- formatting helpers

### [tests/test_search.py](/Users/adil/Documents/University/WebServices2/tests/test_search.py:1)

Focus:

- `print`
- `find`
- ranking
- snippets
- highlighting
- advanced query execution
- suggestions

### [tests/test_query_parser.py](/Users/adil/Documents/University/WebServices2/tests/test_query_parser.py:1)

Focus:

- advanced query syntax parsing
- parser error behavior

### [tests/test_ranking.py](/Users/adil/Documents/University/WebServices2/tests/test_ranking.py:1)

Focus:

- TF-IDF math
- ranking order
- IDF weighting

### [tests/test_suggest.py](/Users/adil/Documents/University/WebServices2/tests/test_suggest.py:1)

Focus:

- edit distance
- candidate ranking
- query suggestion rebuilding

### [tests/test_benchmark.py](/Users/adil/Documents/University/WebServices2/tests/test_benchmark.py:1)

Focus:

- benchmark runner helper logic
- metric formatting
- latency measurement helpers

### [tests/test_smoke.py](/Users/adil/Documents/University/WebServices2/tests/test_smoke.py:1)

Focus:

- import sanity
- entry-point sanity

## Why Mocking Is Used

Mocking is used in crawler and CLI tests for three main reasons:

- determinism: tests should not fail because a website is down or slow
- speed: CI should not wait for live crawling or politeness delays
- isolation: the project should test its own logic, not internet reliability

This is especially important for:

- network failures
- timeout behavior
- politeness timing
- CLI integration around crawl/build commands

## Coverage Interpretation

Coverage is useful, but it does not mean correctness by itself.

What `97%` means:

- most executable lines in `src/` are run by tests
- the remaining gaps are small defensive or low-priority branches
- the suite gives strong confidence in the main coursework functionality

What `97%` does not mean:

- it does not guarantee the program is `97% correct`
- it does not replace good assertions or good test design

The important point is that high coverage here comes with meaningful behavioral
checks, not just line-touching.

## Continuous Integration

Automated checks run in GitHub Actions through:

- [.github/workflows/tests.yml](/Users/adil/Documents/University/WebServices2/.github/workflows/tests.yml:1)

The CI pipeline runs:

- `ruff check src tests`
- `python3 -m src.benchmark --skip-crawl --iterations 1`
- `pytest --cov=src --cov-report=term-missing`

This gives visible automated quality checks on pushes and pull requests.

## Suggested Summary For The Video

A concise and accurate way to describe the test strategy is:

> The project uses a layered testing approach combining unit tests for core
> algorithms, integration-style tests for CLI workflows, mocked crawler and
> network tests for reliability, regression tests for previously fixed edge
> cases, and automated CI checks with linting, coverage, and benchmark smoke
> verification.

## Related Documentation

- [README.md](/Users/adil/Documents/University/WebServices2/README.md:1)
- [ARCHITECTURE.md](/Users/adil/Documents/University/WebServices2/docs/ARCHITECTURE.md:1)
- [BENCHMARKS.md](/Users/adil/Documents/University/WebServices2/docs/BENCHMARKS.md:1)
- [COMPLEXITY.md](/Users/adil/Documents/University/WebServices2/docs/COMPLEXITY.md:1)
- [GENAI_EVALUATION.md](/Users/adil/Documents/University/WebServices2/docs/GENAI_EVALUATION.md:1)
