"""
Standalone job description scraper.

Usage:
    python scripts/scraper.py <job-url>
    python scripts/scraper.py <job-url> --output job.txt

Outputs the extracted plain-text job description to stdout or a file.
Supports Greenhouse (API), Lever (API), Ashby (__NEXT_DATA__), Workday (Playwright),
and any generic job page (Playwright + heuristic extraction).
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path

import httpx
from bs4 import BeautifulSoup


# ── Portal detection ──────────────────────────────────────────────────────────

def detect_portal(url: str) -> str:
    patterns = [
        (r"greenhouse\.io", "greenhouse"),
        (r"lever\.co", "lever"),
        (r"ashby\.io", "ashby"),
        (r"myworkdayjobs\.com|workday\.com", "workday"),
    ]
    for pat, name in patterns:
        if re.search(pat, url, re.I):
            return name
    return "generic"


# ── Greenhouse ────────────────────────────────────────────────────────────────

async def scrape_greenhouse(url: str) -> dict:
    m = re.search(r"boards\.greenhouse\.io/(?P<co>[^/]+)/jobs/(?P<id>\d+)", url, re.I)
    if not m:
        return await scrape_generic(url)

    api_url = f"https://boards-api.greenhouse.io/v1/boards/{m['co']}/jobs/{m['id']}"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(api_url)
    if resp.status_code != 200:
        return await scrape_generic(url)

    data = resp.json()
    html = data.get("content", "")
    return {
        "title": data.get("title", ""),
        "company": (data.get("company") or {}).get("name", m["co"]),
        "location": (data.get("location") or {}).get("name", ""),
        "portal": "greenhouse",
        "text": _html_to_text(html),
        "url": url,
    }


# ── Lever ─────────────────────────────────────────────────────────────────────

async def scrape_lever(url: str) -> dict:
    m = re.search(r"jobs\.lever\.co/(?P<co>[^/]+)/(?P<id>[a-f0-9-]+)", url, re.I)
    if not m:
        return await scrape_generic(url)

    api_url = f"https://api.lever.co/v0/postings/{m['co']}/{m['id']}"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(api_url)
    if resp.status_code != 200:
        return await scrape_generic(url)

    data = resp.json()
    desc_html = data.get("description", "") + "\n".join(
        lst.get("content", "") for lst in data.get("lists", [])
    )
    return {
        "title": data.get("text", ""),
        "company": m["co"],
        "location": (data.get("categories") or {}).get("location", ""),
        "portal": "lever",
        "text": _html_to_text(desc_html),
        "url": url,
    }


# ── Ashby ─────────────────────────────────────────────────────────────────────

async def scrape_ashby(url: str) -> dict:
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
    if resp.status_code != 200:
        return await scrape_generic(url)

    soup = BeautifulSoup(resp.text, "lxml")
    tag = soup.find("script", {"id": "__NEXT_DATA__"})
    if not tag or not tag.string:
        return await scrape_generic(url)

    try:
        data = json.loads(tag.string)
        props = data["props"]["pageProps"]
        job = props.get("jobPosting") or props.get("job") or props
        desc_html = job.get("descriptionHtml") or job.get("description") or ""
        return {
            "title": job.get("title") or job.get("jobTitle") or "",
            "company": (job.get("organization") or {}).get("name") or "",
            "location": (job.get("location") or {}).get("locationStr") or "",
            "portal": "ashby",
            "text": _html_to_text(desc_html),
            "url": url,
        }
    except (KeyError, TypeError, json.JSONDecodeError):
        return await scrape_generic(url)


# ── Workday ───────────────────────────────────────────────────────────────────

async def scrape_workday(url: str) -> dict:
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle", timeout=45_000)
        await page.wait_for_selector(
            "[data-automation-id='jobPostingDescription']", timeout=15_000
        )
        title = (await page.locator("[data-automation-id='jobTitle']").first.text_content() or "").strip()
        desc_el = page.locator("[data-automation-id='jobPostingDescription']").first
        desc_html = await desc_el.inner_html()
        await browser.close()

    return {
        "title": title,
        "company": re.search(r"([^.]+)\.myworkdayjobs", url, re.I).group(1) if re.search(r"myworkdayjobs", url, re.I) else "",
        "location": "",
        "portal": "workday",
        "text": _html_to_text(desc_html),
        "url": url,
    }


# ── Generic ───────────────────────────────────────────────────────────────────

async def scrape_generic(url: str) -> dict:
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        await page.wait_for_timeout(2_000)
        html = await page.content()
        title = await page.title()
        await browser.close()

    soup = BeautifulSoup(html, "lxml")
    for tag in soup.find_all(["script", "style", "nav", "header", "footer"]):
        tag.decompose()

    selectors = ["[class*='description']", "[id*='description']", "article", "main"]
    for sel in selectors:
        el = soup.select_one(sel)
        if el and len(el.get_text(strip=True)) > 200:
            return {"title": title, "company": "", "location": "", "portal": "generic",
                    "text": _html_to_text(str(el)), "url": url}

    return {"title": title, "company": "", "location": "", "portal": "generic",
            "text": soup.get_text(separator="\n").strip(), "url": url}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(separator="\n")
    return re.sub(r"\n{3,}", "\n\n", text).strip()


async def scrape(url: str) -> dict:
    portal = detect_portal(url)
    dispatch = {
        "greenhouse": scrape_greenhouse,
        "lever": scrape_lever,
        "ashby": scrape_ashby,
        "workday": scrape_workday,
        "generic": scrape_generic,
    }
    return await dispatch[portal](url)


# ── CLI entry point ───────────────────────────────────────────────────────────

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Scrape a job listing.")
    parser.add_argument("url", help="Job listing URL")
    parser.add_argument("--output", "-o", help="Write output to file instead of stdout")
    parser.add_argument("--json", action="store_true", help="Output full JSON (not just text)")
    args = parser.parse_args()

    result = asyncio.run(scrape(args.url))

    if args.json:
        output = json.dumps(result, indent=2)
    else:
        lines = [
            f"Title:    {result['title']}",
            f"Company:  {result['company']}",
            f"Location: {result['location']}",
            f"Portal:   {result['portal']}",
            "",
            result["text"],
        ]
        output = "\n".join(lines)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Saved to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
