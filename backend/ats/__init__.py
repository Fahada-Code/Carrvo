"""Factory: get_ats(portal) -> BaseATS."""

from __future__ import annotations

from .ashby import AshbyATS
from .base import BaseATS, ATSError, CaptchaEncountered, MissingProfileField, SubmissionResult
from .greenhouse import GreenhouseATS
from .lever import LeverATS
from .workday import WorkdayATS

__all__ = [
    "get_ats",
    "BaseATS",
    "ATSError",
    "CaptchaEncountered",
    "MissingProfileField",
    "SubmissionResult",
]

_PORTAL_MAP: dict[str, type[BaseATS]] = {
    "greenhouse": GreenhouseATS,
    "lever": LeverATS,
    "ashby": AshbyATS,
    "workday": WorkdayATS,
}


def get_ats(portal: str) -> BaseATS:
    """Return the ATS script for the given portal name. Raises KeyError if unsupported."""
    cls = _PORTAL_MAP.get(portal)
    if not cls:
        raise KeyError(
            f"No ATS script for portal '{portal}'. "
            f"Supported: {', '.join(_PORTAL_MAP)}"
        )
    return cls()
