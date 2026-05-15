"""Parsing utilities for advanced search queries."""

from __future__ import annotations

from dataclasses import dataclass
import re

from src.exceptions import QuerySyntaxError
from src.indexer import tokenize


TOKEN_OR_QUOTE_PATTERN = re.compile(r'"[^"]+"|\S+')


@dataclass(frozen=True)
class ParsedQuery:
    """Normalized representation of a supported search query."""

    mode: str
    terms: list[str]
    phrases: list[list[str]]
    excluded_terms: list[str]
    author_filters: list[list[str]]
    tag_filters: list[list[str]]

    def display_text(self) -> str:
        """Return a readable normalized form of the query."""
        parts: list[str] = []
        for phrase in self.phrases:
            parts.append(f'"{" ".join(phrase)}"')
        parts.extend(self.terms)
        parts.extend(f"author:{' '.join(tokens)}" for tokens in self.author_filters)
        parts.extend(f"tag:{' '.join(tokens)}" for tokens in self.tag_filters)
        parts.extend(f"-{term}" for term in self.excluded_terms)

        separator = " OR " if self.mode == "or" else " "
        return separator.join(parts)

    def scoring_terms(self) -> list[str]:
        """Return normalized content terms that should contribute to ranking."""
        ordered_terms = [*self.terms]
        for phrase in self.phrases:
            ordered_terms.extend(phrase)

        deduplicated: list[str] = []
        for term in ordered_terms:
            if term not in deduplicated:
                deduplicated.append(term)
        return deduplicated

    def has_positive_clauses(self) -> bool:
        """Return whether the query contains any non-exclusion clause."""
        return bool(self.terms or self.phrases or self.author_filters or self.tag_filters)


def parse_query(raw_query: str) -> ParsedQuery:
    """Parse a user query into structured search clauses."""
    query = raw_query.strip()
    if not query:
        raise QuerySyntaxError("Please provide a non-empty query.")

    if query.count('"') % 2 != 0:
        raise QuerySyntaxError("Query contains an unmatched quote.")

    tokens = TOKEN_OR_QUOTE_PATTERN.findall(query)
    if not tokens:
        raise QuerySyntaxError("Please provide a non-empty query.")

    mode = "and"
    parsed_terms: list[str] = []
    parsed_phrases: list[list[str]] = []
    excluded_terms: list[str] = []
    author_filters: list[list[str]] = []
    tag_filters: list[list[str]] = []

    previous_was_or = False

    for token in tokens:
        if token.upper() == "OR":
            if previous_was_or or not (parsed_terms or parsed_phrases or author_filters or tag_filters):
                raise QuerySyntaxError("OR must appear between valid query clauses.")
            mode = "or"
            previous_was_or = True
            continue

        previous_was_or = False

        if token.startswith("-"):
            normalized = tokenize(token[1:])
            if not normalized:
                raise QuerySyntaxError("Exclusion operator must be followed by a term.")
            excluded_terms.extend(normalized)
            continue

        if token.startswith("author:"):
            normalized = tokenize(token.removeprefix("author:"))
            if not normalized:
                raise QuerySyntaxError("Author filter must include a value.")
            author_filters.append(normalized)
            continue

        if token.startswith("tag:"):
            normalized = tokenize(token.removeprefix("tag:"))
            if not normalized:
                raise QuerySyntaxError("Tag filter must include a value.")
            tag_filters.append(normalized)
            continue

        if token.startswith('"') and token.endswith('"'):
            normalized = tokenize(token[1:-1])
            if not normalized:
                raise QuerySyntaxError("Phrase queries must contain at least one word.")
            parsed_phrases.append(normalized)
            continue

        normalized = tokenize(token)
        if not normalized:
            raise QuerySyntaxError("Query term must contain at least one searchable character.")
        parsed_terms.extend(normalized)

    if previous_was_or:
        raise QuerySyntaxError("OR must appear between valid query clauses.")

    parsed_query = ParsedQuery(
        mode=mode,
        terms=parsed_terms,
        phrases=parsed_phrases,
        excluded_terms=excluded_terms,
        author_filters=author_filters,
        tag_filters=tag_filters,
    )
    if not parsed_query.has_positive_clauses():
        raise QuerySyntaxError("Please provide at least one searchable term or filter.")
    return parsed_query
