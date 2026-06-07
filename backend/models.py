from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, HttpUrl


class AtsPortal(str, Enum):
    greenhouse = "greenhouse"
    lever = "lever"
    ashby = "ashby"
    workday = "workday"
    unknown = "unknown"


class PipelineStepName(str, Enum):
    scrape = "scrape"
    tailor_resume = "tailor_resume"
    tailor_cover = "tailor_cover"
    compile = "compile"
    submit = "submit"


class ApplicationStatus(str, Enum):
    submitted = "submitted"
    error = "error"
    pending = "pending"


# ── API request/response ──────────────────────────────────────────────────────

class StartPipelineRequest(BaseModel):
    url: str


class StartPipelineResponse(BaseModel):
    job_id: str


class ConfirmRequest(BaseModel):
    job_id: str


# ── Domain models ─────────────────────────────────────────────────────────────
# Defined before the SSE event payloads that reference them so Pydantic can
# resolve the annotations at class-definition time.

class JobInfo(BaseModel):
    title: str
    company: str
    location: str
    portal: AtsPortal
    url: str
    word_count: int
    description_text: str


class TailoringInfo(BaseModel):
    resume_changes: list[str]
    cover_letter_opening: str
    resume_tex_path: str
    cover_letter_tex_path: str
    resume_pdf_path: str
    cover_letter_pdf_path: str


# ── SSE event payloads ────────────────────────────────────────────────────────

class StepStartEvent(BaseModel):
    step: PipelineStepName
    message: str


class StepDoneEvent(BaseModel):
    step: PipelineStepName
    message: str
    elapsed_ms: int
    payload: dict[str, Any] = {}


class StepErrorEvent(BaseModel):
    step: PipelineStepName
    message: str


class ConfirmationNeededEvent(BaseModel):
    job: JobInfo
    tailoring: TailoringInfo


class SubmittedEvent(BaseModel):
    success: bool
    confirmation_url: str = ""


class ApplicationEntry(BaseModel):
    id: str
    date: str
    company: str
    role: str
    portal: AtsPortal
    url: str
    status: ApplicationStatus
    resume_path: str
    cover_letter_path: str
    submitted_at: datetime | None = None
