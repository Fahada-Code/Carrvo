"""Greenhouse scraper.

Strategy:
  1. Extract company board token and job ID from the URL.
  2. Hit the public Greenhouse boards JSON API (no auth required).
  3. Fall back to Playwright if the API returns a non-200 or the URL is embedded.
"""

from __future__ import annotations

import re

import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper, JobDescription, ScraperError, html_to_text

_BOARDS_URL_RE = re.compile(
    r"boards\.greenhouse\.io/(?P<company>[^/]+)/jobs/(?P<job_id>\d+)", re.IGNORECASE
)
_API_BASE = "https://boards-api.greenhouse.io/v1/boards"


class GreenhouseScraper(BaseScraper):
    async def scrape(self, url: str) -> JobDescription:
        m = _BOARDS_URL_RE.search(url)
        if m:
            return await self._scrape_via_api(m.group("company"), m.group("job_id"), url)
        # Embedded Greenhouse iframe — fall back to generic Playwright extraction
        return await self._scrape_via_playwright(url)

    async def _scrape_via_api(self, company: str, job_id: str, source_url: str) -> JobDescription:
        api_url = f"{_API_BASE}/{company}/jobs/{job_id}"
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(api_url, headers={"User-Agent": "Carrvo/1.0"})

        if resp.status_code != 200:
            raise ScraperError(
                f"Greenhouse API returned {resp.status_code} for {company}/{job_id}. "
                "Try pasting the direct job listing URL."
            )

        data = resp.json()
        content_html: str = data.get("content", "")
        soup = BeautifulSoup(content_html, "lxml")

        # Greenhouse puts requirements in <li> under an h2/h3 labelled "Requirements"
        requirements: list[str] = []
        for heading in soup.find_all(re.compile(r"^h[2-4]$")):
            if "requirement" in heading.get_text().lower():
                sib = heading.find_next_sibling("ul")
                if sib:
                    requirements = [li.get_text(strip=True) for li in sib.find_all("li")]
                break

        return JobDescription(
            title=data.get("title", ""),
            company=data.get("company", {}).get("name", company),
            location=data.get("location", {}).get("name", ""),
            description_html=content_html,
            description_text=html_to_text(content_html),
            requirements=requirements,
            portal="greenhouse",
            source_url=source_url,
        )

    async def _scrape_via_playwright(self, url: str) -> JobDescription:
        from playwright.async_api import async_playwright

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30_000)

            title = await page.title()
            content_html = await page.inner_html("#content") or await page.inner_html("body")
            await browser.close()

        soup = BeautifulSoup(content_html, "lxml")
        company = soup.select_one(".company-name, [class*='company']")

        return JobDescription(
            title=title,
            company=company.get_text(strip=True) if company else "",
            location="",
            description_html=content_html,
            description_text=html_to_text(content_html),
            portal="greenhouse",
            source_url=url,
        )
