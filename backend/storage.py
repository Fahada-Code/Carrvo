"""Read/write operations for ~/.carrvo/ — the local application store."""

from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

import aiofiles

from config import settings
from models import ApplicationEntry, ApplicationStatus, AtsPortal


def _slug(text: str) -> str:
    """
    Convert text to a safe directory-name slug. Every non-alphanumeric character
    (including '.', '/', and '\\') collapses to '-', which neutralises path-traversal
    attempts such as '../../etc' from scraped company/role names.
    """
    slug = "".join(c if c.isalnum() else "-" for c in text.lower()).strip("-")[:40]
    return slug or "untitled"


def job_dir(company: str, role: str) -> Path:
    """
    Return the job-specific directory, guaranteed to stay within jobs_dir.
    The final path is resolved and checked so a crafted name can never escape the tree.
    """
    candidate = (settings.jobs_dir / f"{_slug(company)}_{_slug(role)}").resolve()
    jobs_root = settings.jobs_dir.resolve()
    if jobs_root not in candidate.parents and candidate != jobs_root:
        raise ValueError("Resolved job directory escapes the jobs root.")
    return candidate


def ensure_carrvo_home() -> None:
    settings.carrvo_home.mkdir(parents=True, exist_ok=True)
    settings.jobs_dir.mkdir(parents=True, exist_ok=True)

    if not settings.applications_log.exists():
        settings.applications_log.write_text("[]", encoding="utf-8")
    if not settings.qa_bank.exists():
        settings.qa_bank.write_text("{}", encoding="utf-8")


def read_base_resume() -> str:
    if not settings.resume_path.exists():
        raise FileNotFoundError(
            f"Base resume not found at {settings.resume_path}. "
            "Place your LaTeX resume there to get started."
        )
    return settings.resume_path.read_text(encoding="utf-8")


def read_base_cover_letter() -> str:
    if not settings.cover_letter_path.exists():
        raise FileNotFoundError(
            f"Base cover letter not found at {settings.cover_letter_path}. "
            "Place your LaTeX cover letter template there to get started."
        )
    return settings.cover_letter_path.read_text(encoding="utf-8")


def write_job_file(company: str, role: str, filename: str, content: str | bytes) -> Path:
    """Write a file into the job-specific directory. Returns the path."""
    d = job_dir(company, role)
    d.mkdir(parents=True, exist_ok=True)
    path = d / filename
    if isinstance(content, str):
        path.write_text(content, encoding="utf-8")
    else:
        path.write_bytes(content)
    return path


def copy_to_job_dir(src: Path, company: str, role: str) -> Path:
    d = job_dir(company, role)
    d.mkdir(parents=True, exist_ok=True)
    dst = d / src.name
    shutil.copy2(src, dst)
    return dst


async def append_application(entry: ApplicationEntry) -> None:
    async with aiofiles.open(settings.applications_log, mode="r", encoding="utf-8") as f:
        entries = json.loads(await f.read())
    entries.insert(0, entry.model_dump(mode="json"))
    async with aiofiles.open(settings.applications_log, mode="w", encoding="utf-8") as f:
        await f.write(json.dumps(entries, indent=2, default=str))


async def load_applications() -> list[ApplicationEntry]:
    if not settings.applications_log.exists():
        return []
    async with aiofiles.open(settings.applications_log, mode="r", encoding="utf-8") as f:
        raw = json.loads(await f.read())
    return [ApplicationEntry(**r) for r in raw]


def new_application_entry(
    company: str,
    role: str,
    portal: AtsPortal,
    url: str,
    resume_path: str,
    cover_letter_path: str,
    status: ApplicationStatus = ApplicationStatus.submitted,
) -> ApplicationEntry:
    return ApplicationEntry(
        id=str(uuid.uuid4()),
        date=datetime.now(timezone.utc).date().isoformat(),
        company=company,
        role=role,
        portal=portal,
        url=url,
        status=status,
        resume_path=resume_path,
        cover_letter_path=cover_letter_path,
        submitted_at=datetime.now(timezone.utc),
    )
