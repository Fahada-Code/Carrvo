"""
Standalone Lever ATS automation script.

Usage:
    python scripts/lever.py --url <url> --resume <path> --cover-letter <path> --profile <json>
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from exceptions import CaptchaEncountered, MissingProfileField


async def apply(
    resume_path: Path,
    coverletter_path: Path,
    profile: dict,
    job_url: str,
) -> dict:
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(job_url, wait_until="networkidle", timeout=30_000)

        # Click the Apply button to open the form
        apply_btn = page.locator("a[href*='/apply'], .postings-btn, button:has-text('Apply')").first
        if await apply_btn.count():
            await apply_btn.click()
            await page.wait_for_selector(".application-form, form", timeout=8_000)

        if await page.locator("iframe[src*='recaptcha'], .h-captcha").count():
            raise CaptchaEncountered("CAPTCHA on Lever form.")

        for field_id, key, required in [
            ("#name", "full_name", True),
            ("#email", "email", True),
            ("#phone", "phone", False),
            ("#org", "current_company", False),
        ]:
            el = page.locator(field_id).first
            if await el.count():
                value = profile.get(key, "")
                if required and not value:
                    raise MissingProfileField(key)
                if value:
                    await el.fill(str(value))

        # Resume
        resume_input = page.locator("input[type='file']").first
        if await resume_input.count():
            await resume_input.set_input_files(str(resume_path))

        # LinkedIn
        linkedin = page.locator("input[placeholder*='linkedin'], input[name*='linkedin']").first
        if await linkedin.count() and profile.get("linkedin_url"):
            await linkedin.fill(profile["linkedin_url"])

        submit_btn = page.locator("button[type='submit'], input[type='submit']").last
        await submit_btn.click()
        await page.wait_for_load_state("networkidle", timeout=15_000)
        confirmation_url = page.url
        await browser.close()

    return {"success": True, "confirmation_url": confirmation_url, "error": None}


def _main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--resume", required=True, type=Path)
    parser.add_argument("--cover-letter", required=True, type=Path)
    parser.add_argument("--profile", required=True)
    args = parser.parse_args()

    profile_raw = args.profile
    if Path(profile_raw).exists():
        profile = json.loads(Path(profile_raw).read_text())
    else:
        profile = json.loads(profile_raw)

    result = asyncio.run(apply(args.resume, args.cover_letter, profile, args.url))
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    _main()
