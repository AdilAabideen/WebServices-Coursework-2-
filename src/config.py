"""Project-wide configuration constants."""

from __future__ import annotations

from pathlib import Path


DEFAULT_START_URL = "https://quotes.toscrape.com/"
DEFAULT_DELAY_SECONDS = 6.0
DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_INDEX_PATH = Path("data/index.json")
TOKEN_PATTERN = r"\w+"
MAX_SNIPPET_LENGTH = 220
MAX_QUERY_SUGGESTIONS = 3
