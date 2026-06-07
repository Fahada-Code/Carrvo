"""Tests for storage slug/path safety."""

import pytest

from storage import _slug


class TestSlug:
    def test_basic_lowercasing(self):
        assert _slug("Stripe") == "stripe"

    def test_spaces_become_hyphens(self):
        assert _slug("Senior Backend Engineer") == "senior-backend-engineer"

    def test_path_traversal_neutralised(self):
        # '.' and '/' collapse to '-', so traversal sequences cannot survive.
        result = _slug("../../etc/passwd")
        assert "/" not in result
        assert ".." not in result

    def test_empty_returns_untitled(self):
        assert _slug("") == "untitled"

    def test_only_symbols_returns_untitled(self):
        assert _slug("/////") == "untitled"

    def test_truncated_to_40(self):
        assert len(_slug("a" * 100)) == 40
