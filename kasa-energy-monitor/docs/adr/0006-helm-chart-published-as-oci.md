# 0006. Package the application as a Helm chart published to an OCI registry

- **Status:** Proposed
- **Date:** 2026-11-24

## Context

The application must be deployable by Argo CD and installable by anyone trying the project.
It ships optional monitoring resources (ServiceMonitor, PrometheusRule, dashboard).

## Decision

Maintain a Helm chart in `deploy/helm/kasa-energy-monitor`, validated with
`values.schema.json`, tested with chart-testing on kind, and published to
`oci://ghcr.io/<user>/charts` on every release.

## Consequences

- The application is consumed like any third-party chart, by version.
- Optional resources are toggled through values.
- Templating adds complexity compared to plain manifests.

## Alternatives considered

- **Kustomize** — simpler overlays, but no packaging, versioning or distribution story.
- **Plain manifests** — fine for the first PoC, not reusable.
