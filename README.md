# WebServices2

Python command-line search engine coursework for `https://quotes.toscrape.com/`.

## Overview

The project currently supports:

- polite crawling across all quote pages
- positional inverted indexing with per-document frequencies and token positions
- JSON save/load for the built index
- CLI search commands: `build`, `load`, `print`, and `find`
- smoothed TF-IDF ranking
- phrase, `OR`, exclusion, author, and tag queries
- misspelling suggestions for failed text queries

## Getting Started

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Build or load the index:

```bash
python -m src.main build
python -m src.main load
```

4. Run searches:

```bash
python -m src.main find love
python -m src.main find '"good friends"'
python -m src.main find good OR friends
python -m src.main find author:einstein
```

5. Run tests:

```bash
pytest
```

## Benchmarking And Analysis

- Benchmark script: `python -m src.benchmark`
- Benchmark notes: [docs/BENCHMARKS.md](/Users/adil/Documents/University/WebServices2/docs/BENCHMARKS.md)
- Complexity analysis: [docs/COMPLEXITY.md](/Users/adil/Documents/University/WebServices2/docs/COMPLEXITY.md)

## Continuous Integration

GitHub Actions runs the Python test pipeline on pushes and pull requests. The workflow installs dependencies, runs the CLI entry point, and executes `pytest`.
