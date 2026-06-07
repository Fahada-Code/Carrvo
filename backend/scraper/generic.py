"""Generic fallback scraper.

Used when the ATS portal is unknown or unrecognised. Launches a headless browser,
loads the page, and extracts the largest coherent block of text — which is almost
always the job description on any well-structured job board.
"""

from __future__ import annotations

from bs4 import BeautifulSoup, Tag

from .base import BaseScraper, JobDescription, ScraperError, html_to_text

# Tags that commonly contain job descriptions, in preference order
_CANDIDATE_SELECTORS = [
    "[class*='job-description']",
    "[class*='description']",
    "[id*='description']",
    "[class*='posting']",
    "article",
    "main",
    ".content",
    "#content",
]


class GenericScraper(BaseScraper):
    async def scrape(self, url: str) -> JobDescription:
        from playwright.async_api import async_playwright, TimeoutError as PWTimeout

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=30_000,
                )
                # Give JS frameworks a moment to hydrate
                await page.wait_for_timeout(2_500)
            except PWTimeout:
                raise ScraperError(f"Page timed out: {url}")

            title = (await page.title()).strip()
            page_html = await page.content()
            await browser.close()

        soup = BeautifulSoup(page_html, "lxml")

        # Remove noise
        for tag in soup.find_all(["script", "style", "nav", "header", "footer"]):
            tag.decompose()

        description_el: Tag | None = None
        for sel in _CANDIDATE_SELECTORS:
            el = soup.select_one(sel)
            if el and len(el.get_text(strip=True)) > 200:
                description_el = el
                break

        # If no candidate matched, fall back to the longest div
        if not description_el:
            best, best_len = None, 0
            for div in soup.find_all("div"):
                length = len(div.get_text(strip=True))
                if length > best_len:
                    best, best_len = div, length
            description_el = best

        if not description_el or len(description_el.get_text(strip=True)) < 100:
            raise ScraperError(
                "Could not extract a job description from this page. "
                "The content may require login or a non-standard page structure."
            )

        description_html = str(description_el)
        description_text = html_to_text(description_html)

        # Best-effort title and company extraction
        h1 = soup.find("h1")
        detected_title = h1.get_text(strip=True) if h1 else title

        return JobDescription(
            title=detected_title,
            company="",
            location="",
            description_html=description_html,
            description_text=description_text,
            portal="unknown",
            source_url=url,
        )
