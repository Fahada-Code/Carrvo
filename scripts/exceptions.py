class ScraperError(Exception):
    """Raised when a scraper cannot extract a usable job description."""


class CaptchaEncountered(Exception):
    """Raised when a CAPTCHA is detected on an ATS form."""


class MissingProfileField(Exception):
    """Raised when a required field is absent from the user profile."""
    def __init__(self, field: str):
        super().__init__(f"Missing required profile field: '{field}'")
        self.field = field
