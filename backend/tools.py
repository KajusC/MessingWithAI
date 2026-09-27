from datetime import date

from ddgs import DDGS
from langchain.tools import tool
from playwright.sync_api import sync_playwright

from database import database

latest_results: list[dict[str, str]] = []


@tool
def current_date() -> str:
    """Return today's date. Use this for any question about the current date."""
    return date.today().isoformat()


@tool
def search_database(query: str) -> list[dict[str, str]]:
    """Search pages already stored in the database. Call this before the web."""
    return database.search(query)


# DuckDuckGo search engine
@tool
def web_search(query: str) -> list[dict[str, str]]:
    """Search the web when the database does not answer the question."""
    print("Web searching for: ", query)
    global latest_results
    answer = DDGS().text(query, max_results=5)
    latest_results = answer
    return answer


@tool
def scrape_website(url: str) -> str:
    """Open one page and return its HTML when a search snippet is too short."""
    print("Scraping website: ", url)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        return page.content()


@tool
def save_search_results() -> str:
    """Save every page from the latest web_search. Call this right after web_search. It takes no arguments."""
    if not latest_results:
        return "No search results to save. Call web_search first."
    for item in latest_results:
        database.insert_page(
            label=item.get("title") or item["href"],
            url=item["href"],
            description=item.get("body") or "",
            tags=[],
            document_date=date.today(),
        )
    return f"Saved {len(latest_results)} pages."
