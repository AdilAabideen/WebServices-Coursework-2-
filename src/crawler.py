"""Polite crawler for traversing quote pages."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urljoin
import time

import requests
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class Quote:
    """Structured quote data extracted from a page."""

    text: str
    author: str
    tags: list[str]


@dataclass(frozen=True)
class PageContent:
    """Parsed content for a crawled page."""

    url: str
    quotes: list[Quote]
    next_page: str | None


class Crawler:
    """Crawl quote pages while respecting a politeness delay."""

    def __init__(
        self,
        start_url: str = "https://quotes.toscrape.com/",
        *,
        delay_seconds: float = 6.0,
        session: requests.Session | None = None,
        sleep_func: Callable[[float], None] = time.sleep,
        time_func: Callable[[], float] = time.monotonic,
        timeout: float = 10.0,
    ) -> None:
        self.start_url = start_url
        self.delay_seconds = delay_seconds
        self.session = session or requests.Session()
        self.sleep_func = sleep_func
        self.time_func = time_func
        self.timeout = timeout
        self.visited_urls: set[str] = set()
        self._queued_urls: set[str] = set()
        self._last_request_time: float | None = None

    def crawl(self, *, max_pages: int | None = None) -> list[PageContent]:
        """Visit reachable quote pages from the start URL."""
        pages: list[PageContent] = []
        pending_urls = deque([self.start_url])
        self._queued_urls = {self.normalize_url(self.start_url)}

        while pending_urls:
            if max_pages is not None and len(pages) >= max_pages:
                break

            current_url = self.normalize_url(pending_urls.popleft())
            self._queued_urls.discard(current_url)

            if current_url in self.visited_urls:
                continue

            self.visited_urls.add(current_url)
            html = self.fetch(current_url)
            if html is None:
                continue

            page = self.parse_page(current_url, html)
            pages.append(page)

            if page.next_page is not None:
                next_url = self.normalize_url(page.next_page)
                if next_url not in self.visited_urls and next_url not in self._queued_urls:
                    pending_urls.append(next_url)
                    self._queued_urls.add(next_url)

        return pages

    def fetch(self, url: str) -> str | None:
        """Fetch a page without allowing network failures to abort the crawl."""
        self._respect_politeness_window()
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException:
            self._mark_request_complete()
            return None
        self._mark_request_complete()
        return response.text

    def parse_page(self, url: str, html: str) -> PageContent:
        """Parse quotes and pagination from a page."""
        soup = BeautifulSoup(html, "html.parser")
        return PageContent(
            url=url,
            quotes=self.extract_quotes(soup),
            next_page=self.extract_next_page_link(soup, base_url=url),
        )

    def extract_quotes(self, soup: BeautifulSoup) -> list[Quote]:
        """Extract quote text, author, and tags from the page."""
        quotes: list[Quote] = []
        for quote_node in soup.select("div.quote"):
            text_node = quote_node.select_one("span.text")
            author_node = quote_node.select_one("small.author")
            tag_nodes = quote_node.select("a.tag")

            text = self._extract_quote_text(text_node)
            author = author_node.get_text(strip=True) if author_node else ""
            tags = [tag.get_text(strip=True) for tag in tag_nodes]

            quotes.append(Quote(text=text, author=author, tags=tags))

        return quotes

    def extract_next_page_link(self, soup: BeautifulSoup, *, base_url: str) -> str | None:
        """Return the absolute next-page URL if pagination is present."""
        next_link = soup.select_one("li.next a")
        if next_link is None:
            return None

        href = next_link.get("href")
        if not href:
            return None

        return self.normalize_url(urljoin(base_url, href))

    def normalize_url(self, url: str) -> str:
        """Normalize URLs so duplicate pages are not revisited."""
        return url.rstrip("/") + "/"

    def _respect_politeness_window(self) -> None:
        if self._last_request_time is None:
            return

        elapsed = self.time_func() - self._last_request_time
        remaining_delay = self.delay_seconds - elapsed
        if remaining_delay > 0:
            self.sleep_func(remaining_delay)

    def _mark_request_complete(self) -> None:
        self._last_request_time = self.time_func()

    def _extract_quote_text(self, text_node: BeautifulSoup | None) -> str:
        """Prefer the direct quote text even when the HTML is malformed."""
        if text_node is None:
            return ""

        for child in text_node.children:
            if isinstance(child, str):
                candidate = child.strip()
                if candidate:
                    return candidate

        return text_node.get_text(strip=True)
