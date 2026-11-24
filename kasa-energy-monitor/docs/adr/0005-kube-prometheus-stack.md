# 0005. kube-prometheus-stack for metrics, alerts and dashboards

- **Status:** Proposed
- **Date:** 2026-11-24

## Context

The cluster already runs a manually installed Prometheus-based stack. The project needs
storage for about a year of data from a few dozen time series, alerting and dashboards.

## Decision

Keep kube-prometheus-stack (Prometheus Operator, Prometheus, Alertmanager, Grafana) and
adopt it into Argo CD. Use `ServiceMonitor` and `PrometheusRule` resources for integration.

## Consequences

- Industry-standard tooling with extensive documentation and community dashboards.
- Monitoring configuration becomes declarative Kubernetes resources shipped with each app.
- Higher memory footprint than alternatives — irrelevant at this scale.

## Alternatives considered

- **VictoriaMetrics** — more efficient storage and memory, but its advantages do not matter
  for ~30 series, and Prometheus is the more common skill in job requirements.
