"""
Standalone Workday ATS automation script.

Usage:
    python scripts/workday.py --url <url> --resume <path> --cover-letter <path> --profile <json>
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
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()
        await page.goto(job_url, wait_until="networkidle", timeout=45_000)

        # Click Apply
        apply_btn = page.locator("[data-automation-id='applyButton'], button:has-text('Apply')").first
        if await apply_btn.count():
            await apply_btn.click()
            await page.wait_for_load_state("networkidle", timeout=20_000)

        step, max_steps = 0, 10
        while step < max_steps:
            await _fill_step(page, resume_path, profile)

            next_btn = page.locator(
                "[data-automation-id='bottom-navigation-next-btn'], button:has-text('Next')"
            ).first
            submit_btn = page.locator(
                "[data-automation-id='bottom-navigation-save-and-submit-btn'], button:has-text('Submit')"
            ).first

            if await submit_btn.count():
                await submit_btn.click()
                await page.wait_for_load_state("networkidle", timeout=20_000)
                confirmation_url = page.url
                await browser.close()
                return {"success": True, "confirmation_url": confirmation_url, "error": None}

            if not await next_btn.count():
                break

            await next_btn.click()
            await page.wait_for_load_state("networkidle", timeout=15_000)
            step += 1

        await browser.close()
        return {"success": False, "confirmation_url": "", "error": "Could not complete all form steps."}


async def _fill_step(page, resume_path: Path, profile: dict) -> None:
    field_map = {
        "[data-automation-id='legalNameSection_firstName']": ("first_name", True),
        "[data-automation-id='legalNameSection_lastName']": ("last_name", True),
        "[data-automation-id='email']": ("email", True),
        "[data-automation-id='phone-number']": ("phone", False),
    }
    for selector, (key, required) in field_map.items():
        el = page.locator(selector).first
        if not await el.count():
            continue
        value = profile.get(key, "")
        if required and not value:
            raise MissingProfileField(key)
        if value:
            await el.fill(str(value))

    resume_upload = page.locator(
        "[data-automation-id='file-upload-input-ref'], input[type='file']"
    ).first
    if await resume_upload.count():
        await resume_upload.set_input_files(str(resume_path))


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
