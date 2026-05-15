# Complexity Analysis

## Data Structures

The search engine relies on a small set of core structures:

- `documents`: Python dictionary keyed by document ID
- `terms`: Python dictionary keyed by normalized term
- `postings`: per-term dictionary keyed by document ID
- `positions`: per-posting list of token offsets
- `quotes` metadata: stored once per document for snippet rendering

Because the implementation is dictionary-heavy, most direct term and document lookups are constant-time on average.

## Complexity Table

| Operation | Complexity | Explanation |
| --- | --- | --- |
| Build index | `O(T)` | Each token is visited once to build frequencies and positions. |
| Save index | `O(T + M)` | Serializes term postings plus document metadata. |
| Load index | `O(T + M)` | Rebuilds dictionaries and posting objects from JSON. |
| Single-term lookup | `O(1 + d)` | Dictionary lookup plus iterating the term's postings if printed or ranked. |
| Multi-term AND | `O(d1 + d2 + ...)` | Each query term contributes a postings set that is intersected. |
| OR query | `O(d1 + d2 + ...)` | Each postings set is unioned into the candidate result set. |
| Phrase search | `O(p1 + p2 + ...)` | Compares positional lists for shared documents to find adjacent token offsets. |
| Author/tag filter | `O(D × F)` | Scans document metadata and tokenizes candidate author/tag values. |
| TF-IDF ranking | `O(C × q)` | Scores only the `C` candidate documents across `q` query terms. |
| Snippet selection | `O(Q × L)` | Checks stored quote metadata for matching terms or phrases. |
| Query suggestion | `O(V × L^2)` | Compares a misspelled term against vocabulary terms using Levenshtein distance. |

## Symbols

- `T`: total number of indexed tokens
- `M`: total size of stored document metadata
- `d`: postings list size for a single term
- `d1`, `d2`, ...: postings sizes for multiple query terms
- `p1`, `p2`, ...: positional list sizes for phrase terms
- `D`: number of documents
- `F`: number of filter values checked in metadata
- `C`: number of candidate documents after query matching
- `q`: number of scoring terms in the query
- `Q`: number of quotes stored in a document
- `L`: average token or string length used by the operation
- `V`: vocabulary size

## Why The Costs Look Like This

### Build Index

The indexer in [src/indexer.py](/Users/adil/Documents/University/WebServices2/src/indexer.py:1) tokenizes each document and records each token position once. That makes indexing linear in the total number of tokens rather than quadratic in the number of documents or terms.

### Query Execution

The search layer in [src/search.py](/Users/adil/Documents/University/WebServices2/src/search.py:1) resolves terms through dictionaries, then combines postings with set intersection or union. Phrase search is more expensive than term search because it has to inspect position lists inside shared documents rather than just presence/absence.

### TF-IDF Ranking

The ranker in [src/ranking.py](/Users/adil/Documents/University/WebServices2/src/ranking.py:1) does not score every document in the corpus. It only scores the candidate set returned by query matching, so ranking cost scales with the match set, not the full collection.

### Suggestions

The suggestion path in [src/suggest.py](/Users/adil/Documents/University/WebServices2/src/suggest.py:1) is intentionally a fallback only when search misses. It scans the vocabulary and computes Levenshtein distance against filtered candidates. That is the heaviest per-query algorithm in the system, which is why it is only used after no exact results are found.

## Practical Interpretation

For the current coursework corpus, all search operations are effectively fast because the collection is small. The complexity discussion matters more as an explanation of scaling behavior:

- indexing grows linearly with total token count
- phrase search becomes more expensive as term positions get denser
- ranking stays manageable if candidate generation is selective
- query suggestions are the least scalable part and would be the first area to optimize further on a larger corpus

## Possible Future Optimisations

If the dataset grew significantly, the most practical improvements would be:

1. Sort AND-query terms by postings size before intersection.
2. Cache tokenized metadata for author/tag filters.
3. Pre-compute or cache IDF values.
4. Replace brute-force suggestion scans with a BK-tree or another approximate-match index.
