"""
scraper.py
----------
Step 1 of the pipeline: take a raw URL, fetch it, and turn the messy HTML
into clean, readable text we can actually chunk and embed.
"""

import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass

from config import REQUEST_TIMEOUT_SECONDS, USER_AGENT

# Tags that never contain content worth keeping
NOISE_TAGS = ["script", "style", "nav", "footer", "header", "form", "noscript", "svg", "iframe"]


@dataclass
class ScrapedPage:
    url: str
    title: str
    description: str
    text: str


class ScrapeError(Exception):
    """Raised when a URL can't be fetched or has no usable content."""
    pass


def fetch_html(url: str) -> str:
    """Download the raw HTML for a URL."""
    headers = {"User-Agent": USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ScrapeError(f"Could not fetch {url}: {exc}") from exc
    return response.text


def extract_content(html: str, url: str) -> ScrapedPage:
    """Turn raw HTML into a clean ScrapedPage (title, description, body text)."""
    soup = BeautifulSoup(html, "lxml")

    for tag_name in NOISE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else url

    description = ""
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        description = meta_desc["content"].strip()

    # Prefer <article> or <main> if present -- usually the real content.
    main_container = soup.find("article") or soup.find("main") or soup.body or soup

    paragraphs = [p.get_text(" ", strip=True) for p in main_container.find_all(["p", "li", "h1", "h2", "h3"])]
    paragraphs = [p for p in paragraphs if len(p.split()) > 3]  # drop tiny fragments/menu items

    text = "\n\n".join(paragraphs)

    if not text:
        raise ScrapeError(f"No readable content found at {url}")

    return ScrapedPage(url=url, title=title, description=description, text=text)


def scrape_url(url: str) -> ScrapedPage:
    """Convenience wrapper: fetch + extract in one call."""
    html = fetch_html(url)
    return extract_content(html, url)
# if __name__ == "__main__":
#     page = scrape_url("https://en.wikipedia.org/wiki/Artificial_intelligence")
#     print("TITLE:", page.title)
#     print("DESCRIPTION:", page.description)
#     print("TEXT PREVIEW:", page.text[:500])