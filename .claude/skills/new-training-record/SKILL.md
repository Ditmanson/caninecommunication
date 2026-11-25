---
name: new-training-record
description: Gather facts and write a training record on k9-communication.com. Use when adding a new dog (client or the owner's own) or a new dated session for a dog already in /training-records/.
---

# New training record

A training record is two kinds of page:

- **Dog page**: `content/training-records/<dog>/_index.md`, `layout: dog`. The bio, and the list of that dog's sessions (newest first, with the dog's age that day).
- **Session**: `content/training-records/records/<dog>-<slug>.md`, tagged `dogs: [<dog>]`. One dated session.

Templates: `content/training-records/donar/` and `records/donar-first-day.md` (client dog), `griz/` and `denali/` (the owner's dogs). Read the matching template before writing.

## 1. Gather

Source is whatever the owner gave: a message, notes, or `newcontent.md` (repo root). Read it, then fill every gap below. Ask with AskUserQuestion, batching up to 4 questions per round, until every fact is settled.

New dog:

- **Name** as it should appear publicly: spelling confirmed, and first name only or with the family surname.
- **Born**: date, or just the year. Year only → `born: <year>-07-01` with a comment saying only the year is known; the table shows the year.
- **Breed**, **problem** that brought them in, the family's **goals**.
- **Starting point**: what the dog knows, food drive, play drive.
- **Plan**: K9-Communication's plan for the dog.

Every session:

- **Date**.
- **Where the dog started**, **what we did**, any **goals** set.
- **Who did what**: anything the handler or family came up with gets credited to them, never to us.
- **Media**: YouTube IDs and photos, or none yet. A video goes in only one session per dog.

Ambiguous words in the notes (homophones, misspellings that could be two words) get asked about, never guessed. Done when every fact on the page traces to the owner.

## 2. Write

Match the griz.sh dog posts (`../k9-blog/content/posts/denali.md`):

- **Dog page**: one-paragraph intro, then a `| <Name> | The short version |` table, then short `##` sections (the plan, methods, next steps). End with "His/Her sessions are newest first." plus "No photos or videos yet." when that's true.
- **Session**: one-line intro, then `##` sections of bullets.
- **Bullets** open with a bold lead: `- **Meals in the vehicle:** ...`.
- **Voice**: the owner's, first person, plain and short. Fix typos; keep the meaning.
- **Links**: methods link to their service page (`/services/food-and-play-training/`, `/services/escape-and-avoidance-training/`, anchors from their `##` headings); threshold → `/services/in-home-consult/#how-we-make-your-plan`; Premack → bold `**[Granny's rule/Premack principle](https://en.wikipedia.org/wiki/Premack%27s_principle)**`.
- **Weight** on a new dog page: after the existing cards, so the owner's dogs stay pinned first.

## 3. Check

1. Add a test to `DogRecords` in `tests/test_site.py`: the dog's page lists the session, with the age when `born` is set.
2. `python3 -m unittest discover tests` goes green.
3. Commit. Push, tag, and the `newcontent.md` reset follow `CLAUDE.md`.

Report to the owner: the pages and URLs, every typo fix or wording change made to their notes, and anything left open.
