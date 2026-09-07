# 0001: Hugo + Bulma (npm/Hugo Pipes) + htmx + Alpine.js

## Status

Accepted

## Context

`caninecommunication` needed a frontend stack. Two decisions were made in sequence, both through a PoC/grilling process with the site owner rather than picked unilaterally:

1. **Hugo vs. Next.js/Amplify** (ticket #3): a side-by-side mockup canvas comparing a Hugo-simple direction against a Next.js/Amplify-modern direction, same copy and layout, only execution polish varying.
2. **UI specifics** (ticket #4, this ADR): color scheme, CSS framework, and how much client-side interactivity to add on top of Hugo.

## Decisions

**Hugo**, not Next.js/Amplify. The owner already knows Hugo (it runs griz.sh), and the PoC's extra visual polish on the Next.js side wasn't judged worth the added build complexity for a site of this size.

**Bulma, via npm + Hugo Pipes**, not a CDN link. griz.sh loads Bulma from a CDN (`<link>` to `bulma.min.css`); this site instead vendors Bulma's Sass source (`npm install bulma`) and compiles it through Hugo's asset pipeline. This is a deliberate deviation from griz.sh, chosen because:
   - Bulma v1 is a full rewrite that generates its component styling from a small set of Sass variables into CSS custom properties (`--bulma-*`) — configuring those variables at compile time gives a real custom color scheme, not just a handful of CSS overrides bolted onto the default palette.
   - The import list is **trimmed** to the Bulma partials actually in use (see `assets/sass/main.scss`), grown incrementally as later tickets need more components, rather than the wholesale `@use "bulma"` entry point griz.sh's CDN link effectively pulls in.
   - **Setup dependency**: despite "extended" in its name, the locally-installed Hugo binary does *not* bundle Dart Sass — `transpiler: dartsass` requires a standalone `dart-sass` executable on `PATH` (`brew install dart-sass` / `apt install dart-sass`, or see gohugo.io's Dart Sass install docs). The `sass-embedded` npm package was tried first and does **not** work for this (Hugo's docs explicitly warn it off - embedded Dart Sass was deprecated in 2023). This is a real prerequisite for anyone building this site, not just an implementation detail.
   - **Bulma theme-system gotcha**: Bulma's light theme hardcodes `scheme-main-l` at `100%` — it isn't exposed as a configurable `!default` Sass variable — so the page background renders pure white regardless of the `$scheme-h`/`$scheme-s` override unless the resulting `--bulma-scheme-main*` CSS custom properties are overridden directly afterward. `assets/sass/main.scss` does this, scoped with `@media not all and (prefers-color-scheme: dark)` and `[data-theme="light"]` so it doesn't clobber Bulma's own automatic dark theme.

**Warm sand & espresso** color scheme, configured through Bulma's own `initial-variables`/`derived-variables` Sass hooks (`$scheme-h`, `$scheme-s`, `$primary`, `$link`) rather than a hand-rolled parallel CSS-variable system. This was the deliberate choice: Bulma v1 already ships a real light/dark theme pair (`themes/light.scss`, `themes/dark.scss`) keyed off these same variables and auto-switches on `prefers-color-scheme`, plus supports a manual `[data-theme="light"|"dark"]` override — which is exactly the "structured so a toggle is cheap later" requirement without inventing our own theming mechanism. No manual toggle UI is built yet; only the automatic OS-preference switch is live.

**Lora (headings) + Nunito Sans (body)**, chosen from a 4-way visual specimen comparison (a plain HTML page, not the color-scheme mockup canvas) against the brief "easy to read, not corporate/textbook."

**htmx 2.x + Alpine.js**, both via CDN (same versions/delivery mechanism griz.sh already uses: htmx 2.0.10, Alpine 3.16.3). htmx is scoped to genuinely server-driven interactions (chat widget responses, FAQ answer fragments, the client-capture form) — not used for pure client-side state, which Alpine.js handles (e.g. the mobile nav burger toggle, implemented with Alpine's `x-data`/`@click` rather than griz.sh's hand-rolled `DOMContentLoaded` listener). Both Lambda endpoints this site calls live on a different origin than the site itself, so `htmx-config` disables `selfRequestsOnly` — same requirement griz.sh's chat widget already documents.

## Consequences

- Anyone building this site locally needs `dart-sass` on `PATH` in addition to Hugo and Node/npm - not obvious from Hugo's "extended" binary name alone.
- The trimmed Bulma import list in `assets/sass/main.scss` must be extended (not replaced with the wholesale `bulma` entry point) whenever a later ticket needs a Bulma component not already imported.
- A future light/dark toggle UI is cheap: it only needs to set `document.documentElement.dataset.theme = "light" | "dark"`, since the CSS already responds to that attribute.
