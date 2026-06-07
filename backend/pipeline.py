"""Async pipeline orchestration with SSE streaming.

Each pipeline run gets a unique job_id. The caller streams events by subscribing
to an asyncio.Queue. Events are JSON-serialisable dicts with an `event` type field.

Flow:
  start_pipeline(url) -> job_id
  subscribe(job_id)   -> AsyncGenerator[dict]  (consumed by the SSE endpoint)
  confirm(job_id)     -> resumes the pipeline at the submit step
"""

from __future__ import annotations

import asyncio
import time
import uuid
from pathlib import Path
from typing import AsyncGenerator

from ats import get_ats, CaptchaEncountered, MissingProfileField
from compiler import compile_latex, CompilerError
from models import ApplicationStatus, AtsPortal
from scraper import get_scraper, ScraperError
from storage import (
    ensure_carrvo_home,
    new_application_entry,
    append_application,
    read_base_resume,
    read_base_cover_letter,
    write_job_file,
    copy_to_job_dir,
)
from tailorer import tailor_resume, generate_cover_letter, inject_into_template

# ── State store ───────────────────────────────────────────────────────────────

_queues: dict[str, asyncio.Queue[dict | None]] = {}
_confirm_events: dict[str, asyncio.Event] = {}
_cancel_events: dict[str, asyncio.Event] = {}

# ── Public API ────────────────────────────────────────────────────────────────


def start_pipeline() -> str:
    """Register a new pipeline run and return its job_id. Call `run_pipeline` in a task."""
    job_id = str(uuid.uuid4())
    _queues[job_id] = asyncio.Queue()
    _confirm_events[job_id] = asyncio.Event()
    _cancel_events[job_id] = asyncio.Event()
    return job_id


async def subscribe(job_id: str) -> AsyncGenerator[dict, None]:
    """Yield SSE-ready event dicts until the pipeline finishes or errors."""
    q = _queues.get(job_id)
    if not q:
        yield {"event": "error", "data": {"message": "Unknown job_id"}}
        return

    while True:
        item = await q.get()
        if item is None:
            break
        yield item


def confirm(job_id: str) -> bool:
    event = _confirm_events.get(job_id)
    if not event:
        return False
    event.set()
    return True


def cancel(job_id: str) -> bool:
    event = _cancel_events.get(job_id)
    if not event:
        return False
    event.set()
    return True


# ── Pipeline runner ───────────────────────────────────────────────────────────


async def run_pipeline(job_id: str, url: str, profile: dict) -> None:
    """Run the full pipeline asynchronously. Sends events to the subscriber queue."""
    q = _queues[job_id]
    confirm_event = _confirm_events[job_id]
    cancel_event = _cancel_events[job_id]

    async def emit(event: str, data: dict) -> None:
        await q.put({"event": event, "data": data})

    async def step_start(name: str, msg: str) -> float:
        await emit("step_start", {"step": name, "message": msg})
        return time.perf_counter()

    async def step_done(name: str, msg: str, started_at: float, payload: dict | None = None) -> None:
        elapsed = int((time.perf_counter() - started_at) * 1000)
        await emit("step_done", {"step": name, "message": msg, "elapsed_ms": elapsed, "payload": payload or {}})

    async def step_error(name: str, msg: str) -> None:
        await emit("step_error", {"step": name, "message": msg})
        await q.put(None)

    try:
        ensure_carrvo_home()

        # ── Step 1: Scrape ────────────────────────────────────────────────────
        t = await step_start("scrape", "Fetching and parsing the job listing…")
        try:
            scraper = get_scraper(url)
            job = await scraper.scrape(url)
        except ScraperError as exc:
            await step_error("scrape", str(exc))
            return

        await step_done(
            "scrape",
            f"Found {job.word_count:,} words · {job.portal.title()} portal",
            t,
            {"title": job.title, "company": job.company, "location": job.location},
        )

        # ── Step 2: Tailor resume ─────────────────────────────────────────────
        t = await step_start("tailor_resume", "Tailoring your resume for this role…")
        try:
            base_resume = read_base_resume()
        except FileNotFoundError as exc:
            await step_error("tailor_resume", str(exc))
            return

        try:
            tailored = await tailor_resume(job.full_text, base_resume)
        except Exception as exc:
            await step_error("tailor_resume", f"AI tailoring failed: {exc}")
            return

        resume_tex_path = write_job_file(job.company, job.title, "resume_tailored.tex", tailored.latex)
        change_summary = "; ".join(tailored.changes[:3])
        await step_done("tailor_resume", change_summary, t, {"changes": tailored.changes})

        # ── Step 3: Tailor cover letter ───────────────────────────────────────
        t = await step_start("tailor_cover", "Writing a tailored cover letter…")
        try:
            base_cl = read_base_cover_letter()
        except FileNotFoundError as exc:
            await step_error("tailor_cover", str(exc))
            return

        try:
            # Extract resume summary (first 800 chars of the description text as proxy)
            resume_summary = base_resume[:800]
            cl_body = await generate_cover_letter(job.full_text, resume_summary)
            cl_latex = inject_into_template(base_cl, cl_body)
        except Exception as exc:
            await step_error("tailor_cover", f"Cover letter generation failed: {exc}")
            return

        cl_tex_path = write_job_file(job.company, job.title, "coverletter_tailored.tex", cl_latex)
        cl_opening = cl_body.split("\n\n")[0][:200]
        await step_done("tailor_cover", "Cover letter written (3 paragraphs)", t, {"opening": cl_opening})

        # ── Step 4: Compile PDFs ──────────────────────────────────────────────
        t = await step_start("compile", "Compiling LaTeX to PDF…")
        try:
            resume_pdf_tmp = await compile_latex(tailored.latex, "resume")
            cl_pdf_tmp = await compile_latex(cl_latex, "coverletter")
        except CompilerError as exc:
            await step_error("compile", str(exc))
            return

        resume_pdf_path = copy_to_job_dir(resume_pdf_tmp, job.company, job.title)
        cl_pdf_path = copy_to_job_dir(cl_pdf_tmp, job.company, job.title)
        resume_pdf_tmp.unlink(missing_ok=True)
        cl_pdf_tmp.unlink(missing_ok=True)

        await step_done(
            "compile",
            f"resume.pdf ({_kb(resume_pdf_path)} KB) · coverletter.pdf ({_kb(cl_pdf_path)} KB)",
            t,
            {"resume_pdf": str(resume_pdf_path), "cover_letter_pdf": str(cl_pdf_path)},
        )

        # ── Confirmation gate ─────────────────────────────────────────────────
        await emit("confirmation_needed", {
            "job": {
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "portal": job.portal,
                "url": url,
                "word_count": job.word_count,
                "description_text": job.description_text[:500],
            },
            "tailoring": {
                "resume_changes": tailored.changes,
                "cover_letter_opening": cl_opening,
                "resume_tex_path": str(resume_tex_path),
                "cover_letter_tex_path": str(cl_tex_path),
                "resume_pdf_path": str(resume_pdf_path),
                "cover_letter_pdf_path": str(cl_pdf_path),
            },
        })

        # Wait for user confirmation or cancellation
        done, _ = await asyncio.wait(
            [
                asyncio.create_task(confirm_event.wait()),
                asyncio.create_task(cancel_event.wait()),
            ],
            return_when=asyncio.FIRST_COMPLETED,
        )

        if cancel_event.is_set():
            await emit("cancelled", {"message": "Application cancelled by user."})
            await q.put(None)
            return

        # ── Step 5: Submit ────────────────────────────────────────────────────
        t = await step_start("submit", "Submitting application via ATS…")
        try:
            ats = get_ats(job.portal)
            result = await ats.fill_and_submit(url, resume_pdf_path, cl_pdf_path, profile)
        except CaptchaEncountered as exc:
            await step_error("submit", f"CAPTCHA required: {exc}")
            return
        except MissingProfileField as exc:
            await step_error("submit", str(exc))
            return
        except KeyError:
            # Portal not yet supported — log as pending so the user can finish manually.
            await step_done("submit", "Portal not yet supported — logged as pending", t)
            entry = new_application_entry(
                job.company, job.title,
                AtsPortal(job.portal), url,
                str(resume_pdf_path), str(cl_pdf_path),
                status=ApplicationStatus.pending,
            )
            await append_application(entry)
            await emit(
                "submitted",
                {
                    "success": False,
                    "confirmation_url": "",
                    "message": "Logged as pending — portal not yet automated.",
                },
            )
            return
        except Exception as exc:
            await step_error("submit", f"Submission failed: {exc}")
            return

        await step_done("submit", "Application submitted successfully", t, {"confirmation_url": result.confirmation_url})

        entry = new_application_entry(
            job.company, job.title,
            AtsPortal(job.portal), url,
            str(resume_pdf_path), str(cl_pdf_path),
        )
        await append_application(entry)

        await emit("submitted", {"success": True, "confirmation_url": result.confirmation_url})

    except Exception as exc:
        await q.put({"event": "fatal_error", "data": {"message": str(exc)}})
    finally:
        await q.put(None)
        _queues.pop(job_id, None)
        _confirm_events.pop(job_id, None)
        _cancel_events.pop(job_id, None)


def _kb(path: Path) -> int:
    try:
        return path.stat().st_size // 1024
    except OSError:
        return 0
