"""Tests for the polite crawler."""

from __future__ import annotations

from typing import Any

import requests

from src.crawler import Crawler


SINGLE_PAGE_HTML = """
<html>
  <body>
    <div class="quote">
      <span class="text">"Life is about making an impact."</span>
      <span>
        <small class="author">Kevin Kruse</small>
      </span>
      <div class="tags">
        <a class="tag" href="/tag/life/page/1/">life</a>
        <a class="tag" href="/tag/inspirational/page/1/">inspirational</a>
      </div>
    </div>
    <li class="next">
      <a href="/page/2/">Next <span aria-hidden="true">&rarr;</span></a>
    </li>
  </body>
</html>
"""


LAST_PAGE_HTML = """
<html>
  <body>
    <div class="quote">
      <span class="text">"Be yourself; everyone else is already taken."</span>
      <span>
        <small class="author">Oscar Wilde</small>
      </span>
      <div class="tags">
        <a class="tag" href="/tag/humor/page/1/">humor</a>
      </div>
    </div>
  </body>
</html>
"""


class MockResponse:
    """Minimal response stub for requests-based tests."""

    def __init__(self, text: str, status_code: int = 200) -> None:
        self.text = text
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"status code: {self.status_code}")


class MockSession:
    """Session stub backed by a fixed response map."""

    def __init__(self, responses: dict[str, Any]) -> None:
        self.responses = responses
        self.requested_urls: list[str] = []

    def get(self, url: str, timeout: float) -> MockResponse:
        self.requested_urls.append(url)
        response = self.responses[url]
        if isinstance(response, Exception):
            raise response
        return response


def test_extract_next_page_link() -> None:
    crawler = Crawler()
    page = crawler.parse_page("https://quotes.toscrape.com/", SINGLE_PAGE_HTML)

    assert page.next_page == "https://quotes.toscrape.com/page/2/"


def test_extract_quote_text() -> None:
    crawler = Crawler()
    page = crawler.parse_page("https://quotes.toscrape.com/", SINGLE_PAGE_HTML)

    assert page.quotes[0].text == '"Life is about making an impact."'


def test_extract_authors() -> None:
    crawler = Crawler()
    page = crawler.parse_page("https://quotes.toscrape.com/", SINGLE_PAGE_HTML)

    assert page.quotes[0].author == "Kevin Kruse"


def test_extract_tags() -> None:
    crawler = Crawler()
    page = crawler.parse_page("https://quotes.toscrape.com/", SINGLE_PAGE_HTML)

    assert page.quotes[0].tags == ["life", "inspirational"]


def test_avoid_duplicate_urls() -> None:
    session = MockSession(
        {
            "https://quotes.toscrape.com/": MockResponse(SINGLE_PAGE_HTML),
            "https://quotes.toscrape.com/page/2/": MockResponse(LAST_PAGE_HTML),
        }
    )
    crawler = Crawler(session=session)

    pages = crawler.crawl()

    assert [page.url for page in pages] == [
        "https://quotes.toscrape.com/",
        "https://quotes.toscrape.com/page/2/",
    ]
    assert session.requested_urls == [
        "https://quotes.toscrape.com/",
        "https://quotes.toscrape.com/page/2/",
    ]


def test_handle_failed_request() -> None:
    session = MockSession(
        {
            "https://quotes.toscrape.com/": requests.ConnectionError("boom"),
        }
    )
    crawler = Crawler(session=session)

    pages = crawler.crawl()

    assert pages == []
    assert crawler.visited_urls == {"https://quotes.toscrape.com/"}


def test_delay_function_is_called_between_requests() -> None:
    sleep_calls: list[float] = []
    time_values = iter([100.0, 102.0, 106.0])
    session = MockSession(
        {
            "https://quotes.toscrape.com/": MockResponse(SINGLE_PAGE_HTML),
            "https://quotes.toscrape.com/page/2/": MockResponse(LAST_PAGE_HTML),
        }
    )
    crawler = Crawler(
        session=session,
        delay_seconds=6.0,
        sleep_func=sleep_calls.append,
        time_func=lambda: next(time_values),
    )

    crawler.crawl()

    assert sleep_calls == [4.0]
