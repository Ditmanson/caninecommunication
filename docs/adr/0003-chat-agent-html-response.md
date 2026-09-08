# 0003: Chat agent returns raw HTML, not JSON+Mustache

## Status

Accepted

## Context

griz.sh's existing chatbot (`lambda/chatbot/handler.py` in that repo) returns `{"answer": "<html>"}` as JSON, and its widget uses `htmx-ext-json-enc` (to send JSON) plus `htmx-ext-client-side-templates` + Mustache (to unwrap `.answer` and inject it as HTML) - three extra script dependencies beyond htmx itself.

This site's chat agent (`lambda/chat-agent/`, ticket #6) doesn't need any of that: every other htmx integration on this site (the FAQ accordion's fragments, the client-capture form) already returns the answer as a direct HTML response body, and htmx's default `hx-swap` just injects it - no JSON unwrapping step required.

## Decision

The chat agent Lambda returns the rendered HTML answer directly as the response body (same `_markdown_to_safe_html` conversion logic as griz.sh's bot, just not wrapped in JSON), and the widget (`layouts/_partials/chatWidget.html`) is a plain `<form>` with `hx-post` - no `json-enc`, no `client-side-templates`, no Mustache. One fewer pattern to hold in mind, three fewer script tags loaded on every page.

## A real htmx gotcha hit while building this

`hx-target="find .chat-answer"` failed with `htmx:targetError` in the browser console - `find` only searches **descendants** of the element carrying the attribute. The chat widget's `.chat-answer` div is a **sibling** of the `<form>`, not nested inside it, so `find` never locates it. Fixed with `hx-target="next .chat-answer"` (same fix already used correctly in the FAQ accordion, where `.faq-answer` is genuinely a sibling of its button). The client-capture form (#5) never had this bug - its `.capture-response` div is the last child *inside* the form, where `find` is the right choice.

**Rule of thumb going forward**: `find` when the target is a descendant of the element with `hx-target`; `next` (or `closest`) when it's a sibling or ancestor instead. Check the actual DOM relationship, don't assume.

## Consequences

- Any future htmx wiring on this site should default to a direct-HTML-response Lambda, matching the rest of the site, rather than reaching for griz.sh's JSON+Mustache pattern.
- The chat agent's own site index (`SITE_CONTENT_INDEX_URL`) is fetched with graceful degradation - a failed fetch caches empty rather than raising, since this site isn't deployed yet and the agent still needs to answer from griz.sh's (already live) content and the custom-responses data in the meantime. Verified locally against the real, live `griz.sh/index.json`.
