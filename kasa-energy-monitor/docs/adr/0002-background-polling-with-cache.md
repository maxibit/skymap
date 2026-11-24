# 0002. Background polling with an in-memory cache

- **Status:** Proposed
- **Date:** 2026-11-24

## Context

Two consumers need plug data: Prometheus (every 15 s) and the live UI (every few seconds,
any number of browsers). Many exporters, including the community exporter used so far,
follow the *multi-target* pattern: Prometheus calls `/scrape?target=<ip>` and the exporter
queries the device during the scrape.

## Decision

A background poller queries each plug every 5 s and stores the latest reading in memory.
`/metrics`, `/api/plugs` and the SSE stream all read from this cache.

## Consequences

- The load on the plugs is constant and independent of the number of browsers and scrapers.
- The UI and Prometheus see the same data.
- Prometheus timestamps may be up to one poll interval older than the actual reading —
  acceptable for energy monitoring.
- The plug list lives in the exporter configuration rather than in the Prometheus scrape config.

## Alternatives considered

- **Multi-target, poll on scrape** — simpler and stateless, but the live UI would need its
  own polling path, and every additional scraper would hit the plugs again.
