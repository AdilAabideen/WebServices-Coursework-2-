# COMP3011 Search Engine Tool

Python command-line search engine coursework for `https://quotes.toscrape.com/`.

## Overview

This project crawls the quotes website, builds a positional inverted index, stores the index as JSON, and provides ranked command-line search over the collected pages. The implementation includes phrase search, boolean-style query operators, metadata filters, and misspelling suggestions.

## Features

- polite crawler for all 10 quotes pages
- positional inverted index with frequencies and positions
- JSON index persistence in `data/index.json`
- smoothed TF-IDF ranking
- phrase search using positions
- `OR` and exclusion query support
- `author:` and `tag:` metadata filters
- misspelling suggestions using edit distance
- result snippets highlight matched query terms in the terminal
- benchmark runner and complexity analysis
- automated testing, coverage, and CI workflows

## Advanced Features

The project includes a few higher-level retrieval and usability features beyond basic keyword lookup:

- Levenshtein-based misspelling suggestions
- smoothed TF-IDF ranking over candidate matches
- snippet highlighting for matched terms and phrases
- metadata-aware filtering with `author:` and `tag:`
- boolean `OR`, phrase search, and `-term` exclusion

Details:

- [ADVANCED_FEATURES.md](/Users/adil/Documents/University/WebServices2/docs/ADVANCED_FEATURES.md)

## Quick Start

```bash
pip install -r requirements.txt
python3 -m src.main build
python3 -m src.main find love
python3 -m src.main find '"good friends"'
```

## Installation

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Optional quality tooling:

```bash
pip install ruff
```

## Usage

The project is driven through `python3 -m src.main`.

Typical flow:

1. Build the index from the live site.
2. Load the saved index to verify it.
3. Run `print` or `find` queries against the stored index.

## Commands

### `build`

Crawls the site, builds the inverted index, and saves it.

```bash
python3 -m src.main build
python3 -m src.main build --max-pages 1
python3 -m src.main build --output data/test-index.json
```

### `load`

Loads an existing saved index and prints a summary.

```bash
python3 -m src.main load
python3 -m src.main load --path data/test-index.json
```

### `print`

Shows postings information for a single normalized term.

```bash
python3 -m src.main print love
python3 -m src.main print indifference
```

### `find`

Runs ranked search against the saved index.

```bash
python3 -m src.main find love
python3 -m src.main find good friends
python3 -m src.main find '"good friends"'
python3 -m src.main find good OR friends
python3 -m src.main find good -friends
python3 -m src.main find author:einstein
python3 -m src.main find tag:life
```

### `benchmark`

Runs the benchmark suite.

```bash
python3 -m src.benchmark
python3 -m src.benchmark --skip-crawl
python3 -m src.benchmark --iterations 500
```

## Example Queries

Basic ranked term search:

```bash
python3 -m src.main find love
```

Expected style of output:

```text
Results for query: "love"
1. https://quotes.toscrape.com/page/2/ | quotes=10 | score=8.0000
   Match: "This life is what you make it..."
   Author: Marilyn Monroe
   Tags: friends, heartbreak, inspirational, life, love, sisters
```

Phrase search:

```bash
python3 -m src.main find '"good friends"'
```

Expected style of output:

```text
Results for query: "good friends"
1. https://quotes.toscrape.com/page/2/ | quotes=10 | score=22.7502
   Match: "Good friends, good books, and a sleepy conscience: this is the ideal life."
   Author: Mark Twain
   Tags: books, contentment, friends, friendship, life
```

Metadata filter:

```bash
python3 -m src.main find author:einstein
```

Expected style of output:

```text
Results for query: "author:einstein"
1. https://quotes.toscrape.com/page/5/ | quotes=10 | score=N/A
   Match: "Life is like riding a bicycle. To keep your balance, you must keep moving."
   Author: Albert Einstein
   Tags: life, simile
```

Suggestion example:

```bash
python3 -m src.main find frends
```

Expected style of output:

```text
No results found for query: "frends".
Did you mean: "friends"?
```

## Architecture

High-level architecture:

1. `crawler.py` fetches and parses the live site.
2. `indexer.py` turns page content into page-documents and builds the positional inverted index.
3. `storage.py` saves and loads the JSON index.
4. `query_parser.py` parses advanced query syntax.
5. `search.py` resolves document matches and snippets.
6. `ranking.py` applies smoothed TF-IDF.
7. `suggest.py` provides edit-distance suggestions.
8. `main.py` provides the CLI.
9. `benchmark.py` measures performance.

Detailed notes:

- [ARCHITECTURE.md](/Users/adil/Documents/University/WebServices2/docs/ARCHITECTURE.md)

## Inverted Index Design

The saved index separates term statistics from document metadata.

Term side:

- normalized term
- document frequency
- total frequency
- postings
- per-document frequency
- token positions

Document side:

- `document_id`
- `url`
- `quote_count`
- `token_count`
- `authors`
- `tags`
- `quotes` with text, author, and tags

This design keeps searchable postings compact while still preserving quote text for snippets.

## Ranking Algorithm

Ranking uses smoothed TF-IDF:

```text
idf = log((1 + total_documents) / (1 + document_frequency)) + 1
score = sum(term_frequency_in_document * idf)
```

That means:

- frequent terms inside a document raise the score
- rarer terms across the collection receive higher weight
- only candidate documents are scored

Additional details:

- [COMPLEXITY.md](/Users/adil/Documents/University/WebServices2/docs/COMPLEXITY.md)

## Query Processing

Supported query forms:

- single-term: `find love`
- multi-term AND: `find good friends`
- phrase: `find '"good friends"'`
- union: `find good OR friends`
- exclusion: `find good -friends`
- author filter: `find author:einstein`
- tag filter: `find tag:life`

The parser normalizes case, handles invalid syntax gracefully, and routes the query into the correct matching path.

Advanced query behavior, ranking, suggestions, and highlighting:

- [ADVANCED_FEATURES.md](/Users/adil/Documents/University/WebServices2/docs/ADVANCED_FEATURES.md)

## Query Suggestions

When a text query has no exact match, the project suggests likely vocabulary terms using Levenshtein distance with a conservative length filter.

Example:

```bash
python3 -m src.main find frends
```

Output:

```text
No results found for query: "frends".
Did you mean: "friends"?
```

## Testing

The project includes unit tests for:

- crawler parsing and politeness behavior
- index construction and storage
- CLI commands
- advanced query parsing and matching
- TF-IDF ranking
- suggestion ranking
- benchmark helper functions

Run:

```bash
pytest
ruff check src tests
mypy src
```

Detailed notes:

- [TESTING.md](/Users/adil/Documents/University/WebServices2/docs/TESTING.md)
- [VIDEO_GUIDE.md](/Users/adil/Documents/University/WebServices2/docs/VIDEO_GUIDE.md)

## Coverage

Current measured coverage:

- `pytest --cov=src --cov-report=term-missing`
- `97%` total coverage

This includes direct coverage for the benchmark module, which was previously the main uncovered area.

## Benchmarking

Benchmark command:

```bash
python3 -m src.benchmark
```

Offline benchmark option:

```bash
python3 -m src.benchmark --skip-crawl
```

Detailed notes:

- [BENCHMARKS.md](/Users/adil/Documents/University/WebServices2/docs/BENCHMARKS.md)

## Complexity Analysis

The project documents time-complexity tradeoffs for indexing, search, phrase matching, ranking, and suggestions.

Detailed notes:

- [COMPLEXITY.md](/Users/adil/Documents/University/WebServices2/docs/COMPLEXITY.md)

## GenAI Declaration

Generative AI tools were used during development for implementation assistance, debugging support, test scaffolding, and documentation drafting. All produced code and text were reviewed, adapted, and validated within the repository through manual inspection, tests, and benchmark checks.

Detailed reflection:

- [GENAI_EVALUATION.md](/Users/adil/Documents/University/WebServices2/docs/GENAI_EVALUATION.md)

## Limitations

- the corpus is small and fixed to `quotes.toscrape.com`
- documents are page-level rather than quote-level
- query suggestions are brute-force over the vocabulary
- metadata filters are unranked and intentionally show `score=N/A`
- crawl benchmarking depends on network conditions

## Future Work

1. Index individual quotes as documents rather than whole pages.
2. Add parenthesized boolean precedence and richer query composition.
3. Optimise suggestions with a BK-tree or similar approximate-match structure.
4. Add field-aware ranking or field-aware snippet explanations.
5. Add exportable benchmark reports or plots.

## References

- Quotes to Scrape: `https://quotes.toscrape.com/`
- Requests: `https://requests.readthedocs.io/`
- Beautiful Soup: `https://www.crummy.com/software/BeautifulSoup/bs4/doc/`
- Pytest: `https://docs.pytest.org/`
- Ruff: `https://docs.astral.sh/ruff/`
- GitHub Actions: `https://docs.github.com/actions`
