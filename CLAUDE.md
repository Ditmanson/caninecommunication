## Agent skills

### Issue tracker

Issues and specs live as GitHub Issues on `Ditmanson/caninecommunication`. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context layout (`CONTEXT.md` + `docs/adr/` at the repo root). See `docs/agents/domain.md`.

## Project

Business/booking site for griz.sh's owner — the professional, conversion-focused counterpart to griz.sh's casual dog-training blog. See `CONTEXT.md` for the domain glossary. griz.sh is not being migrated or retired as part of this project.

## Workflow

- Solo dev (owner + Claude). Iterative design, test-driven development.
- Test on localhost only. Never deploy or go live without an explicit ask from the owner via a GitHub issue.
- AWS-native — reuse the same AWS account/credentials already set up for griz.sh.
- Frontend framework is not yet decided. Don't assume Hugo or Next.js until the ADR from ticket #4 exists in `docs/adr/`.
