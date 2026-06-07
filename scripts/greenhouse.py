"""
Standalone Greenhouse ATS automation script.

Usage (called by carrvo CLI or backend):
    from scripts.greenhouse import apply
    result = asyncio.run(apply(resume_path, coverletter_path, profile, job_url))

Or directly:
    python scripts/greenhouse.py --url <url> --resume <path> --cover-letter <path> --profile <json>
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path

from exceptions import CaptchaEncountered, MissingProfileField


async def apply(
    resume_path: Path,
    coverletter_path: Path,
    profile: dict,
    job_url: str,
) -> dict:
    """
    Returns:
        {"success": bool, "confirmation_url": str, "error": str | None}
    """
    from playwright.async_api import async_playwright

    apply_url = _to_apply_url(job_url)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(apply_url, wait_until="networkidle", timeout=30_000)

        if await page.locator("iframe[src*='recaptcha']").count():
            raise CaptchaEncountered("reCAPTCHA on Greenhouse form — complete it in your browser.")

        # Personal info
        for selector, key, required in [
            ("#first_name", "first_name", True),
            ("#last_name", "last_name", True),
            ("#email", "email", True),
            ("#phone", "phone", False),
        ]:
            if await page.locator(selector).count():
                value = profile.get(key, "")
                if required and not value:
                    raise MissingProfileField(key)
                if value:
                    await page.fill(selector, str(value))

        # Resume
        resume_input = page.locator("#job_application_resume, input[type='file'][name*='resume']").first
        if await resume_input.count():
            await resume_input.set_input_files(str(resume_path))

        # Cover letter (optional)
        cl_input = page.locator(
            "#job_application_cover_letter, input[type='file'][name*='cover']"
        ).first
        if await cl_input.count():
            await cl_input.set_input_files(str(coverletter_path))

        # LinkedIn (optional)
        linkedin = page.locator("input[name*='linkedin']").first
        if await linkedin.count() and profile.get("linkedin_url"):
            await linkedin.fill(profile["linkedin_url"])

        submit_btn = page.locator("input[type='submit'], button[type='submit']").last
        await submit_btn.click()
        await page.wait_for_load_state("networkidle", timeout=15_000)
        confirmation_url = page.url
        await browser.close()

    return {"success": True, "confirmation_url": confirmation_url, "error": None}


def _to_apply_url(url: str) -> str:
    return url.rstrip("/") + "/apply" if "/apply" not in url else url


def _main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--resume", required=True, type=Path)
    parser.add_argument("--cover-letter", required=True, type=Path)
    parser.add_argument("--profile", required=True, help="JSON string or path to profile JSON")
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
