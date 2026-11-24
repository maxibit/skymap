# 0010. Sealed Secrets for secrets in Git

- **Status:** Proposed
- **Date:** 2026-11-24

## Context

GitOps requires every resource in Git, including the cloudflared tunnel token, the Grafana
admin password and the notification token. The GitOps repository may be public.

## Decision

Use Bitnami Sealed Secrets. Only `SealedSecret` objects, encrypted with the controller's
public key, are committed. The controller's private key is backed up outside the cluster.

## Consequences

- Secrets live safely in a public repository; Argo CD needs no plugins.
- Losing the controller key without a backup means re-creating every secret.
- Secrets are bound to the cluster (and by default to name and namespace).

## Alternatives considered

- **SOPS + age (KSOPS)** — encrypts files, cluster-independent, but needs an Argo CD plugin.
- **External Secrets Operator** — best with an external store (Vault, cloud secret managers);
  no such store exists here.
