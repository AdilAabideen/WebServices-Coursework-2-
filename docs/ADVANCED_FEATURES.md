# Advanced Features

This project includes several retrieval and usability features beyond a basic keyword lookup. The `find` command combines structured query parsing, candidate retrieval, ranking, snippet selection, and output formatting into one search flow.

## TF-IDF Ranking

TF-IDF is used after candidate documents have already been matched by the search layer.

- `TF` measures how often a query term appears in one indexed page.
- `IDF` measures how rare that term is across the full collection.
- the final document score is the sum of `TF * IDF` across the query terms

In this application, each crawled quotes page is one indexed document. The ranker uses posting frequencies from the inverted index rather than rescanning raw text, which keeps ranking efficient.

The implementation uses smoothed IDF:

```text
idf = log((1 + total_documents) / (1 + document_frequency)) + 1
score = sum(term_frequency_in_document * idf)
```

Effect in practice:

- documents with more occurrences of a query term score higher
- rarer terms contribute more than very common terms
- only the candidate match set is ranked, not the whole corpus

## Levenshtein Suggestions

When a text query returns no exact results, the system can suggest a likely correction using Levenshtein edit distance.

Levenshtein distance counts the minimum number of single-character edits needed to turn one word into another:

- insertion
- deletion
- substitution

For example, `frends` is close to `friends` because it only needs one character inserted.

In this application, suggestions are conservative:

- only missing text terms are considered
- candidate vocabulary terms are filtered by length first
- only candidates inside a small edit-distance threshold are scored
- ties are broken by term frequency so common real terms are preferred

This keeps suggestions useful without making aggressive or noisy corrections.

## Snippet Highlighting

The `find` command prints matching quote snippets under each result. Positive query terms and phrases are highlighted in terminal output so the user can immediately see why a result matched.

The highlighting logic:

- truncates long quote text for readable CLI output
- prefers phrase highlights before single-term highlights
- highlights only positive content terms and phrases
- does not highlight metadata filters or excluded terms

This makes ranked results easier to inspect quickly from the terminal.

## Metadata Filtering

The query parser supports metadata-aware search through:

- `author:<name>`
- `tag:<value>`

These filters do not depend on TF-IDF. They are resolved through stored document metadata and then combined with the text-match clauses.

Examples:

```bash
python3 -m src.main find author:einstein
python3 -m src.main find tag:life
python3 -m src.main find love author:monroe
```

Metadata-only queries still return matching documents and snippets, but they are shown with `score=N/A` because there are no content terms to rank.

## Boolean And Exclusion Queries

The parser supports several advanced query forms:

- space-separated terms for AND behavior
- `OR` for union queries
- quoted phrases for exact adjacent-token matching
- `-term` for NOT-style exclusion

Examples:

```bash
python3 -m src.main find good friends
python3 -m src.main find good OR friends
python3 -m src.main find '"good friends"'
python3 -m src.main find good -friends
```

How they work in this application:

- AND queries intersect postings sets
- OR queries union postings sets
- phrase queries use stored token positions
- exclusions remove documents containing the unwanted term after positive matching

Together, these features make the search engine more than a simple inverted-index lookup. It supports ranked retrieval, controlled fuzzy suggestions, metadata-aware filtering, and readable highlighted output from the CLI.
