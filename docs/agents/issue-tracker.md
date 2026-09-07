# Issue tracker: GitHub Issues

Issues and specs for this repo live as GitHub Issues on `Ditmanson/caninecommunication`.

## Conventions

- One feature = one **epic** issue, labeled `epic`. Its body holds the spec (problem statement, solution, implementation/testing decisions, out-of-scope notes).
- Implementation tickets are separate issues, one per vertical slice, each starting with a `Parent: #<epic-issue-number>` line.
- A ticket's dependencies are recorded as a `Blocked by: #N, #N` line near the top, or "None (can start immediately)".
- Acceptance criteria are a GitHub task list (`- [ ]` / `- [x]`) in the ticket body.
- A ticket that's actionable now gets the `ready-for-agent` label; leave it off tickets still blocked.
- Closing an issue (state `closed`, reason `completed`) is how "done" is recorded. Conversation/history is regular issue comments, not a body section.
- The epic issue's body (or a pinned comment) lists its child ticket issues as a task list once they exist, and the epic is closed once every child ticket is closed.

## When a skill says "publish to the issue tracker"

Create the epic issue first (if the feature doesn't have one yet), then one issue per ticket, in dependency order, via `gh issue create` or `gh api repos/Ditmanson/caninecommunication/issues`. Label actionable tickets `ready-for-agent`.

## When a skill says "fetch the relevant ticket"

`gh issue view <number>` (or the issue URL the user gives you).

## Wayfinding operations

Used by `/wayfinder`. This is a separate mechanism from feature tickets above — it tracks a research/decision effort as local files, not GitHub issues. The **map** is a file with one **child** file per ticket.

- **Map**: `.scratch/<effort>/map.md` (the Notes / Decisions-so-far / Fog body).
- **Child ticket**: `.scratch/<effort>/issues/NN-<slug>.md`, numbered from `01`, with the question in the body. A `Type:` line records the ticket type (`research`/`prototype`/`grilling`/`task`); a `Status:` line records `claimed`/`resolved`.
- **Blocking**: a `Blocked by: NN, NN` line near the top. A ticket is unblocked when every file it lists is `resolved`.
- **Frontier**: scan `.scratch/<effort>/issues/` for files that are open, unblocked, and unclaimed; first by number wins.
- **Claim**: set `Status: claimed` and save before any work.
- **Resolve**: append the answer under an `## Answer` heading, set `Status: resolved`, then append a context pointer (gist + link) to the map's Decisions-so-far in `map.md`.
