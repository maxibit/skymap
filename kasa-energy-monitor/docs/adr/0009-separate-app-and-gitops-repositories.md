# 0009. Separate application and GitOps repositories, app-of-apps

- **Status:** Proposed
- **Date:** 2026-11-24

## Context

Argo CD is freshly installed; the existing workloads were installed by hand. The cluster
should be reproducible from Git, and releasing software should be separate from deploying it.

## Decision

- `kasa-energy-monitor` holds the application, its chart and its documentation.
- `homelab-gitops` holds the desired state of the whole cluster.
- `homelab-gitops` uses the app-of-apps pattern: one root Application, applied once by hand,
  creates an Application per component, including Argo CD itself.

## Consequences

- Deployments are reviewable pull requests and can be rolled back with `git revert`.
- CI in the application repository never needs credentials for the cluster.
- Version bumps require a second PR (automated by Renovate).

## Alternatives considered

- **Monorepo** — fewer moving parts, but mixes release and deployment concerns.
- **ApplicationSet** — useful with many similar apps or clusters; unnecessary for one cluster.
- **Flux** — equally valid; Argo CD is already installed and is more common in job requirements.
