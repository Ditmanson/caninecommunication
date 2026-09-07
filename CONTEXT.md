# caninecommunication

## What this is

Business/booking companion site to griz.sh. Same person and brand, but professional and conversion-focused: services, payments, appointment scheduling, and a client list. griz.sh remains the casual, content-focused blog — this site doesn't replace it.

## Glossary

**griz.sh** — The existing Hugo-based dog-training blog at griz.sh, titled "Canine Communication with Griz." Has its own AWS-hosted chatbot (Lambda + Bedrock) that searches its published content. Stays independent of this site.

**Cross-site agent** — This site's own chat agent, run on a separate Lambda from griz.sh's chatbot. Answers from three sources: this site's own content, griz.sh's public `index.json`, and the custom-responses data directory.

**Custom-responses data directory** — A local, hand-editable data directory holding canned Q&A the site owner can add to directly, searched by the cross-site agent alongside real page content. Format decided when the agent is built.

**Client record** — A DynamoDB row for one client/lead: name, email, consent timestamp, appointment history. Written by the client-capture form.

**Booking link-out** — The site's "Book an appointment" CTA. Links to an external booking page URL rather than embedding one, because Proton Calendar's appointment-scheduling feature (the intended long-term destination, once Proton Pro is purchased) only produces a standalone hosted link, not an embeddable widget.

## Status

Frontend framework not yet chosen. See the ADR in `docs/adr/` once it exists (Hugo vs. Next.js/Amplify, informed by a look-and-feel PoC) before assuming either.
