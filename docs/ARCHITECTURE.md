# Architecture

## Overview

The project is a small command-line information retrieval pipeline built around a crawl -> index -> persist -> search workflow.

At a high level:

1. Crawl the live website.
2. Extract quotes, authors, tags, and pagination.
3. Convert crawled pages into page-documents.
4. Build a positional inverted index.
5. Save the index as JSON.
6. Load the saved index for search.
7. Parse queries, match candidate documents, rank results, and display snippets.

## Module Responsibilities

### `src/crawler.py`

Responsible for:

- fetching pages with `requests`
- enforcing the politeness delay
- parsing HTML with `BeautifulSoup`
- extracting quote text, authors, tags, and next-page links
- avoiding duplicate URLs

The crawler returns `PageContent` objects rather than building the index directly. That separation keeps the network layer independent from indexing logic.

### `src/indexer.py`

Responsible for:

- tokenization
- lowercase normalization
- positional indexing
- document frequency and total frequency aggregation
- conversion from `PageContent` to `Document`

Each crawled page becomes one indexable document. Searchable text is rebuilt from:

- quote text
- quote author
- quote tags

### `src/storage.py`

Responsible for:

- saving the index to JSON
- loading the JSON back into typed in-memory structures
- validating the saved structure through the model layer

This keeps persistence concerns separate from query execution.

### `src/models.py`

Responsible for:

- structured dataclasses for quotes, pages, documents, postings, term statistics, and ranked results
- validation of loaded metadata and index payloads

This file defines the main data contracts used across the project.

### `src/query_parser.py`

Responsible for:

- turning raw query text into a normalized internal representation
- detecting invalid syntax
- supporting:
  - phrase queries
  - `OR`
  - exclusion
  - `author:`
  - `tag:`

This keeps syntax concerns separate from search execution.

### `src/search.py`

Responsible for:

- executing parsed queries against the index
- AND, OR, phrase, exclusion, author, and tag matching
- quote snippet selection from metadata

This is the core retrieval layer.

### `src/ranking.py`

Responsible for:

- term frequency lookup
- inverse document frequency
- TF-IDF scoring
- document ranking

It only ranks candidate matches returned by `search.py`.

### `src/suggest.py`

Responsible for:

- Levenshtein distance
- vocabulary filtering for suggestion candidates
- ranking near-match suggestions

This module is only used when no exact text results are found.

### `src/main.py`

Responsible for:

- command-line parsing
- dispatching `crawl`, `build`, `load`, `print`, and `find`
- formatting user-facing output
- keeping CLI error handling consistent

### `src/benchmark.py`

Responsible for:

- measuring crawl time
- measuring index build time
- measuring stored index size
- measuring query, TF-IDF, and suggestion latency

It is an analysis tool rather than part of the user-facing search path.

## Data Flow

### Build Flow

```text
Crawler -> PageContent -> Document -> InvertedIndex -> JSON file
```

### Search Flow

```text
JSON file -> InvertedIndex -> ParsedQuery -> Candidate documents -> Ranked results -> CLI output
```

## Inverted Index Layout

The saved index has two major sections.

### `documents`

Stores document-level metadata:

- `document_id`
- `url`
- `quote_count`
- `token_count`
- `authors`
- `tags`
- `quotes`

### `terms`

Stores term-level retrieval data:

- `document_frequency`
- `total_frequency`
- `postings`
- posting `frequency`
- posting `positions`

This separation is deliberate:

- postings stay compact and retrieval-focused
- quote text is preserved once for snippet output
- ranking and search do not need to re-fetch live pages

## Design Choices

### Page-level documents

The current index is page-based rather than quote-based. This is simpler and fits the coursework stages well, though it makes result granularity coarser.

### Metadata-aware search output

The system stores full quote metadata so search output can show readable snippets without bloating postings.

### Typed, defensive loading

The storage/model layer validates saved index structure so invalid JSON or malformed payloads fail with clear errors instead of undefined behavior.

## Extension Points

The architecture is set up so future changes can stay local:

- quote-level documents would mainly affect `indexer.py`
- new ranking methods would mainly affect `ranking.py`
- richer boolean syntax would mainly affect `query_parser.py` and `search.py`
- faster suggestion structures would mainly affect `suggest.py`
