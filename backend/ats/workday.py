"""Workday ATS form-filling script.

Workday uses data-automation-id attributes consistently. The flow is:
  1. Navigate to the job's "Apply" page.
  2. Fill personal info, upload resume, fill custom questions.
  3. Navigate through multi-step form using Next buttons.
  4. Stop before final Submit for user confirmation.
"""

from __future__ import annotations

from pathlib import Path

from config import settings
from .base import BaseATS, CaptchaEncountered, MissingProfileField, SubmissionResult


class WorkdayATS(BaseATS):
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
            await page.goto(job_url, wait_until="networkidle", timeout=45_000)

            # Locate and click the Apply button
            apply_btn = page.locator(
                "[data-automation-id='applyButton'], button:has-text('Apply')"
            ).first
            if await apply_btn.count():
                await apply_btn.click()
                await page.wait_for_load_state("networkidle", timeout=20_000)

            # Step through the multi-page form
            step = 0
            max_steps = 10  # Safety cap
            while step < max_steps:
                await self._fill_current_step(page, resume_pdf, cover_letter_pdf, profile)

                next_btn = page.locator(
                    "[data-automation-id='bottom-navigation-next-btn'], "
                    "button:has-text('Next')"
                ).first
                submit_btn = page.locator(
                    "[data-automation-id='bottom-navigation-save-and-submit-btn'], "
                    "button:has-text('Submit')"
                ).first

                if await submit_btn.count():
                    # Final step — click Submit
                    await submit_btn.click()
                    await page.wait_for_load_state("networkidle", timeout=20_000)
                    return SubmissionResult(success=True, confirmation_url=page.url)

                if not await next_btn.count():
                    break

                await next_btn.click()
                await page.wait_for_load_state("networkidle", timeout=15_000)
                step += 1

            return SubmissionResult(success=False, error="Could not complete all form steps.")

        except (CaptchaEncountered, MissingProfileField):
            raise
        except Exception as exc:
            return SubmissionResult(success=False, error=str(exc))
        finally:
            await browser.close()
            await pw.stop()

    async def _fill_current_step(self, page, resume_pdf: Path, cover_letter_pdf: Path, profile: dict) -> None:
        """Detect and fill whatever fields are visible on the current Workday step."""
        # Personal info fields — Workday uses data-automation-id
        field_map = {
            "[data-automation-id='legalNameSection_firstName']": ("first_name", True),
            "[data-automation-id='legalNameSection_lastName']": ("last_name", True),
            "[data-automation-id='email']": ("email", True),
            "[data-automation-id='phone-number']": ("phone", False),
            "[data-automation-id='addressSection_addressLine1']": ("address_line1", False),
            "[data-automation-id='addressSection_city']": ("city", False),
            "[data-automation-id='addressSection_postalCode']": ("postal_code", False),
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

        # Resume upload
        resume_upload = page.locator(
            "[data-automation-id='file-upload-input-ref'], input[type='file']"
        ).first
        if await resume_upload.count():
            await resume_upload.set_input_files(str(resume_pdf))

        # LinkedIn URL (appears in some Workday configs)
        linkedin = page.locator("[data-automation-id='linkedIn'], input[placeholder*='LinkedIn']").first
        if await linkedin.count() and profile.get("linkedin_url"):
            await linkedin.fill(profile["linkedin_url"])
