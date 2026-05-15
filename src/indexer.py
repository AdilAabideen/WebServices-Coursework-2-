"""Tokenisation and inverted index utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Iterable

from src.crawler import PageContent


TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)


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
        return {
            "frequency": self.frequency,
            "positions": self.positions,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Posting:
        return cls(
            frequency=int(payload["frequency"]),
            positions=[int(position) for position in payload["positions"]],
        )


@dataclass(frozen=True)
class TermInfo:
    """Aggregate statistics and postings for a term."""

    document_frequency: int
    total_frequency: int
    postings: dict[str, Posting]

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_frequency": self.document_frequency,
            "total_frequency": self.total_frequency,
            "postings": {
                document_id: posting.to_dict()
                for document_id, posting in self.postings.items()
            },
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> TermInfo:
        return cls(
            document_frequency=int(payload["document_frequency"]),
            total_frequency=int(payload["total_frequency"]),
            postings={
                document_id: Posting.from_dict(posting)
                for document_id, posting in payload["postings"].items()
            },
        )


@dataclass(frozen=True)
class InvertedIndex:
    """Serializable inverted index with document metadata."""

    documents: dict[str, dict[str, Any]]
    terms: dict[str, TermInfo]

    @property
    def document_count(self) -> int:
        return len(self.documents)

    @property
    def term_count(self) -> int:
        return len(self.terms)

    def to_dict(self) -> dict[str, Any]:
        return {
            "documents": self.documents,
            "terms": {
                term: term_info.to_dict()
                for term, term_info in self.terms.items()
            },
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> InvertedIndex:
        documents = dict(payload["documents"])
        terms = {
            term: TermInfo.from_dict(term_payload)
            for term, term_payload in payload["terms"].items()
        }
        return cls(documents=documents, terms=terms)


def tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase normalized terms."""
    return TOKEN_PATTERN.findall(text.lower())


def build_inverted_index(documents: Iterable[Document]) -> InvertedIndex:
    """Build a positional inverted index from documents."""
    document_metadata: dict[str, dict[str, Any]] = {}
    term_postings: dict[str, dict[str, Posting]] = {}

    for document in documents:
        if document.document_id in document_metadata:
            raise ValueError(f"Duplicate document ID: {document.document_id}")

        tokens = tokenize(document.text)
        document_metadata[document.document_id] = {
            "document_id": document.document_id,
            **document.metadata,
            "token_count": len(tokens),
        }

        positions_by_term: dict[str, list[int]] = {}
        for position, token in enumerate(tokens):
            positions_by_term.setdefault(token, []).append(position)

        for term, positions in positions_by_term.items():
            term_postings.setdefault(term, {})
            term_postings[term][document.document_id] = Posting(
                frequency=len(positions),
                positions=positions,
            )

    terms = {
        term: TermInfo(
            document_frequency=len(postings),
            total_frequency=sum(posting.frequency for posting in postings.values()),
            postings=postings,
        )
        for term, postings in term_postings.items()
    }

    return InvertedIndex(documents=document_metadata, terms=terms)


def build_index_from_pages(pages: Iterable[PageContent]) -> InvertedIndex:
    """Convert crawled pages into documents and build an inverted index."""
    return build_inverted_index(page_to_document(page) for page in pages)


def page_to_document(page: PageContent) -> Document:
    """Convert a crawled page into an indexable document."""
    authors = sorted({quote.author for quote in page.quotes if quote.author})
    tags = sorted({tag for quote in page.quotes for tag in quote.tags})
    lines = [
        " ".join([quote.text, quote.author, *quote.tags]).strip()
        for quote in page.quotes
    ]
    text = "\n".join(line for line in lines if line)

    return Document(
        document_id=page.url,
        text=text,
        metadata={
            "url": page.url,
            "quote_count": len(page.quotes),
            "authors": authors,
            "tags": tags,
        },
    )
