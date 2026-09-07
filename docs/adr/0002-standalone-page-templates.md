# 0002: Standalone root-level pages need a `type` front matter override

## Status

Accepted

## Context

`content/book.md` is a standalone page at the content root (not inside a section) - per the content architecture decision, Home/Book/Contact/About are all single pages like this, while Services/Testimonials/FAQ are sections.

The obvious guess - a template named after the content file, `layouts/book.html` - does **not** get used. Hugo's template lookup for a root-level page of kind `page` doesn't match on filename; it falls through to a generic `layouts/page.html` (which doesn't exist in this repo) and the content renders as a bare, un-styled page with no layout applied - Hugo warns `found no layout file for "html" for kind "page"` and separately `Template /book.html is unused` (visible with `--printUnusedTemplates`), but a plain build gives no indication anything is wrong.

## Decision

Give the page a `type` front matter value matching a pseudo-section name, then put its template at `layouts/<type>/page.html` - the same path Hugo would use for a page inside a real section named `<type>`, even though no such content directory exists:

```yaml
# content/book.md
---
title: "Book a Session"
type: "book"
---
```

```
layouts/book/page.html
```

## Consequences

Contact and About (also standalone root-level pages, not yet built) need the same pattern: `type: "contact"` / `type: "about"` front matter plus `layouts/contact/page.html` / `layouts/about/page.html` - not a same-named file directly under `layouts/`.
