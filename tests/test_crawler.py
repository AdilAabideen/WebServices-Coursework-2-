"""Tests for the polite crawler.

Test type: crawler-focused unit tests with mocked network behavior and regression coverage.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

from src.crawler import Crawler
from src.exceptions import CrawlError


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

ACTUAL_PAGE_HTML = (
    Path(__file__).with_name("fixtures") / "quotes_page_1.html"
).read_text(encoding="utf-8")


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


# Crawler unit test for extract next page link.
def test_extract_next_page_link() -> None:
    crawler = Crawler()
    page = crawler.parse_page("https://quotes.toscrape.com/", ACTUAL_PAGE_HTML)

    assert page.next_page == "https://quotes.toscrape.com/page/2/"


# Crawler unit test for extract quote text.
def test_extract_quote_text() -> None:
    crawler = Crawler()
    page = crawler.parse_page("https://quotes.toscrape.com/", ACTUAL_PAGE_HTML)

    assert page.quotes[-1].text == "“A day without sunshine is like, you know, night.”"


# Crawler unit test for extract authors.
def test_extract_authors() -> None:
    crawler = Crawler()
    page = crawler.parse_page("https://quotes.toscrape.com/", ACTUAL_PAGE_HTML)

    assert page.quotes[0].author == "Albert Einstein"
    assert page.quotes[-1].author == "Steve Martin"


# Crawler unit test for extract tags.
def test_extract_tags() -> None:
    crawler = Crawler()
    page = crawler.parse_page("https://quotes.toscrape.com/", ACTUAL_PAGE_HTML)

    assert page.quotes[6].tags == ["life", "love"]


# Crawler unit test for parse actual page extracts all quotes.
def test_parse_actual_page_extracts_all_quotes() -> None:
    crawler = Crawler()
    page = crawler.parse_page("https://quotes.toscrape.com/", ACTUAL_PAGE_HTML)

    assert len(page.quotes) == 10


# Crawler unit test for avoid duplicate urls.
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


# Crawler unit test for crawl can stop after max pages.
def test_crawl_can_stop_after_max_pages() -> None:
    session = MockSession(
        {
            "https://quotes.toscrape.com/": MockResponse(SINGLE_PAGE_HTML),
            "https://quotes.toscrape.com/page/2/": MockResponse(LAST_PAGE_HTML),
        }
    )
    crawler = Crawler(session=session)

    pages = crawler.crawl(max_pages=1)

    assert [page.url for page in pages] == ["https://quotes.toscrape.com/"]
    assert session.requested_urls == ["https://quotes.toscrape.com/"]


# Crawler unit test for handle failed request.
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


# Crawler unit test for handle timeout request.
def test_handle_timeout_request() -> None:
    session = MockSession(
        {
            "https://quotes.toscrape.com/": requests.Timeout("slow"),
        }
    )
    crawler = Crawler(session=session)

    pages = crawler.crawl()

    assert pages == []
    assert crawler.visited_urls == {"https://quotes.toscrape.com/"}


# Crawler unit test for delay function is called between requests.
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


# Crawler unit test for crawler constructor validates inputs.
def test_crawler_constructor_validates_inputs() -> None:
    try:
        Crawler(start_url="")
    except CrawlError as exc:
        assert "start URL" in str(exc)
    else:
        raise AssertionError("Expected CrawlError for empty start URL")

    try:
        Crawler(delay_seconds=-1.0)
    except CrawlError as exc:
        assert "delay" in str(exc)
    else:
        raise AssertionError("Expected CrawlError for negative delay")

    try:
        Crawler(timeout=0.0)
    except CrawlError as exc:
        assert "timeout" in str(exc)
    else:
        raise AssertionError("Expected CrawlError for invalid timeout")


# Crawler unit test for crawl rejects negative max pages.
def test_crawl_rejects_negative_max_pages() -> None:
    crawler = Crawler()

    try:
        crawler.crawl(max_pages=-1)
    except CrawlError as exc:
        assert "max_pages" in str(exc)
    else:
        raise AssertionError("Expected CrawlError for negative max_pages")


# Crawler unit test for normalize url rejects empty string.
def test_normalize_url_rejects_empty_string() -> None:
    crawler = Crawler()

    try:
        crawler.normalize_url("")
    except CrawlError as exc:
        assert "empty URL" in str(exc)
    else:
        raise AssertionError("Expected CrawlError for empty URL")


# Crawler unit test for extract next page link handles missing href.
def test_extract_next_page_link_handles_missing_href() -> None:
    crawler = Crawler()
    soup = BeautifulSoup('<li class="next"><a>Next</a></li>', "html.parser")

    assert crawler.extract_next_page_link(soup, base_url="https://quotes.toscrape.com/") is None


# Crawler unit test for extract quote text handles missing and nested text node.
def test_extract_quote_text_handles_missing_and_nested_text_node() -> None:
    crawler = Crawler()
    assert crawler._extract_quote_text(None) == ""

    soup = BeautifulSoup('<span class="text"><b>Nested text</b></span>', "html.parser")
    text_node = soup.select_one("span.text")

    assert text_node is not None
    assert crawler._extract_quote_text(text_node) == "Nested text"
