"""Persistence helpers for the inverted index."""

from __future__ import annotations

import json
from pathlib import Path

from src.indexer import InvertedIndex


class IndexStorageError(Exception):
    """Raised when index persistence or loading fails."""


def save_index(index: InvertedIndex, path: str | Path) -> None:
    """Save an inverted index to a JSON file."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(index.to_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )


def load_index(path: str | Path) -> InvertedIndex:
    """Load an inverted index from a JSON file."""
    source = Path(path)

    if not source.exists():
        raise IndexStorageError(f"Index file not found: {source}")

    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
        return InvertedIndex.from_dict(payload)
    except json.JSONDecodeError as exc:
        raise IndexStorageError(f"Index file is corrupt: {source}") from exc
    except (KeyError, TypeError, ValueError) as exc:
        raise IndexStorageError(f"Index file has invalid structure: {source}") from exc
