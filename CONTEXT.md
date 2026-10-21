# caninecommunication

## What this is

Business/booking companion site to griz.sh. Same person and brand, but professional and conversion-focused: services, payments, appointment scheduling, and a client list. griz.sh remains the casual, content-focused blog — this site doesn't replace it.

## Glossary

**griz.sh** — The existing Hugo-based dog-training blog at griz.sh, titled "Canine Communication with Griz." Has its own AWS-hosted chatbot (Lambda + Bedrock) that searches its published content. Stays independent of this site.

**Cross-site agent** — This site's own chat agent, run on a separate Lambda from griz.sh's chatbot. Answers from three sources: this site's own content, griz.sh's public `index.json`, and the custom-responses data directory.

**Custom-responses data directory** — A local, hand-editable data directory holding canned Q&A the site owner can add to directly, searched by the cross-site agent alongside real page content. Format decided when the agent is built.

**Client record** — A DynamoDB row for one client/lead: name, email, consent timestamp, appointment history. Written by the client-capture form.

**Booking link-out** — The Book page's "Book online" button: a link to the owner's single Proton Calendar booking page (home area only), not an embed, since Proton booking pages are standalone hosted links. Travel-area clients book by email instead.

**Service** — One bookable unit of training (e.g. Verbal Markers, Recall). Services build on each other: each lists the services it requires.
_Avoid_: Class, package, day

**Fundamentals Bootcamp** — An example full build that chains the core services in order. A guideline that gets customized per client, not a requirement.
_Avoid_: Bootcamp (alone), program

**In-Home Consult** — The entry service every new client starts with, held at the client's home. Booked with a consult deposit.
_Avoid_: Day 0, Behavior Consult, evaluation

**Consult deposit** — The $30 paid for the In-Home Consult, credited toward the first training session if booked within 60 days; non-refundable unless the owner declines the dog. Paid at the consult until online payment exists.

**Returning client** — Someone who has completed an In-Home Consult and can book any service whose requirements they meet.
_Avoid_: Member, existing customer

**Home area** — El Paso County. Clients here can book online, Fridays and Saturdays, 6am–6pm.

**Travel area** — Teller, Douglas, Elbert, Pueblo, Fremont, and Lincoln counties. Clients here book by email so drive time can be planned, and pay a mileage fee.
_Avoid_: Surrounding counties, service radius

**Mileage fee** — $0.70 per mile, round trip, measured from the El Paso County line, charged per visit in the travel area.
_Avoid_: Travel fee, trip charge

**Client community** — The owner's Discord server, for clients and people the owner chooses to invite. Joined through an unlisted invite page, not linked publicly.
_Avoid_: Club, chat, Discord channel

## Status

Frontend framework not yet chosen. See the ADR in `docs/adr/` once it exists (Hugo vs. Next.js/Amplify, informed by a look-and-feel PoC) before assuming either.
