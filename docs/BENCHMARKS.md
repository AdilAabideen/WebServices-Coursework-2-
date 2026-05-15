# Benchmarks

## Purpose

These benchmarks provide a small, repeatable performance snapshot for the current search engine implementation. They are not intended to be statistically rigorous system benchmarks; they are intended to show the cost of the main operations in the coursework pipeline.

## Command

Run the benchmark suite from the repository root:

```bash
python -m src.benchmark
```

Useful options:

```bash
python -m src.benchmark --skip-crawl
python -m src.benchmark --iterations 500
python -m src.benchmark --crawl-pages 10 --crawl-delay 0
```

Notes:

- The default benchmark crawl uses the same 6-second politeness window as the main crawler commands.
- Use `--crawl-delay 0` only when you explicitly want to measure crawler overhead without waiting time.
- Results vary by machine, Python version, network conditions, and whether the saved index is already present.

## Sample Results

Sample run captured on the coursework development machine with Python 3.11 and the current `data/index.json`, using `--crawl-delay 0` to isolate crawler overhead:

| Metric | Value | Notes |
| --- | --- | --- |
| `crawl_time` | 3.173 s | 10 pages crawled with `delay=0.0s` |
| `build_index_time` | 2.672 ms | 10 documents reconstructed from metadata |
| `build_index_from_pages` | 2.132 ms | 10 crawled pages reused in-memory |
| `index_size` | 377277 bytes | 368.43 KiB persisted JSON |
| `query_latency` | 0.012 ms | Parse + execute + rank for `love` |
| `tfidf_latency` | 0.009 ms | Rank 10 candidate documents for `love` |
| `suggestion_latency` | 3.332 ms | Suggestion path for `frends` |

## Interpretation

- Crawl time is dominated by HTTP/network cost rather than local CPU work.
- Index build time is low because the collection is small: 10 page-documents and roughly a few thousand searchable tokens.
- Query latency is effectively constant at this dataset size because vocabulary lookup is dictionary-backed and candidate sets are small.
- TF-IDF ranking is cheap because only candidate documents are scored.
- Suggestion latency is noticeably higher than normal search because it compares the misspelled term against the vocabulary using edit distance, which is quadratic in word length for each candidate.

## Reproducing The Numbers

1. Ensure `data/index.json` exists:

```bash
python -m src.main build
```

2. Run the benchmark script:

```bash
python -m src.benchmark
```

3. Compare the output against the values above. Small differences are expected.
