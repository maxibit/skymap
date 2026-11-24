# Architecture Decision Records

Significant decisions are recorded here using a lightweight
[MADR](https://adr.github.io/madr/)-style format. An ADR is never edited after it is
accepted; a later ADR supersedes it instead.

| ADR | Title | Status |
|---|---|---|
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions | Accepted |
| [0002](0002-background-polling-with-cache.md) | Background polling with an in-memory cache | Proposed |
| [0003](0003-server-sent-events-for-live-ui.md) | Server-Sent Events for the live UI | Proposed |
| [0004](0004-single-replica.md) | Run a single replica of the exporter | Proposed |
| [0005](0005-kube-prometheus-stack.md) | kube-prometheus-stack for metrics, alerts and dashboards | Proposed |
| [0006](0006-helm-chart-published-as-oci.md) | Package the application as a Helm chart published to an OCI registry | Proposed |
| [0007](0007-cloudflare-tunnel-without-ingress.md) | Expose services through Cloudflare Tunnel without an Ingress controller | Proposed |
| [0008](0008-device-identity-and-metric-units.md) | Device identity, info metric and base units | Proposed |
| [0009](0009-separate-app-and-gitops-repositories.md) | Separate application and GitOps repositories, app-of-apps | Proposed |
| [0010](0010-sealed-secrets.md) | Sealed Secrets for secrets in Git | Proposed |
| [0011](0011-dependency-free-embedded-ui.md) | Dependency-free UI embedded in the binary | Proposed |
| [0012](0012-pushover-notifications.md) | Pushover for alert notifications | Proposed |
| [0013](0013-cloudflare-zero-trust.md) | Cloudflare Zero Trust for access and identity | Proposed |

Template: [template.md](template.md).
