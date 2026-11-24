# 0012. Pushover for alert notifications

- **Status:** Proposed
- **Date:** 2026-11-24

## Context

Alerts must reach the phone reliably, with different urgency for a crashed exporter and a
plug that lost Wi-Fi, and with a link to the runbook. Running an extra service just to
deliver notifications is undesirable in a small cluster.

## Decision

- Send notifications to Pushover with Alertmanager's native `pushover_configs` receiver.
- Configure it once, centrally, in the kube-prometheus-stack values in `homelab-gitops`,
  so cluster alerts and application alerts share the same route tree.
- Read the user key and application token from files (`user_key_file`, `token_file`)
  mounted from a SealedSecret, so the credentials never appear in Git or in the rendered
  Alertmanager configuration.
- Map severity to priority: `critical` → 1, `warning` → 0, `info` → -1; route `Watchdog`
  and `InfoInhibitor` to a `null` receiver.
- Put the `runbook_url` annotation in the message `url` field.

## Consequences

- No bridge or extra workload to run; delivery and retries are handled by Pushover.
- Priorities map naturally to severities and respect the phone's quiet hours.
- External dependency, and the Pushover app is a paid one-time purchase per platform after
  the trial.
- File-based credentials require a recent Alertmanager release.

## Alternatives considered

- **ntfy** — free and self-hostable, but either another service to operate or a public
  server, and it needs a webhook bridge from Alertmanager.
- **Telegram** — native receiver, but bot setup and no real priority levels.
- **E-mail** — native, but too slow and noisy for alerts.
- **`AlertmanagerConfig` resources per namespace** — the operator adds a `namespace`
  matcher, so a config in `monitoring` would not receive alerts labelled
  `namespace="kasa"`. A central configuration is simpler with a single receiver.
