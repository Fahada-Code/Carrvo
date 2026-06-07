"""Base ATS automation interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SubmissionResult:
    success: bool
    confirmation_url: str = ""
    error: str = ""


class BaseATS(ABC):
    """
    All ATS scripts must implement this interface.
    They receive a Playwright page that is already authenticated (the user logged in manually).
    """

    @abstractmethod
    async def fill_and_submit(
        self,
        job_url: str,
        resume_pdf: Path,
        cover_letter_pdf: Path,
        profile: dict,
    ) -> SubmissionResult:
        """
        Navigate to the job URL, fill all form fields, and submit.
        Must pause before the final submit button click and await caller confirmation.
        Returns SubmissionResult.
        """

    @staticmethod
    async def _get_authenticated_page(ws_endpoint: str | None = None):
        """Return a Playwright page connected to the user's existing browser session."""
        from playwright.async_api import async_playwright

        pw = await async_playwright().start()
        if ws_endpoint:
            browser = await pw.chromium.connect_over_cdp(ws_endpoint)
            context = browser.contexts[0]
        else:
            browser = await pw.chromium.launch(headless=False)
            context = await browser.new_context()

        page = await context.new_page()
        return pw, browser, page


class ATSError(Exception):
    """Raised when an ATS script encounters an unrecoverable error."""


class CaptchaEncountered(ATSError):
    """Raised when a CAPTCHA is detected — surface to user, do not bypass."""


class MissingProfileField(ATSError):
    """Raised when a required field is absent from the user profile."""
    def __init__(self, field: str):
        super().__init__(f"Missing required profile field: {field}")
        self.field = field
