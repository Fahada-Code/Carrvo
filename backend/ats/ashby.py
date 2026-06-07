"""Ashby ATS form-filling script.

Ashby renders a React application form. Fields are identified by labels rather
than stable IDs, so we use label-to-input association via aria-labelledby / for.
"""

from __future__ import annotations

from pathlib import Path

from config import settings
from .base import BaseATS, CaptchaEncountered, MissingProfileField, SubmissionResult


class AshbyATS(BaseATS):
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

            # Click "Apply" if it's a job detail page (not already the form)
            apply_btn = page.locator("button:has-text('Apply'), a:has-text('Apply Now')").first
            if await apply_btn.count():
                await apply_btn.click()
                await page.wait_for_load_state("networkidle", timeout=10_000)

            if await page.locator(".h-captcha, iframe[src*='recaptcha']").count():
                raise CaptchaEncountered("CAPTCHA on Ashby form.")

            # Fill fields by visible label text
            await self._fill_by_label(page, "First name", "first_name", profile, required=True)
            await self._fill_by_label(page, "Last name", "last_name", profile, required=True)
            await self._fill_by_label(page, "Email", "email", profile, required=True)
            await self._fill_by_label(page, "Phone", "phone", profile)
            await self._fill_by_label(page, "LinkedIn", "linkedin_url", profile)
            await self._fill_by_label(page, "Website", "website_url", profile)

            # Resume upload
            resume_input = page.locator("input[type='file'][accept*='pdf'], input[type='file']").first
            if await resume_input.count():
                await resume_input.set_input_files(str(resume_pdf))

            # Cover letter (Ashby sometimes has a dedicated upload, sometimes a textarea)
            cl_file = page.locator("input[type='file'][accept*='pdf']").nth(1)
            if await cl_file.count():
                await cl_file.set_input_files(str(cover_letter_pdf))

            # Submit
            submit_btn = page.locator("button[type='submit']:has-text('Submit'), button:has-text('Apply')").last
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
    async def _fill_by_label(page, label_text: str, profile_key: str, profile: dict, required: bool = False) -> None:
        value = profile.get(profile_key, "")
        if required and not value:
            raise MissingProfileField(profile_key)
        if not value:
            return

        label = page.locator(f"label:has-text('{label_text}')").first
        if not await label.count():
            return

        for_attr = await label.get_attribute("for")
        if for_attr:
            await page.fill(f"#{for_attr}", str(value))
        else:
            # Fallback: find the adjacent input
            parent = label.locator("..")
            inp = parent.locator("input, textarea").first
            if await inp.count():
                await inp.fill(str(value))
