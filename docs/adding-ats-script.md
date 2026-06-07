# Adding an ATS Automation Script

## File location

Place the script at `./scripts/<ats_name>.py`.

## Required interface

Every ATS script must implement this interface:

```python
def apply(
    resume_path: str,
    coverletter_path: str,
    profile: dict,
    job_url: str,
) -> dict:
    """
    Returns:
        {
            "success": bool,
            "confirmation_url": str,   # URL of submitted application, if available
            "error": str | None,       # Error message if success is False
        }
    """
```

## Required behaviour

- Use an existing Playwright browser session — do not create a new browser profile
- Never store or log session cookies, credentials, or form values
- Pause before the final submit click and return control to the caller
- If a CAPTCHA appears, raise `CaptchaEncountered` — do not attempt to solve it
- If a required field is missing from `profile`, raise `MissingProfileField(field_name)`

## Testing requirements

Before submitting a PR:
- Test against at least 3 real job postings on the portal
- Document any fields that required special handling
- Document any bot-detection measures encountered and how they were surfaced to the user

## Example skeleton

```python
# scripts/greenhouse.py
from playwright.sync_api import Page
from .exceptions import CaptchaEncountered, MissingProfileField


def apply(resume_path: str, coverletter_path: str, profile: dict, job_url: str) -> dict:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp("http://localhost:9222")
        page = browser.contexts[0].new_page()

        page.goto(job_url)
        # ... form-filling logic ...

        # Always pause before submit
        return _pause_and_confirm(page, profile)
```

## Naming conventions

| Portal | File name |
|---|---|
| Greenhouse | `greenhouse.py` |
| Workday | `workday.py` |
| Lever | `lever.py` |
| Ashby | `ashby.py` |
| iCIMS | `icims.py` |
| Taleo | `taleo.py` |
| SmartRecruiters | `smartrecruiters.py` |
