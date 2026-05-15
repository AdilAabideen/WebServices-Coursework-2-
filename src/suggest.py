"""Query suggestion helpers based on edit distance and term frequency."""

from __future__ import annotations

from dataclasses import dataclass

from src.config import MAX_QUERY_SUGGESTIONS
from src.models import InvertedIndex
from src.query_parser import ParsedQuery


@dataclass(frozen=True)
class Suggestion:
    """A ranked query suggestion candidate."""

    term: str
    distance: int
    frequency: int


def levenshtein_distance(source: str, target: str) -> int:
    """Return the Levenshtein edit distance between two strings."""
    if source == target:
        return 0
    if not source:
        return len(target)
    if not target:
        return len(source)

    previous_row = list(range(len(target) + 1))
    for source_index, source_char in enumerate(source, start=1):
        current_row = [source_index]
        for target_index, target_char in enumerate(target, start=1):
            insertion = current_row[target_index - 1] + 1
            deletion = previous_row[target_index] + 1
            substitution = previous_row[target_index - 1] + (source_char != target_char)
            current_row.append(min(insertion, deletion, substitution))
        previous_row = current_row
    return previous_row[-1]


def suggest_terms(
    index: InvertedIndex,
    term: str,
    *,
    limit: int = MAX_QUERY_SUGGESTIONS,
) -> list[Suggestion]:
    """Return ranked near-match suggestions for a misspelled normalized term."""
    if not term or term in index.terms:
        return []

    max_distance = _max_edit_distance(len(term))
    candidates: list[Suggestion] = []

    for candidate_term, term_info in index.terms.items():
        if abs(len(candidate_term) - len(term)) > max_distance:
            continue

        distance = levenshtein_distance(term, candidate_term)
        if distance > max_distance:
            continue

        candidates.append(
            Suggestion(
                term=candidate_term,
                distance=distance,
                frequency=term_info.total_frequency,
            )
        )

    return sorted(
        candidates,
        key=lambda item: (item.distance, -item.frequency, item.term),
    )[:limit]


def suggest_query(index: InvertedIndex, query: ParsedQuery) -> str | None:
    """Return a corrected query string when missing text terms have close suggestions."""
    replacements_made = False

    suggested_terms: list[str] = []
    for term in query.terms:
        suggestion = _best_term_suggestion(index, term)
        if suggestion is None:
            suggested_terms.append(term)
            continue
        suggested_terms.append(suggestion.term)
        replacements_made = True

    suggested_phrases: list[list[str]] = []
    for phrase in query.phrases:
        suggested_phrase: list[str] = []
        for term in phrase:
            suggestion = _best_term_suggestion(index, term)
            if suggestion is None:
                suggested_phrase.append(term)
                continue
            suggested_phrase.append(suggestion.term)
            replacements_made = True
        suggested_phrases.append(suggested_phrase)

    if not replacements_made:
        return None

    parts: list[str] = []
    for phrase in suggested_phrases:
        parts.append(f'"{" ".join(phrase)}"')
    parts.extend(suggested_terms)
    parts.extend(f"author:{' '.join(tokens)}" for tokens in query.author_filters)
    parts.extend(f"tag:{' '.join(tokens)}" for tokens in query.tag_filters)
    parts.extend(f"-{term}" for term in query.excluded_terms)

    separator = " OR " if query.mode == "or" else " "
    return separator.join(parts)


def _best_term_suggestion(index: InvertedIndex, term: str) -> Suggestion | None:
    """Return the top suggestion for a term if one exists."""
    if term in index.terms:
        return None

    suggestions = suggest_terms(index, term, limit=1)
    if not suggestions:
        return None
    return suggestions[0]


def _max_edit_distance(term_length: int) -> int:
    """Return a conservative edit-distance threshold based on term length."""
    if term_length <= 4:
        return 1
    if term_length <= 8:
        return 2
    return 3
