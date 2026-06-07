"""Base scraper interface and shared data model."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from bs4 import BeautifulSoup


@dataclass
class JobDescription:
    title: str
    company: str
    location: str
    description_html: str
    description_text: str
    requirements: list[str] = field(default_factory=list)
    nice_to_haves: list[str] = field(default_factory=list)
    application_questions: list[str] = field(default_factory=list)
    portal: str = "unknown"
    source_url: str = ""

    @property
    def word_count(self) -> int:
        return len(self.description_text.split())

    @property
    def full_text(self) -> str:
        """Combined text for AI prompts."""
        parts = [
            f"Job Title: {self.title}",
            f"Company: {self.company}",
            f"Location: {self.location}",
            "",
            self.description_text,
        ]
        if self.requirements:
            parts += ["", "Requirements:"] + [f"- {r}" for r in self.requirements]
        if self.nice_to_haves:
            parts += ["", "Nice to have:"] + [f"- {r}" for r in self.nice_to_haves]
        if self.application_questions:
            parts += ["", "Application questions:"] + [f"- {q}" for q in self.application_questions]
        return "\n".join(parts)


def html_to_text(html: str) -> str:
    """Strip HTML tags and normalise whitespace."""
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(separator="\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_list_items(soup: BeautifulSoup, selector: str) -> list[str]:
    """Pull bullet-point text from a CSS-selected container."""
    container = soup.select_one(selector)
    if not container:
        return []
    return [li.get_text(strip=True) for li in container.find_all("li") if li.get_text(strip=True)]


class BaseScraper(ABC):
    """All scrapers implement this interface."""

    @abstractmethod
    async def scrape(self, url: str) -> JobDescription:
        """Fetch and parse a job listing. Raises ScraperError on failure."""

    @staticmethod
    def _clean_text(text: str) -> str:
        return re.sub(r"[ \t]+", " ", text).strip()


class ScraperError(Exception):
    """Raised when a scraper cannot extract a usable job description."""
