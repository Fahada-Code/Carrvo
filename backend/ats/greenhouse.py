"""Greenhouse ATS form-filling script.

Greenhouse's application form is rendered at:
  boards.greenhouse.io/{company}/jobs/{id}/apply

Field map (stable across companies):
  - #first_name, #last_name, #email, #phone
  - #job_application_resume (file upload)
  - #job_application_cover_letter (file upload, if present)
  - .custom-question textarea / input (open-ended questions)
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path

from config import settings
from .base import BaseATS, CaptchaEncountered, MissingProfileField, SubmissionResult


class GreenhouseATS(BaseATS):
    async def fill_and_submit(
        self,
        job_url: str,
        resume_pdf: Path,
        cover_letter_pdf: Path,
        profile: dict,
    ) -> SubmissionResult:
        apply_url = self._to_apply_url(job_url)

        pw, browser, page = await self._get_authenticated_page(
            settings.browser_ws_endpoint or None
        )

        try:
            await page.goto(apply_url, wait_until="networkidle", timeout=30_000)

            # Detect CAPTCHA
            if await page.locator("iframe[src*='recaptcha']").count():
                raise CaptchaEncountered(
                    "Greenhouse is showing a reCAPTCHA. Please complete it in your browser."
                )

            # Fill personal info
            for field, key in [
                ("#first_name", "first_name"),
                ("#last_name", "last_name"),
                ("#email", "email"),
                ("#phone", "phone"),
            ]:
                if await page.locator(field).count():
                    value = profile.get(key)
                    if not value:
                        raise MissingProfileField(key)
                    await page.fill(field, str(value))

            # Upload resume
            resume_input = page.locator("#job_application_resume, input[type='file'][name*='resume']").first
            if await resume_input.count():
                await resume_input.set_input_files(str(resume_pdf))

            # Upload cover letter (optional field)
            cl_input = page.locator(
                "#job_application_cover_letter, input[type='file'][name*='cover']"
            ).first
            if await cl_input.count():
                await cl_input.set_input_files(str(cover_letter_pdf))

            # LinkedIn URL (optional)
            linkedin = page.locator("input[name*='linkedin'], input[id*='linkedin']").first
            if await linkedin.count() and profile.get("linkedin_url"):
                await linkedin.fill(profile["linkedin_url"])

            # Website/portfolio (optional)
            website = page.locator("input[name*='website'], input[name*='portfolio']").first
            if await website.count() and profile.get("website_url"):
                await website.fill(profile.get("website_url", ""))

            # Work authorisation dropdowns (best-effort)
            await self._handle_work_auth(page, profile)

            # Pause — caller must call confirm() separately
            # We return the page URL as the confirmation URL after actual submit
            confirmation_url = page.url

            # Actual submit
            submit_btn = page.locator("input[type='submit'], button[type='submit']").last
            await submit_btn.click()
            await page.wait_for_load_state("networkidle", timeout=15_000)

            return SubmissionResult(success=True, confirmation_url=page.url)

        except (CaptchaEncountered, MissingProfileField):
            raise
        except Exception as exc:
            return SubmissionResult(success=False, error=str(exc))
        finally:
            await browser.close()
            await pw.stop()

    @staticmethod
    def _to_apply_url(job_url: str) -> str:
        """Convert a job listing URL to its /apply equivalent."""
        if "/apply" not in job_url:
            return job_url.rstrip("/") + "/apply"
        return job_url

    @staticmethod
    async def _handle_work_auth(page, profile: dict) -> None:
        """Fill work-authorisation dropdowns using profile defaults."""
        auth_value = profile.get("work_authorization", "")
        if not auth_value:
            return
        for sel in page.locator("select[name*='work_auth'], select[id*='work_auth']").all():
            try:
                await sel.select_option(label=auth_value)
            except Exception:
                pass
