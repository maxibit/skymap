# 0011. Dependency-free UI embedded in the binary

- **Status:** Proposed
- **Date:** 2026-11-24

## Context

The original prototype loaded Tailwind (Play CDN, intended for development only) and
ECharts from public CDNs. Historical charts now live in Grafana, so the UI only needs
live cards, on/off buttons and small sparklines.

## Decision

Write the UI in plain HTML, CSS and JavaScript, embedded with `go:embed`. Draw sparklines
as inline SVG. No external requests from the browser.

## Consequences

- A single self-contained binary; the UI works without internet access.
- A strict Content-Security-Policy (`default-src 'self'`) becomes possible.
- No build step for the frontend.
- Styling and charts are hand-written; acceptable for a small UI.

## Alternatives considered

- **Bundled framework (React/Vue + Vite)** — more productive for large UIs, adds a toolchain.
- **Embedding ECharts locally** — works offline, but duplicates what Grafana already does.
