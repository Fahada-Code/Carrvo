"""Factory: get_scraper(url) -> BaseScraper."""

from __future__ import annotations

import re

from .ashby import AshbyScraper
from .base import BaseScraper, JobDescription, ScraperError
from .generic import GenericScraper
from .greenhouse import GreenhouseScraper
from .lever import LeverScraper
from .workday import WorkdayScraper

__all__ = ["get_scraper", "BaseScraper", "JobDescription", "ScraperError"]

_PORTAL_MAP: list[tuple[re.Pattern[str], type[BaseScraper]]] = [
    (re.compile(r"greenhouse\.io", re.I), GreenhouseScraper),
    (re.compile(r"lever\.co", re.I), LeverScraper),
    (re.compile(r"ashby\.io", re.I), AshbyScraper),
    (re.compile(r"myworkdayjobs\.com|workday\.com", re.I), WorkdayScraper),
]


def get_scraper(url: str) -> BaseScraper:
    """Return the most specific scraper for the given URL."""
    for pattern, scraper_cls in _PORTAL_MAP:
        if pattern.search(url):
            return scraper_cls()
    return GenericScraper()
