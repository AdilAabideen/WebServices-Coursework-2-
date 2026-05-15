"""Tests for tokenisation and inverted index construction."""

from __future__ import annotations

from src.indexer import Document, build_inverted_index, page_to_document, tokenize
from src.models import PageContent, Quote


def test_case_insensitive_tokenisation() -> None:
    tokens = tokenize("Hello hello HELLO")

    assert tokens == ["hello", "hello", "hello"]


def test_punctuation_handling() -> None:
    tokens = tokenize("Hello, world! End-to-end.")

    assert tokens == ["hello", "world", "end", "to", "end"]


def test_correct_word_frequency() -> None:
    index = build_inverted_index(
        [Document(document_id="doc-1", text="alpha beta alpha")]
    )

    assert index.terms["alpha"].postings["doc-1"].frequency == 2
    assert index.terms["alpha"].total_frequency == 2


def test_correct_word_positions() -> None:
    index = build_inverted_index(
        [Document(document_id="doc-1", text="alpha beta alpha gamma")]
    )

    assert index.terms["alpha"].postings["doc-1"].positions == [0, 2]


def test_correct_document_frequency() -> None:
    index = build_inverted_index(
        [
            Document(document_id="doc-1", text="alpha beta"),
            Document(document_id="doc-2", text="alpha gamma"),
        ]
    )

    assert index.terms["alpha"].document_frequency == 2
    assert index.terms["beta"].document_frequency == 1


def test_empty_text_handling() -> None:
    index = build_inverted_index(
        [Document(document_id="doc-1", text="", metadata={"url": "empty"})]
    )

    assert index.document_count == 1
    assert index.term_count == 0
    assert index.documents["doc-1"]["token_count"] == 0


def test_page_to_document_preserves_quote_metadata() -> None:
    page = PageContent(
        url="https://quotes.toscrape.com/page/2/",
        quotes=[
            Quote(
                text="Good friends, good books, and a sleepy conscience: this is the ideal life.",
                author="Mark Twain",
                tags=["books", "contentment", "friends", "friendship", "life"],
            )
        ],
        next_page=None,
    )

    document = page_to_document(page)

    assert document.metadata["quotes"] == [
        {
            "text": "Good friends, good books, and a sleepy conscience: this is the ideal life.",
            "author": "Mark Twain",
            "tags": ["books", "contentment", "friends", "friendship", "life"],
        }
    ]
