"""Lever scraper.

Strategy:
  1. Extract company and posting ID from the URL.
  2. Use the public Lever postings API (no auth required).
  3. Fall back to Playwright if the API fails.
"""

from __future__ import annotations

import re

import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper, JobDescription, ScraperError, html_to_text

_URL_RE = re.compile(
    r"jobs\.lever\.co/(?P<company>[^/]+)/(?P<posting_id>[a-f0-9-]+)", re.IGNORECASE
)
_API_BASE = "https://api.lever.co/v0/postings"


class LeverScraper(BaseScraper):
    async def scrape(self, url: str) -> JobDescription:
        m = _URL_RE.search(url)
        if not m:
            return await self._scrape_via_playwright(url)
        return await self._scrape_via_api(m.group("company"), m.group("posting_id"), url)

    async def _scrape_via_api(self, company: str, posting_id: str, source_url: str) -> JobDescription:
        api_url = f"{_API_BASE}/{company}/{posting_id}"
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(api_url, headers={"User-Agent": "Carrvo/1.0"})

        if resp.status_code != 200:
            raise ScraperError(
                f"Lever API returned {resp.status_code} for {company}/{posting_id}."
            )

        data = resp.json()

        # Lever `lists` is an array of {text: "Requirements", content: "<ul>..."}
        requirements: list[str] = []
        nice_to_haves: list[str] = []

        for lst in data.get("lists", []):
            label = lst.get("text", "").lower()
            soup = BeautifulSoup(lst.get("content", ""), "lxml")
            items = [li.get_text(strip=True) for li in soup.find_all("li")]
            if "requirement" in label or "qualif" in label:
                requirements.extend(items)
            elif "nice" in label or "bonus" in label or "preferred" in label:
                nice_to_haves.extend(items)

        description_html = data.get("description", "")
        additional = data.get("additionalPlain", "")
        full_description = description_html
        if additional:
            full_description += f"\n{additional}"

        return JobDescription(
            title=data.get("text", ""),
            company=company,
            location=data.get("categories", {}).get("location", ""),
            description_html=full_description,
            description_text=html_to_text(full_description),
            requirements=requirements,
            nice_to_haves=nice_to_haves,
            portal="lever",
            source_url=source_url,
        )

    async def _scrape_via_playwright(self, url: str) -> JobDescription:
        from playwright.async_api import async_playwright

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30_000)

            title = (await page.locator(".posting-headline h2").text_content() or "").strip()
            location = (await page.locator(".sort-by-location").text_content() or "").strip()
            content_html = await page.inner_html(".posting-description") or await page.inner_html("body")
            await browser.close()

        return JobDescription(
            title=title,
            company="",
            location=location,
            description_html=content_html,
            description_text=html_to_text(content_html),
            portal="lever",
            source_url=url,
        )
