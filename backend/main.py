"""FastAPI application entry point."""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from config import settings
from models import StartPipelineRequest, StartPipelineResponse
from pipeline import cancel, confirm, run_pipeline, start_pipeline, subscribe
from security import RateLimiter, UnsafeUrlError, validate_job_url
from storage import ensure_carrvo_home, load_applications

logging.basicConfig(level=settings.log_level)

# Starting a pipeline launches a browser and an AI call — keep it modest.
_start_limiter = RateLimiter(max_requests=10, window_seconds=60)


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_carrvo_home()
    yield


app = FastAPI(title="Carrvo API", version="0.1.0", docs_url="/docs", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pipeline endpoints ────────────────────────────────────────────────────────

@app.post("/api/pipeline/start", response_model=StartPipelineResponse)
async def pipeline_start(
    body: StartPipelineRequest,
    background_tasks: BackgroundTasks,
    request: Request,
) -> StartPipelineResponse:
    """
    Start a new pipeline run for the given job URL.
    Returns a job_id — subscribe to /api/pipeline/{job_id}/events for progress.
    """
    client_ip = request.client.host if request.client else "unknown"
    if not _start_limiter.allow(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests. Please slow down.")

    # Reject SSRF / malformed URLs before we ever fetch them.
    try:
        url = validate_job_url(body.url)
    except UnsafeUrlError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Minimal profile — full profile system is deferred (Phase 2)
    profile: dict = {}

    job_id = start_pipeline()
    background_tasks.add_task(run_pipeline, job_id, url, profile)
    return StartPipelineResponse(job_id=job_id)


@app.get("/api/pipeline/{job_id}/events")
async def pipeline_events(job_id: str) -> EventSourceResponse:
    """SSE stream for a running pipeline. Emits step_start, step_done, step_error,
    confirmation_needed, submitted, and cancelled events."""

    async def generator():
        async for event in subscribe(job_id):
            yield {
                "event": event["event"],
                "data": json.dumps(event["data"]),
            }

    return EventSourceResponse(generator())


@app.post("/api/pipeline/{job_id}/confirm")
async def pipeline_confirm(job_id: str) -> JSONResponse:
    """Signal that the user has reviewed and confirmed the application."""
    ok = confirm(job_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Pipeline not found or already finished.")
    return JSONResponse({"ok": True})


@app.post("/api/pipeline/{job_id}/cancel")
async def pipeline_cancel(job_id: str) -> JSONResponse:
    """Cancel a running pipeline at the confirmation gate."""
    ok = cancel(job_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Pipeline not found or already finished.")
    return JSONResponse({"ok": True})


# ── Application log ───────────────────────────────────────────────────────────

@app.get("/api/log")
async def get_log() -> JSONResponse:
    """Return all past applications, newest first."""
    entries = await load_applications()
    return JSONResponse([e.model_dump(mode="json") for e in entries])


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "version": "0.1.0"})
