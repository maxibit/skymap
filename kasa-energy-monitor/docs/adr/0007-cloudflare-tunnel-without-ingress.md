# 0007. Expose services through Cloudflare Tunnel without an Ingress controller

- **Status:** Proposed
- **Date:** 2026-11-24

## Context

`cloudflared` already runs in the cluster with two replicas. The home network should not
open inbound ports.

## Decision

Route public hostnames directly from cloudflared to the Kubernetes Services. Protect every
hostname with a Cloudflare Access policy.

## Consequences

- No inbound ports, no certificate management in the cluster, no Ingress controller to operate.
- Authentication happens at the edge before traffic reaches the cluster.
- Routing configuration is coupled to Cloudflare; moving away requires an Ingress controller.
- Local access during a Cloudflare outage uses `kubectl port-forward`.

## Alternatives considered

- **Ingress controller (ingress-nginx / Traefik) or Gateway API behind the tunnel** — a more
  portable setup and a good future learning step, but an extra component with no current need.
