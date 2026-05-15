"""Structured data models for crawl, index, and search operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from src.exceptions import IndexValidationError


@dataclass(frozen=True)
class Quote:
    """Structured quote data extracted from a page."""

    text: str
    author: str
    tags: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Serialize quote metadata to a JSON-compatible dictionary."""
        return {
            "text": self.text,
            "author": self.author,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> Quote:
        """Create quote metadata from a JSON-compatible dictionary."""
        validate_mapping_keys(payload, {"text", "author", "tags"}, "quote")
        raw_tags = payload["tags"]
        if not isinstance(raw_tags, list):
            raise IndexValidationError("Invalid index structure: quote tags must be a list.")
        return cls(
            text=str(payload["text"]),
            author=str(payload["author"]),
            tags=[str(tag) for tag in raw_tags],
        )


@dataclass(frozen=True)
class PageContent:
    """Parsed content for a crawled page."""

    url: str
    quotes: list[Quote]
    next_page: str | None


@dataclass(frozen=True)
class Document:
    """Indexable document payload."""

    document_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Posting:
    """Per-document posting statistics for a term."""

    frequency: int
    positions: list[int]

    def to_dict(self) -> dict[str, Any]:
        """Serialize a posting to a JSON-compatible dictionary."""
        return {
            "frequency": self.frequency,
            "positions": self.positions,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> Posting:
        """Create a posting from a JSON-compatible dictionary."""
        validate_mapping_keys(payload, {"frequency", "positions"}, "posting")
        positions = payload["positions"]
        if not isinstance(positions, list):
            raise IndexValidationError("Invalid index structure: posting positions must be a list.")
        return cls(
            frequency=int(payload["frequency"]),
            positions=[int(position) for position in positions],
        )


@dataclass(frozen=True)
class TermInfo:
    """Aggregate statistics and postings for a term."""

    document_frequency: int
    total_frequency: int
    postings: dict[str, Posting]

    def to_dict(self) -> dict[str, Any]:
        """Serialize term statistics to a JSON-compatible dictionary."""
        return {
            "document_frequency": self.document_frequency,
            "total_frequency": self.total_frequency,
            "postings": {
                document_id: posting.to_dict()
                for document_id, posting in self.postings.items()
            },
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> TermInfo:
        """Create term statistics from a JSON-compatible dictionary."""
        validate_mapping_keys(payload, {"document_frequency", "total_frequency", "postings"}, "term info")
        raw_postings = payload["postings"]
        if not isinstance(raw_postings, Mapping):
            raise IndexValidationError("Invalid index structure: term postings must be an object.")
        return cls(
            document_frequency=int(payload["document_frequency"]),
            total_frequency=int(payload["total_frequency"]),
            postings={
                str(document_id): Posting.from_dict(posting)
                for document_id, posting in raw_postings.items()
            },
        )


@dataclass(frozen=True)
class InvertedIndex:
    """Serializable inverted index with document metadata."""

    documents: dict[str, dict[str, Any]]
    terms: dict[str, TermInfo]

    @property
    def document_count(self) -> int:
        """Return the number of indexed documents."""
        return len(self.documents)

    @property
    def term_count(self) -> int:
        """Return the number of unique indexed terms."""
        return len(self.terms)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the index to a JSON-compatible dictionary."""
        return {
            "documents": self.documents,
            "terms": {
                term: term_info.to_dict()
                for term, term_info in self.terms.items()
            },
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> InvertedIndex:
        """Create an index from a JSON-compatible dictionary."""
        validate_mapping_keys(payload, {"documents", "terms"}, "inverted index")
        raw_documents = payload["documents"]
        raw_terms = payload["terms"]
        if not isinstance(raw_documents, Mapping):
            raise IndexValidationError("Invalid index structure: documents must be an object.")
        if not isinstance(raw_terms, Mapping):
            raise IndexValidationError("Invalid index structure: terms must be an object.")

        documents = {
            str(document_id): validate_document_metadata(metadata, str(document_id))
            for document_id, metadata in raw_documents.items()
        }
        terms = {
            str(term): TermInfo.from_dict(term_payload)
            for term, term_payload in raw_terms.items()
        }
        return cls(documents=documents, terms=terms)


@dataclass(frozen=True)
class RankedDocument:
    """A search match paired with a ranking score."""

    document_id: str
    score: float


def validate_mapping_keys(
    payload: Mapping[str, Any],
    required_keys: set[str],
    context: str,
) -> None:
    """Ensure a mapping contains the required keys for a given context."""
    missing_keys = required_keys.difference(payload.keys())
    if missing_keys:
        missing_list = ", ".join(sorted(missing_keys))
        raise IndexValidationError(
            f"Invalid index structure: missing {context} fields: {missing_list}."
        )


def validate_document_metadata(metadata: Any, document_id: str) -> dict[str, Any]:
    """Validate document metadata loaded from storage."""
    if not isinstance(metadata, Mapping):
        raise IndexValidationError(
            f"Invalid index structure: document metadata for '{document_id}' must be an object."
        )

    normalized = {str(key): value for key, value in metadata.items()}
    if "quotes" in normalized:
        raw_quotes = normalized["quotes"]
        if not isinstance(raw_quotes, list):
            raise IndexValidationError(
                f"Invalid index structure: quotes metadata for '{document_id}' must be a list."
            )
        normalized["quotes"] = [Quote.from_dict(quote).to_dict() for quote in raw_quotes]
    return normalized
