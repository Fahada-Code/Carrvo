r"""Security guards for untrusted input.

Two threat surfaces are defended here:
  1. Job URLs — a user (or attacker, in a hosted deployment) controls the URL we fetch.
     Without validation this is a Server-Side Request Forgery (SSRF) vector: an attacker
     could point us at cloud metadata endpoints, localhost services, or internal IPs.
  2. AI-generated LaTeX — Claude's output is untrusted text that we hand to a LaTeX
     compiler. LaTeX can execute shell commands (\write18) and read arbitrary files
     (\input, \openin), so we scan for those primitives before compiling.
"""

from __future__ import annotations

import ipaddress
import re
import socket
import time
from collections import defaultdict, deque
from urllib.parse import urlparse


class UnsafeUrlError(ValueError):
    """Raised when a job URL fails validation."""


class UnsafeLatexError(ValueError):
    """Raised when LaTeX source contains a command that could execute code or read files."""


# ── URL validation (SSRF defense) ─────────────────────────────────────────────

_ALLOWED_SCHEMES = {"http", "https"}


def validate_job_url(url: str) -> str:
    """
    Validate that a URL is safe to fetch. Returns the normalised URL.
    Raises UnsafeUrlError if the scheme is not http(s) or the host resolves to a
    private, loopback, link-local, or reserved IP range.
    """
    if not url or len(url) > 2048:
        raise UnsafeUrlError("URL is empty or unreasonably long.")

    parsed = urlparse(url.strip())

    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise UnsafeUrlError(
            f"URL scheme '{parsed.scheme}' is not allowed. Only http and https are permitted."
        )

    if not parsed.hostname:
        raise UnsafeUrlError("URL has no host.")

    # Resolve the hostname and reject any address in a non-public range.
    for addr in _resolve_all(parsed.hostname):
        if not _is_public_address(addr):
            raise UnsafeUrlError(
                f"URL host '{parsed.hostname}' resolves to a non-public address ({addr}) "
                "and cannot be fetched."
            )

    return url.strip()


def _resolve_all(hostname: str) -> list[str]:
    """Resolve a hostname to all of its IP addresses. Raises UnsafeUrlError on failure."""
    # A literal IP is its own resolution.
    try:
        ipaddress.ip_address(hostname)
        return [hostname]
    except ValueError:
        pass

    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise UnsafeUrlError(f"Could not resolve host '{hostname}': {exc}") from exc

    return list({info[4][0] for info in infos})


def _is_public_address(addr: str) -> bool:
    """Return True only if the address is a routable, public IP."""
    try:
        ip = ipaddress.ip_address(addr)
    except ValueError:
        return False

    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


# ── LaTeX validation (RCE / file-read defense) ────────────────────────────────

# Primitives that can execute shell commands, read/write arbitrary files, or
# pull in remote content. Compiling LaTeX that contains these is unsafe.
_DANGEROUS_LATEX = re.compile(
    r"\\(write18|immediate\s*\\write18|input|include|openin|openout|read|"
    r"write|catcode|csname|directlua|latelua|shellescape|usepackage\s*\{\s*shellesc)",
    re.IGNORECASE,
)

# \input and \include are common in legitimate resumes (splitting sections), so we
# only block them when they reference an absolute path or a parent directory.
_DANGEROUS_PATH_INPUT = re.compile(
    r"\\(input|include)\s*\{[^}]*(\.\.|/|\\\\|~)[^}]*\}",
    re.IGNORECASE,
)


def scan_latex(source: str) -> None:
    """
    Raise UnsafeLatexError if the LaTeX source contains a command capable of
    executing code or reading files outside the working directory.
    """
    if re.search(r"\\write18", source, re.IGNORECASE):
        raise UnsafeLatexError("LaTeX contains \\write18 (shell execution).")

    if re.search(r"\\(directlua|latelua)", source, re.IGNORECASE):
        raise UnsafeLatexError("LaTeX contains Lua execution primitives.")

    if re.search(r"\\(openout|openin|read)\b", source, re.IGNORECASE):
        raise UnsafeLatexError("LaTeX contains file I/O primitives (\\openout/\\openin/\\read).")

    if _DANGEROUS_PATH_INPUT.search(source):
        raise UnsafeLatexError(
            "LaTeX \\input/\\include references an absolute or parent-directory path."
        )


# ── Rate limiting ─────────────────────────────────────────────────────────────

class RateLimiter:
    """
    Fixed-window in-memory rate limiter keyed by client identifier.

    In-process only — adequate for a single local instance, which is Carrvo's
    deployment model. A hosted multi-instance deployment would swap this for Redis.
    """

    def __init__(self, max_requests: int, window_seconds: float) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        window_start = now - self.window_seconds
        hits = self._hits[key]

        while hits and hits[0] < window_start:
            hits.popleft()

        if len(hits) >= self.max_requests:
            return False

        hits.append(now)
        return True
