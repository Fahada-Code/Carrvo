# Carrvo

**Paste a link. Get a tailored resume, cover letter, and submitted application — in minutes.**

Carrvo is an open-core AI job application assistant. It takes a job listing URL and handles everything after that: scraping the description, tailoring your LaTeX resume and cover letter with AI, compiling both to PDF, and auto-submitting through the ATS portal (Workday, Greenhouse, Lever, Ashby, and more).

The one manual step: you sign up and log into the job portal yourself. Everything after that is automated.

---

## Why Carrvo

Spray-and-pray job applications are dead. ATS systems score resumes against job descriptions, and recruiters instantly recognize generic cover letters. The people getting callbacks tailor every single application — but that takes hours per role. Carrvo makes high-quality, tailored applications as fast as bulk applying.

Carrvo's insight: one intentional manual step (account creation) unlocks everything else, avoids bot detection at the account level, and keeps the user in control of every submission.

---

## How It Works

```
  Paste URL
      │
      ▼
  ┌─────────┐   ┌──────────────┐   ┌──────────────┐   ┌─────────┐   ┌────────┐
  │ Scrape  │──▶│ Tailor       │──▶│ Tailor       │──▶│ Compile │──▶│ Submit │
  │ the job │   │ resume (AI)  │   │ cover letter │   │ to PDF  │   │ to ATS │
  └─────────┘   └──────────────┘   └──────────────┘   └─────────┘   └────────┘
                                                                         ▲
                                              You review & confirm ──────┘
```

Every application pauses for your confirmation before submission. Carrvo never submits a generic application, never fabricates experience, and never overwrites your base files.

---

## Architecture

```
carrvo/
├── frontend/            Next.js UI — URL input, live pipeline view, confirmation, log
│   ├── app/             Routes: / , /apply , /log
│   ├── components/      UrlInput, PipelineStatus, ConfirmationScreen, ApplicationLog
│   └── lib/             API client, types, ATS detection
│
├── backend/             FastAPI service — orchestrates the pipeline, streams progress over SSE
│   ├── main.py          API endpoints (start / events / confirm / cancel / log)
│   ├── pipeline.py      Async orchestrator with per-step SSE events
│   ├── scraper/         Per-portal scrapers (Greenhouse, Lever, Ashby, Workday, generic)
│   ├── tailorer/        Claude-powered resume + cover letter tailoring
│   ├── ats/             Playwright form-filling per portal
│   ├── compiler.py      LaTeX → PDF (tectonic / pdflatex), shell-escape disabled
│   ├── security.py      SSRF guard, LaTeX scanner, rate limiter
│   └── storage.py       Local ~/.carrvo/ read/write
│
├── scripts/             Standalone, open-source ATS automation + scraper (no backend needed)
└── docs/                Contributor guides
```

The frontend works on its own with built-in mock data, and automatically switches to the real backend when it's reachable at `NEXT_PUBLIC_API_URL`.

---

## Quick Start

### 1. Frontend (UI)

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The UI runs standalone with mock data — no backend required to explore it.

### 2. Backend (full pipeline)

Requires **Python 3.11+** and a LaTeX engine ([`tectonic`](https://tectonic-typesetting.github.io/) recommended, or `pdflatex`).

```bash
cd backend
cp .env.example .env          # then add your ANTHROPIC_API_KEY
pip install -r requirements.txt
playwright install chromium
uvicorn main:app --reload --port 8000
```

Place your base files before applying:

```
~/.carrvo/resume.tex          your base LaTeX resume
~/.carrvo/coverletter.tex     your cover letter template (use %%BODY%% as the body placeholder)
```

With both servers running, paste a job URL in the UI and watch the pipeline run end-to-end.

---

## Command Line (no backend)

The scripts in `scripts/` run independently:

```bash
# Scrape any job listing to plain text
python scripts/scraper.py https://boards.greenhouse.io/company/jobs/123456 --output job.txt

# Run a portal's form-filling script directly
python scripts/greenhouse.py --url <job-url> --resume resume.pdf \
    --cover-letter coverletter.pdf --profile profile.json
```

---

## Security

Carrvo handles someone's career and personal documents, so security is treated as non-negotiable. Key protections built in:

- **SSRF protection** — job URLs are validated before fetching; private, loopback, link-local, and cloud-metadata addresses are rejected (`security.validate_job_url`).
- **LaTeX sandboxing** — AI-generated `.tex` is scanned for shell-execution and file-I/O primitives (`\write18`, `\input{/abs}`, `\directlua`, …) and the compiler runs with `-no-shell-escape`.
- **Prompt-injection defense** — scraped job text is passed to Claude as clearly delimited untrusted data; the model is instructed never to follow instructions embedded in it.
- **Path-traversal safety** — company/role names are slugified and resolved job directories are verified to stay within `~/.carrvo/jobs/`.
- **Rate limiting** — the pipeline-start endpoint is rate-limited per client.
- **No secrets in code** — all secrets come from environment variables; user data and credentials are never logged.

See `CLAUDE.md §14` for the full security policy.

---

## Testing

```bash
cd backend
pip install -r requirements-dev.txt
pytest                # unit tests for security, scraping detection, storage, escaping
ruff check .          # lint
black --check .       # format check
```

Frontend:

```bash
cd frontend
npx tsc --noEmit      # type check (strict)
npm run lint          # ESLint
```

---

## Tech Stack

| Component | Tool |
|---|---|
| Frontend | Next.js 16 · Tailwind CSS v4 · TypeScript (strict) |
| Backend API | FastAPI · SSE (sse-starlette) |
| Job scraping | httpx · BeautifulSoup · Playwright |
| AI tailoring | Claude API (`claude-sonnet-4-6`) with prompt caching |
| LaTeX compilation | tectonic / pdflatex |
| ATS automation | Playwright |
| Storage | Local JSON (`~/.carrvo/`) |
| License | Apache 2.0 |

---

## Open Core Model

| Layer | License | What it includes |
|---|---|---|
| Automation | Apache 2.0 | Scraping, ATS form-filling, PDF compilation, CLI, community portal scripts |
| AI | Premium | Resume tailoring, cover letter generation, Q&A answering, profile intelligence |

---

## Contributing

Community ATS scripts live in `scripts/`. See [`docs/adding-ats-script.md`](docs/adding-ats-script.md) for the interface contract and testing requirements, and [`docs/contributing.md`](docs/contributing.md) for the general guide.

---

## License

Apache 2.0 — see [`LICENSE`](LICENSE).
