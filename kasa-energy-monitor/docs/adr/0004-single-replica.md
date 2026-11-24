# 0004. Run a single replica of the exporter

- **Status:** Proposed
- **Date:** 2026-11-24

## Context

The exporter keeps state in memory and polls a small number of plugs. Several replicas
would each poll every plug, multiplying the load on devices that are known to be fragile,
and would expose diverging data.

## Decision

Run exactly one replica with a `RollingUpdate` strategy. Availability relies on fast
restarts by Kubernetes.

## Consequences

- A pod restart causes a gap of a few seconds in data and in the UI — acceptable.
- During a rollout two pods briefly poll in parallel; harmless because polling is read-only.
- No PodDisruptionBudget with `minAvailable: 1` (it would block node drains).

## Alternatives considered

- **Multiple replicas with leader election** (Kubernetes Lease) — real HA, but complexity
  without a matching requirement. Revisit if the exporter ever becomes critical.
