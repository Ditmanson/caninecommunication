# caninecommunication

## What this is

The business/booking site of K9-Communication LLC, companion to the Blog at griz.sh. Same person and brand, but professional and conversion-focused: services, payments, appointment scheduling, and a client list. The Blog is the casual, content-focused side — this site doesn't replace it.

## Glossary

**Blog** — K9-Communication LLC's Blog at griz.sh, live since 2026-11-22 from its own repo (`Ditmanson/k9-blog`, with its own glossary). Replaced the old "Canine Communication with Griz" site without carrying its posts over. No chat agent of its own.
_Avoid_: Griz's training blog

**Cross-site agent** — This site's chat agent. Answers from three sources: this site's own content, the Blog's public `index.json`, and the custom-responses data directory.

**Custom-responses data directory** — A local, hand-editable data directory holding canned Q&A the site owner can add to directly, searched by the cross-site agent alongside real page content. Format decided when the agent is built.

**Client record** — A DynamoDB row for one client/lead: name, email, consent timestamp, appointment history. Written by the client-capture form.

**Booking** — Clients text, call, or email the owner; the owner confirms by hand. No online booking, no prices on the Book page. The Book page shows weekly availability from `data/schedule.yaml`.

**Service** — One bookable unit of training (e.g. Food and Play Training, Capstone). Services build on each other: each lists the services it requires.

**Foundation services** — Food and Play Training, then Escape and Avoidance Training. Every other training service requires both. They replaced Verbal Markers/Commands and absorbed Recall, Heeling, and Chill Training.

**Dog record** — One dated training session of the owner's dogs (Griz, Denali), in `content/training-records/records/`, tagged `dogs: [griz, denali]`. Listed newest first on each dog's page with the dog's age that day. A video appears in only one record per dog.
_Avoid_: Post, blog entry

**Archive** — `/archive/`: retired service pages kept for reference. Unlisted (noindex, out of sitemap and chat index) and linked from nowhere on the site.
_Avoid_: Class, package, day

**Fundamentals Bootcamp** — An example full build that chains the core services in order. A guideline that gets customized per client, not a requirement.
_Avoid_: Bootcamp (alone), program

**In-Home Consult** — The entry service every new client starts with, held at the client's home. Booked with a consult deposit; about 30 minutes.

**Video/Phone Consult** — Optional, free call before the In-Home Consult to check fit and give general advice. Requested by text, call, or email. Doesn't replace the In-Home Consult.
_Avoid_: Day 0, Behavior Consult, evaluation

**Stimulus** — Whatever a client's dog struggles to behave around: a place (the daily walk) or an event (people coming over). Every plan is built around one or more.
_Avoid_: Trigger (reserved for the Behavior Modification decision-making process), distraction

**Threshold** — How close a dog can get to a stimulus while still behaving appropriately. Training moves it.

**Plan** — Written by the owner after the In-Home Consult and approved by the client before training starts: the stimulus, the threshold, the method (food and play, escape and avoidance, or both layered), and the sessions.

**Consult deposit** — The $30 paid for the In-Home Consult, credited toward the first training session if booked within 60 days; non-refundable unless the owner declines the dog. Paid at the consult until online payment exists.

**Returning client** — Someone who has completed an In-Home Consult and can book any service whose requirements they meet.
_Avoid_: Member, existing customer

**Service area** — Colorado Springs, Fountain, Pueblo, Hanover, Woodland Park, Falcon, Ellicott, Yoder, Calhan, and surrounding areas (`serviceAreas` in hugo.yaml). Replaces the old home/travel county split; no mileage fee is published.
_Avoid_: Home area, travel area

**Client community** — The owner's Discord server, for clients and people the owner chooses to invite. Joined through an unlisted invite page, not linked publicly.
_Avoid_: Club, chat, Discord channel

## Status

Frontend framework not yet chosen. See the ADR in `docs/adr/` once it exists (Hugo vs. Next.js/Amplify, informed by a look-and-feel PoC) before assuming either.
