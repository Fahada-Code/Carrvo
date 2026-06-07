"""Tests for the security guards: URL validation, LaTeX scanning, rate limiting."""

import pytest

from security import (
    RateLimiter,
    UnsafeLatexError,
    UnsafeUrlError,
    scan_latex,
    validate_job_url,
)


# ── URL validation (SSRF) ─────────────────────────────────────────────────────

class TestValidateJobUrl:
    def test_accepts_public_https_url(self):
        url = "https://boards.greenhouse.io/stripe/jobs/123"
        assert validate_job_url(url) == url

    def test_rejects_non_http_scheme(self):
        with pytest.raises(UnsafeUrlError):
            validate_job_url("file:///etc/passwd")

    def test_rejects_ftp_scheme(self):
        with pytest.raises(UnsafeUrlError):
            validate_job_url("ftp://example.com/resource")

    def test_rejects_loopback(self):
        with pytest.raises(UnsafeUrlError):
            validate_job_url("http://127.0.0.1:8000/admin")

    def test_rejects_localhost_name(self):
        with pytest.raises(UnsafeUrlError):
            validate_job_url("http://localhost/secret")

    def test_rejects_cloud_metadata_ip(self):
        # AWS/GCP link-local metadata endpoint — a classic SSRF target.
        with pytest.raises(UnsafeUrlError):
            validate_job_url("http://169.254.169.254/latest/meta-data/")

    def test_rejects_private_10_range(self):
        with pytest.raises(UnsafeUrlError):
            validate_job_url("http://10.0.0.5/internal")

    def test_rejects_private_192_range(self):
        with pytest.raises(UnsafeUrlError):
            validate_job_url("http://192.168.1.1/router")

    def test_rejects_empty(self):
        with pytest.raises(UnsafeUrlError):
            validate_job_url("")

    def test_rejects_overlong(self):
        with pytest.raises(UnsafeUrlError):
            validate_job_url("https://example.com/" + "a" * 3000)

    def test_rejects_no_host(self):
        with pytest.raises(UnsafeUrlError):
            validate_job_url("https://")


# ── LaTeX scanning (RCE / file read) ──────────────────────────────────────────

class TestScanLatex:
    def test_allows_clean_resume(self):
        clean = r"""
        \documentclass{article}
        \begin{document}
        \section{Experience}
        \begin{itemize}
          \item Built distributed systems at scale.
        \end{itemize}
        \end{document}
        """
        scan_latex(clean)  # should not raise

    def test_blocks_write18(self):
        with pytest.raises(UnsafeLatexError):
            scan_latex(r"\immediate\write18{rm -rf /}")

    def test_blocks_directlua(self):
        with pytest.raises(UnsafeLatexError):
            scan_latex(r"\directlua{os.execute('whoami')}")

    def test_blocks_openout(self):
        with pytest.raises(UnsafeLatexError):
            scan_latex(r"\openout\myfile=/tmp/x.txt")

    def test_blocks_absolute_path_input(self):
        with pytest.raises(UnsafeLatexError):
            scan_latex(r"\input{/etc/passwd}")

    def test_blocks_parent_dir_input(self):
        with pytest.raises(UnsafeLatexError):
            scan_latex(r"\include{../../secrets}")

    def test_allows_relative_input_same_dir(self):
        # Splitting a resume into local section files is legitimate.
        scan_latex(r"\input{experience}")


# ── Rate limiter ──────────────────────────────────────────────────────────────

class TestRateLimiter:
    def test_allows_within_limit(self):
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        assert all(limiter.allow("client") for _ in range(3))

    def test_blocks_over_limit(self):
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            limiter.allow("client")
        assert limiter.allow("client") is False

    def test_separate_keys_independent(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        assert limiter.allow("a") is True
        assert limiter.allow("b") is True
        assert limiter.allow("a") is False
