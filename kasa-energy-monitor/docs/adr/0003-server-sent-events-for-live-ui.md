# 0003. Server-Sent Events for the live UI

- **Status:** Proposed
- **Date:** 2026-11-24

## Context

The UI needs pushed updates every poll cycle. The only browser-to-server action (toggling
a relay) is rare and fits a normal HTTP request.

## Decision

Use Server-Sent Events (`/api/stream`) for server-to-browser updates and plain `POST`
requests for commands. Send a heartbeat comment every 15 s.

## Consequences

- Plain HTTP: works through Cloudflare Tunnel and proxies without special configuration.
- Built-in automatic reconnection in the browser (`EventSource`).
- The heartbeat keeps the connection below Cloudflare's idle timeout.
- One-directional only — acceptable for this use case.

## Alternatives considered

- **WebSocket** — bidirectional, but more complex and not needed.
- **Client polling** — simpler, but wasteful and adds latency.
