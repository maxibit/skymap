# 0008. Device identity, info metric and base units

- **Status:** Proposed
- **Date:** 2026-11-24

## Context

Plugs can be renamed in the Kasa app and can change IP address. Using the alias or the IP
as a label breaks time series when either changes. Prometheus conventions recommend base
units (seconds, bytes, joules) and the `_total` suffix for counters.

## Decision

- Identify devices by `device_id` (from `get_sysinfo`); it is the only identifying label on
  measurement metrics.
- Expose descriptive data (alias, model, versions, MAC, host) through
  `kasa_plug_info{...} 1` and join it in queries with `group_left`.
- Expose energy as `kasa_energy_joules_total`; dashboards convert to kWh.
- Compute cost in Grafana from a dashboard variable, not in the application.

## Consequences

- Renaming a plug updates its display name without creating a new series.
- Queries are slightly longer because of the join.
- Price changes do not require a redeploy.

## Alternatives considered

- **Alias/IP as labels on every metric** — simpler queries, broken history on rename.
- **kWh as the exported unit** — more readable, but against the naming conventions.
