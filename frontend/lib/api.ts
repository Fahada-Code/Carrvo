/**
 * Carrvo backend API client.
 * All functions talk to the FastAPI backend at NEXT_PUBLIC_API_URL.
 */

const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

// ── Pipeline ──────────────────────────────────────────────────────────────────

export async function startPipeline(url: string): Promise<string> {
  const res = await fetch(`${BASE}/api/pipeline/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  });
  if (!res.ok) throw new Error(`Failed to start pipeline: ${res.statusText}`);
  const data = await res.json();
  return data.job_id as string;
}

export function openPipelineStream(jobId: string): EventSource {
  return new EventSource(`${BASE}/api/pipeline/${jobId}/events`);
}

export async function confirmPipeline(jobId: string): Promise<void> {
  const res = await fetch(`${BASE}/api/pipeline/${jobId}/confirm`, { method: 'POST' });
  if (!res.ok) throw new Error(`Confirm failed: ${res.statusText}`);
}

export async function cancelPipeline(jobId: string): Promise<void> {
  await fetch(`${BASE}/api/pipeline/${jobId}/cancel`, { method: 'POST' });
}

// ── Log ───────────────────────────────────────────────────────────────────────

export async function fetchLog(): Promise<ApplicationEntry[]> {
  const res = await fetch(`${BASE}/api/log`);
  if (!res.ok) throw new Error(`Failed to fetch log: ${res.statusText}`);
  return res.json();
}

// ── Types (mirrors backend models) ───────────────────────────────────────────

export interface ApplicationEntry {
  id: string;
  date: string;
  company: string;
  role: string;
  portal: string;
  url: string;
  status: 'submitted' | 'error' | 'pending';
  resume_path: string;
  cover_letter_path: string;
  submitted_at: string | null;
}

export interface JobInfo {
  title: string;
  company: string;
  location: string;
  portal: string;
  url: string;
  word_count: number;
  description_text: string;
}

export interface TailoringInfo {
  resume_changes: string[];
  cover_letter_opening: string;
  resume_tex_path: string;
  cover_letter_tex_path: string;
  resume_pdf_path: string;
  cover_letter_pdf_path: string;
}

// ── SSE event payloads ────────────────────────────────────────────────────────

export type SseEventType =
  | 'step_start'
  | 'step_done'
  | 'step_error'
  | 'confirmation_needed'
  | 'submitted'
  | 'cancelled'
  | 'fatal_error';

export interface StepStartPayload { step: string; message: string }
export interface StepDonePayload  { step: string; message: string; elapsed_ms: number; payload: Record<string, unknown> }
export interface StepErrorPayload { step: string; message: string }
export interface ConfirmationPayload { job: JobInfo; tailoring: TailoringInfo }
export interface SubmittedPayload { success: boolean; confirmation_url: string }
