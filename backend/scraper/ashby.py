"""Ashby scraper.

Ashby job boards are Next.js apps. Their page HTML contains a <script id="__NEXT_DATA__">
JSON blob with all job data, so we can parse that without executing JavaScript.
Falls back to Playwright if the JSON is absent.
"""

from __future__ import annotations

import json
import re

import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper, JobDescription, ScraperError, html_to_text

_URL_RE = re.compile(r"jobs\.ashby\.io/(?P<company>[^/]+)/(?P<job_id>[^/?#]+)", re.IGNORECASE)


class AshbyScraper(BaseScraper):
    async def scrape(self, url: str) -> JobDescription:
        try:
            return await self._scrape_via_next_data(url)
        except ScraperError:
            return await self._scrape_via_playwright(url)

    async def _scrape_via_next_data(self, url: str) -> JobDescription:
        """Fetch raw HTML, parse the __NEXT_DATA__ JSON blob."""
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    )
                },
            )

        if resp.status_code != 200:
            raise ScraperError(f"HTTP {resp.status_code} for {url}")

        soup = BeautifulSoup(resp.text, "lxml")
        next_data_tag = soup.find("script", {"id": "__NEXT_DATA__"})
        if not next_data_tag or not next_data_tag.string:
            raise ScraperError("No __NEXT_DATA__ found — page may be fully client-rendered")

        next_data = json.loads(next_data_tag.string)

        # Navigate the Next.js page props — Ashby's structure
        try:
            props = next_data["props"]["pageProps"]
            job = props.get("jobPosting") or props.get("job") or props
        except (KeyError, TypeError) as exc:
            raise ScraperError(f"Unexpected __NEXT_DATA__ shape: {exc}") from exc

        title = job.get("title") or job.get("jobTitle") or ""
        company = (
            (job.get("organization") or {}).get("name")
            or next_data.get("props", {}).get("pageProps", {}).get("organizationName")
            or ""
        )
        location = (
            (job.get("location") or {}).get("locationStr")
            or job.get("locationStr")
            or job.get("location")
            or ""
        )
        if isinstance(location, dict):
            location = location.get("locationStr") or ""

        description_html = job.get("descriptionHtml") or job.get("description") or ""
        if not description_html:
            raise ScraperError("Could not find description in __NEXT_DATA__")

        return JobDescription(
            title=title,
            company=company,
            location=location,
            description_html=description_html,
            description_text=html_to_text(description_html),
            portal="ashby",
            source_url=url,
        )

    async def _scrape_via_playwright(self, url: str) -> JobDescription:
        from playwright.async_api import async_playwright

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30_000)

            title = (await page.locator("h1").first.text_content() or "").strip()
            # Ashby renders job description in a div with data-testid or class containing "description"
            desc_el = page.locator("[data-testid='job-description'], .job-description, [class*='description']").first
            content_html = await desc_el.inner_html() if await desc_el.count() else await page.inner_html("main")
            await browser.close()

        return JobDescription(
            title=title,
            company="",
            location="",
            description_html=content_html,
            description_text=html_to_text(content_html),
            portal="ashby",
            source_url=url,
        )
