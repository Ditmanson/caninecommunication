# Mailing tool comparison (ticket #9)

## Context

Client emails already land in DynamoDB (`caninecommunication-clients`, ticket #5) with a consent timestamp — that part is decided. This is only about which tool actually *sends* campaigns to that list. Not deployed or decided yet; AWS work in general is on hold until domain/Proton/Stripe setup is done (see `CLAUDE.md`), so this is pure research to close out the standing TODO, not an implementation ticket.

## Candidates

| Tool | Free tier | Cheapest paid tier | Integration effort with our DynamoDB list |
|---|---|---|---|
| **Buttondown** | 100 subscribers | $9/mo → 1,000 subscribers | Clean, well-documented REST API; straightforward to upsert a contact on signup |
| **Mailchimp** | 250 contacts, 500 sends/mo | $13/mo | Has an API, but subscribed **and unsubscribed** contacts both count against the limit — costs creep over time even as your active list shrinks |
| **Kit** (formerly ConvertKit) | 10,000 subscribers | $33/mo → 1,000 subscribers (only kicks in past the free tier's 10k) | REST API for subscriber management; same shape of integration as Buttondown |
| **AWS SES** | 62,000 emails/mo free forever, when sent from Lambda | $0.10 per 1,000 emails after that | No contact/list management, no unsubscribe handling, no campaign editor, no analytics — all of that has to be hand-built against our own DynamoDB table |

Sources: [Buttondown pricing](https://www.sequenzy.com/pricing/buttondown), [Mailchimp pricing 2026](https://mailtoolfinder.com/blog/mailchimp-free-plan-changes-2026/), [Kit pricing](https://kit.com/pricing), [Amazon SES pricing 2026](https://leadsnipper.com/blog/amazon-ses-pricing-2026)

## Notes

- **Integration effort is basically a wash between Buttondown, Mailchimp, and Kit** — all three expose a straightforward contacts API, so syncing a new DynamoDB record over (e.g. via a DynamoDB Streams-triggered Lambda) is the same shape of work regardless of which one is picked. The real differentiator between those three is price/list-size, not engineering effort.
- **AWS SES is the outlier**: dramatically cheaper per-email, and it's the "AWS-native" answer, but it is pure send infrastructure. Bounce/complaint handling, unsubscribe links, list segmentation, and a campaign-composing UI would all need to be built by hand. That's a real project, not a config choice — it fights the "avoid unneeded build complexity" value this project has otherwise followed (Hugo over Next.js, Bulma over a hand-rolled design system).
- **Kit's free tier (10,000 subscribers) is unusually generous** compared to Mailchimp's shrinking free tier (250 contacts as of Jan 2026) — confirmed directly from Kit's own pricing page, not just aggregator claims, since the number looked surprising enough to double-check.
- Mailchimp's free-tier contact-counting quirk (unsubscribes still count against your limit) is a real long-term cost trap for a small business that doesn't actively prune its list.

## Recommendation

**Kit**, for now. At this business's likely scale (a single dog-training practice, not a media company), 10,000 free subscribers is very unlikely to be exceeded for years, the API integration effort is no different from the alternatives, and it avoids Mailchimp's unsubscribe-counting cost trap entirely. Revisit only if the list genuinely approaches 10k, or if AWS SES becomes attractive later because a real list-management UI already exists for some other reason (unlikely to be worth building just for this).

Buttondown is a reasonable second choice if the "developer/markdown-first" feel matters more than the free-tier ceiling — its 100-subscriber free tier is much tighter, so it would mean paying sooner.
