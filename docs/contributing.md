# Contributing to Carrvo

## What to contribute

The open-source layer of Carrvo is the automation infrastructure:
- ATS portal scripts (`scripts/`)
- Job scraper improvements (`scripts/scraper.py`)
- PDF compilation utilities
- CLI commands

The AI tailoring layer (resume rewriting, cover letter generation, Q&A answering) is premium and not open for contribution at this stage.

## Getting started

1. Fork the repository
2. Create a branch: `git checkout -b feat/your-feature`
3. Make your changes following the coding conventions in `CLAUDE.md`
4. Run tests: `pytest scripts/tests/`
5. Submit a pull request

## Pull request checklist

- [ ] Code follows conventions in `CLAUDE.md §14`
- [ ] No secrets, credentials, or personal data committed
- [ ] Tests pass
- [ ] Error cases handled
- [ ] If adding an ATS script: tested against 3 real job postings

## Adding a new ATS portal script

See [`adding-ats-script.md`](adding-ats-script.md) for the detailed guide.

## Code of conduct

Be direct and professional. Focus on the work.
