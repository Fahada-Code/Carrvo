"""
Standalone Ashby ATS automation script.

Usage:
    python scripts/ashby.py --url <url> --resume <path> --cover-letter <path> --profile <json>
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

        # Navigate to apply form if needed
        apply_btn = page.locator("button:has-text('Apply'), a:has-text('Apply Now')").first
        if await apply_btn.count():
            await apply_btn.click()
            await page.wait_for_load_state("networkidle", timeout=10_000)

        if await page.locator(".h-captcha, iframe[src*='recaptcha']").count():
            raise CaptchaEncountered("CAPTCHA on Ashby form.")

        async def fill_by_label(label_text: str, key: str, required: bool = False) -> None:
            value = profile.get(key, "")
            if required and not value:
                raise MissingProfileField(key)
            if not value:
                return
            label = page.locator(f"label:has-text('{label_text}')").first
            if not await label.count():
                return
            for_attr = await label.get_attribute("for")
            if for_attr:
                await page.fill(f"#{for_attr}", str(value))
            else:
                inp = label.locator("..").locator("input, textarea").first
                if await inp.count():
                    await inp.fill(str(value))

        await fill_by_label("First name", "first_name", required=True)
        await fill_by_label("Last name", "last_name", required=True)
        await fill_by_label("Email", "email", required=True)
        await fill_by_label("Phone", "phone")
        await fill_by_label("LinkedIn", "linkedin_url")

        # Resume
        resume_input = page.locator("input[type='file']").first
        if await resume_input.count():
            await resume_input.set_input_files(str(resume_path))

        submit_btn = page.locator("button[type='submit']:has-text('Submit'), button:has-text('Apply')").last
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
