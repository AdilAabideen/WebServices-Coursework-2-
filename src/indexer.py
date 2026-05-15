"""Tokenisation and inverted index utilities."""

from __future__ import annotations

import re
from typing import Any, Iterable

from src.config import TOKEN_PATTERN
from src.exceptions import DuplicateDocumentError
from src.models import Document, InvertedIndex, PageContent, Posting, TermInfo


TOKEN_REGEX = re.compile(TOKEN_PATTERN, re.UNICODE)


def tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase normalized terms."""
    return TOKEN_REGEX.findall(text.lower())


def build_inverted_index(documents: Iterable[Document]) -> InvertedIndex:
    """Build a positional inverted index from documents."""
    document_metadata: dict[str, dict[str, Any]] = {}
    term_postings: dict[str, dict[str, Posting]] = {}

    for document in documents:
        if document.document_id in document_metadata:
            raise DuplicateDocumentError(
                f"Duplicate document ID encountered while indexing: {document.document_id}"
            )

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
    serialized_quotes = [quote.to_dict() for quote in page.quotes]
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
            "quotes": serialized_quotes,
        },
    )
