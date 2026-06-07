"""Lever ATS form-filling script.

Lever's apply form is at the same URL as the job posting — clicking "Apply" opens
a slide-in panel. Lever uses consistent field IDs across all companies.
"""

from __future__ import annotations

from pathlib import Path

from config import settings
from .base import BaseATS, CaptchaEncountered, MissingProfileField, SubmissionResult


class LeverATS(BaseATS):
    async def fill_and_submit(
        self,
        job_url: str,
        resume_pdf: Path,
        cover_letter_pdf: Path,
        profile: dict,
    ) -> SubmissionResult:
        pw, browser, page = await self._get_authenticated_page(
            settings.browser_ws_endpoint or None
        )

        try:
            await page.goto(job_url, wait_until="networkidle", timeout=30_000)

            # Open application panel
            apply_btn = page.locator("a[href*='/apply'], .postings-btn").first
            if await apply_btn.count():
                await apply_btn.click()
                await page.wait_for_selector(".application-form, form[data-lever-source]", timeout=8_000)

            if await page.locator("iframe[src*='recaptcha'], .h-captcha").count():
                raise CaptchaEncountered("CAPTCHA detected on Lever form.")

            # Personal info
            for field_id, profile_key in [
                ("#name", "full_name"),
                ("#email", "email"),
                ("#phone", "phone"),
                ("#org", "current_company"),
            ]:
                el = page.locator(field_id).first
                if await el.count():
                    value = profile.get(profile_key, "")
                    if field_id in ("#name", "#email") and not value:
                        raise MissingProfileField(profile_key)
                    if value:
                        await el.fill(str(value))

            # Resume upload
            resume_input = page.locator("input[type='file'][name*='resume'], input[type='file']").first
            if await resume_input.count():
                await resume_input.set_input_files(str(resume_pdf))

            # Cover letter upload (Lever shows this as a separate file input or textarea)
            cl_file = page.locator("input[type='file'][name*='cover']").first
            if await cl_file.count():
                await cl_file.set_input_files(str(cover_letter_pdf))

            # LinkedIn URL
            linkedin = page.locator("input[placeholder*='linkedin'], input[name*='linkedin']").first
            if await linkedin.count() and profile.get("linkedin_url"):
                await linkedin.fill(profile["linkedin_url"])

            # Submit
            submit_btn = page.locator("button[type='submit'], input[type='submit']").last
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
