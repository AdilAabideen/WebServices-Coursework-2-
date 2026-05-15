# WebServices2

Initial scaffold for the `WebServices2` project.

## Overview

This repository starts with a minimal Python application layout focused on:

- clear source and test separation
- a runnable module entry point
- a smoke test to confirm the package imports cleanly
- basic project hygiene for Git and Python tooling

## Project Structure

```text
.
├── data/
├── requirements.txt
├── src/
│   ├── __init__.py
│   └── main.py
└── tests/
    └── test_smoke.py
```

## Getting Started

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
python -m src.main
```

4. Run tests:

```bash
pytest
```

## Next Steps

- add application modules under `src/`
- expand test coverage beyond smoke checks
- document the project purpose, architecture, and usage in more detail
