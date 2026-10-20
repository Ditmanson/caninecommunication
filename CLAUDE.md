## Agent skills

### Issue tracker

Issues and specs live as GitHub Issues on `Ditmanson/caninecommunication`. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context layout (`CONTEXT.md` + `docs/adr/` at the repo root). See `docs/agents/domain.md`.

## Project

Business/booking site for griz.sh's owner — the professional, conversion-focused counterpart to griz.sh's casual dog-training blog. See `CONTEXT.md` for the domain glossary. griz.sh is not being migrated or retired as part of this project.

## Workflow

- Solo dev (owner + Claude). Iterative design, test-driven development.
- Stack (ADR 0001): Hugo + Bulma (npm/Hugo Pipes) + htmx + Alpine.js. AWS-native, same AWS account as griz.sh.
- **The site is live** at k9-communication.com on Amplify, which auto-builds `main`. A push is a deploy: commit freely, but push only when the owner says so.
- **Test before committing:** `python3 -m unittest discover tests` (builds the site; checks home page structure and every internal link/anchor), plus `hugo server` on localhost for visual checks, including phone width (~390px).
- **Lambdas are live:** `chat-agent` (the Cross-site agent) and `client-capture` (deployed, currently unused). Updating code with `lambda/<name>/deploy.sh` is reversible and fine once the owner has approved the change. Creating new AWS resources still needs explicit owner confirmation first.
- **Keep the chat agent in sync:** `BUSINESS_FACTS` in `lambda/chat-agent/handler.py` repeats prices, policies, booking paths, and contact info. When those change on the site, update it and redeploy.
- **Still off:** Stripe (`paymentsLive: false`, see #7) and the Turnstile CAPTCHA (needs owner-created Cloudflare keys). Don't enable either without the owner.

## Versioning

Annotated git tags, `vMAJOR.MINOR.PATCH`, starting at `v1.0.0` (first complete live site). Tag only when the owner asks.

- **MAJOR**: a redesign or a change in how the business works (e.g. new booking or payment model).
- **MINOR**: new pages, services, FAQ batches, or features.
- **PATCH**: fixes and copy edits.

`git tag -a vX.Y.Z -m "summary"` then `git push origin vX.Y.Z`.
