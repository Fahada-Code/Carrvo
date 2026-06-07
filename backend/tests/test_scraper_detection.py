"""Tests for portal detection and the scraper factory."""

from scraper import get_scraper
from scraper.ashby import AshbyScraper
from scraper.generic import GenericScraper
from scraper.greenhouse import GreenhouseScraper
from scraper.lever import LeverScraper
from scraper.workday import WorkdayScraper


class TestScraperFactory:
    def test_greenhouse_url(self):
        assert isinstance(get_scraper("https://boards.greenhouse.io/co/jobs/1"), GreenhouseScraper)

    def test_lever_url(self):
        assert isinstance(get_scraper("https://jobs.lever.co/co/abc-123"), LeverScraper)

    def test_ashby_url(self):
        assert isinstance(get_scraper("https://jobs.ashby.io/co/xyz"), AshbyScraper)

    def test_workday_url(self):
        assert isinstance(
            get_scraper("https://acme.wd1.myworkdayjobs.com/job/123"), WorkdayScraper
        )

    def test_unknown_url_falls_back_to_generic(self):
        assert isinstance(get_scraper("https://careers.example.com/job/1"), GenericScraper)

    def test_case_insensitive(self):
        assert isinstance(get_scraper("https://BOARDS.GREENHOUSE.IO/co/jobs/1"), GreenhouseScraper)
