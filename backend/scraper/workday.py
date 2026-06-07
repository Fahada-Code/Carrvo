"""Workday scraper.

Workday is the most complex ATS to scrape — it's a heavily React-driven SPA with
no public API. We use Playwright and target specific automation-id attributes that
Workday uses consistently across company instances.
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from .base import BaseScraper, JobDescription, ScraperError, html_to_text

_COMPANY_RE = re.compile(r"(?P<company>[^.]+)\.myworkdayjobs\.com", re.IGNORECASE)


class WorkdayScraper(BaseScraper):
    async def scrape(self, url: str) -> JobDescription:
        from playwright.async_api import async_playwright, TimeoutError as PWTimeout

        m = _COMPANY_RE.search(url)
        company_slug = m.group("company") if m else ""

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )
            page = await context.new_page()

            try:
                await page.goto(url, wait_until="networkidle", timeout=45_000)
                # Wait for the Workday job description container
                await page.wait_for_selector(
                    "[data-automation-id='jobPostingDescription'],"
                    "[data-automation-id='job-posting-detail-description']",
                    timeout=15_000,
                )
            except PWTimeout:
                raise ScraperError(
                    "Workday page timed out. "
                    "Ensure you're logged into the portal in your browser session."
                )

            # Extract title
            title_el = page.locator("[data-automation-id='jobTitle'], h1").first
            title = (await title_el.text_content() or "").strip()

            # Extract location
            loc_el = page.locator("[data-automation-id='locations'], [data-automation-id='location']").first
            location = (await loc_el.text_content() or "").strip()

            # Extract company name
            company_el = page.locator("[data-automation-id='jobPostingHeader'] h2, .css-wlqjmj").first
            company = (await company_el.text_content() or company_slug).strip()

            # Extract job description
            desc_el = page.locator(
                "[data-automation-id='jobPostingDescription'],"
                "[data-automation-id='job-posting-detail-description']"
            ).first
            description_html = await desc_el.inner_html() if await desc_el.count() else ""

            if not description_html:
                raise ScraperError(
                    "Could not find job description on the Workday page. "
                    "The page structure may have changed."
                )

            # Extract any inline questions (Workday sometimes shows them on the detail page)
            questions: list[str] = []
            q_els = page.locator("[data-automation-id='questionnaireQuestion']")
            for i in range(await q_els.count()):
                q_text = (await q_els.nth(i).text_content() or "").strip()
                if q_text:
                    questions.append(q_text)

            await browser.close()

        soup = BeautifulSoup(description_html, "lxml")

        # Workday splits requirements into labelled <ul> sections
        requirements: list[str] = []
        nice_to_haves: list[str] = []
        for ul in soup.find_all("ul"):
            prev = ul.find_previous_sibling()
            label = prev.get_text().lower() if prev else ""
            items = [li.get_text(strip=True) for li in ul.find_all("li")]
            if "required" in label or "must" in label or "qualif" in label:
                requirements.extend(items)
            elif "preferred" in label or "nice" in label or "bonus" in label:
                nice_to_haves.extend(items)

        return JobDescription(
            title=title,
            company=company or company_slug,
            location=location,
            description_html=description_html,
            description_text=html_to_text(description_html),
            requirements=requirements,
            nice_to_haves=nice_to_haves,
            application_questions=questions,
            portal="workday",
            source_url=url,
        )
