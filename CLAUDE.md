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
- Stack decided (ticket #3/#4, ADR 0001): Hugo + Bulma (npm/Hugo Pipes) + htmx + Alpine.js.
- **AWS goes last.** Write and commit Lambda/backend code, deploy scripts, and IaC freely — but do not run any `aws` command that actually creates or modifies a real resource (`create-table`, `create-function`, `create-function-url-config`, etc.) until the owner has purchased the domain, set up Proton Pro, and set up Stripe. This is a deliberate sequencing decision, not a cost concern — confirm explicitly before crossing from "code is ready" to "resource is live," even for reversible/cheap resources.
