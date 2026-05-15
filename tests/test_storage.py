"""Tests for index persistence."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.indexer import Document, build_inverted_index
from src.storage import IndexStorageError, load_index, save_index


def build_sample_index():
    return build_inverted_index(
        [
            Document(document_id="doc-1", text="alpha beta alpha", metadata={"url": "a"}),
            Document(document_id="doc-2", text="gamma beta", metadata={"url": "b"}),
        ]
    )


def test_save_json(tmp_path: Path) -> None:
    path = tmp_path / "index.json"

    save_index(build_sample_index(), path)

    assert path.exists()
    assert '"documents"' in path.read_text(encoding="utf-8")


def test_load_saved_json(tmp_path: Path) -> None:
    path = tmp_path / "index.json"
    index = build_sample_index()
    save_index(index, path)

    loaded = load_index(path)

    assert loaded.documents["doc-1"]["url"] == "a"
    assert loaded.terms["alpha"].postings["doc-1"].positions == [0, 2]


def test_loaded_index_equals_saved_index(tmp_path: Path) -> None:
    path = tmp_path / "index.json"
    index = build_sample_index()
    save_index(index, path)

    loaded = load_index(path)

    assert loaded == index


def test_missing_file_handled(tmp_path: Path) -> None:
    with pytest.raises(IndexStorageError, match="Index file not found"):
        load_index(tmp_path / "missing.json")


def test_corrupt_file_handled(tmp_path: Path) -> None:
    path = tmp_path / "index.json"
    path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(IndexStorageError, match="Index file is corrupt"):
        load_index(path)


def test_invalid_structure_handled(tmp_path: Path) -> None:
    path = tmp_path / "index.json"
    path.write_text('{"documents": {}, "terms": []}', encoding="utf-8")

    with pytest.raises(IndexStorageError, match="Index file has invalid structure"):
        load_index(path)
