# Action Plan

The project is delivered in phases. Each phase ends with a clear exit criterion and is
merged through one or more pull requests, so the Git history tells the story of the project.

Phases 1–2 build the GitOps platform and bring the existing, manually installed workloads
under Argo CD. Phases 3–6 build and ship the application. Phases 7–9 finish operations,
security and documentation.

## Working conventions

- **Branches and PRs:** one branch per task, small PRs, squash merge into `main`.
- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/)
  (`feat:`, `fix:`, `docs:`, `ci:`, `chore:`) — used by release-please to generate versions
  and the changelog.
- **Versioning:** SemVer for the application image; the Helm chart has its own version,
  with `appVersion` tracking the image.
- **Decisions:** every non-trivial decision gets an ADR in [adr/](adr/).
- **Cluster changes:** only through `homelab-gitops` once Phase 1 is complete — no
  `kubectl apply` or `helm upgrade` by hand.

---

## Phase 0 — Inventory and preparation

**Goal:** know exactly what is running today and how it was installed.

- [ ] Create DHCP reservations for every plug in the router.
- [ ] Record each plug: host, model, `hw_ver`, `sw_ver`, `deviceId`, MAC.
- [ ] Capture a raw `get_sysinfo` + `get_realtime` response from each model (test fixtures).
- [ ] Record cluster facts: Kubernetes distribution and version, CNI, StorageClasses, node OS.
- [ ] `helm list -A` — list every Helm release with chart name and version.
- [ ] `helm get values <release> -n <ns> -o yaml` for every release — save the files.
- [ ] Find out how resources not installed with Helm were created (cloudflared, exporter).
- [ ] Note the metric names exposed by the community exporter and used by the current dashboard.
- [ ] Export the current Grafana dashboard JSON as a fallback.
- [ ] Create the GitHub repositories `kasa-energy-monitor` and `homelab-gitops`.

**Exit criterion:** an inventory document (`docs/inventory.md`) answers every open question
in [architecture.md § 14](architecture.md#14-open-questions).

**You learn:** Helm release internals, how to reverse-engineer an existing cluster.

---

## Phase 1 — GitOps foundation

**Goal:** Argo CD reconciles the cluster from `homelab-gitops`, including itself.

- [ ] Create the repository layout described in [repository-structure.md](repository-structure.md).
- [ ] Connect the repository to Argo CD (public repo, or a read-only deploy key).
- [ ] Write `bootstrap/root.yaml` — the root Application (app-of-apps) pointing at `apps/`.
- [ ] Add `apps/argocd.yaml` so Argo CD manages its own installation via its Helm chart,
      using the values of the current installation.
- [ ] Define an `AppProject` for platform components and one for applications.
- [ ] Enable automated sync with `prune` and `selfHeal` once the diff is clean.
- [ ] ADR-0009 (repository split, app-of-apps) accepted.

**Exit criterion:** `kubectl apply -f bootstrap/root.yaml` is the only manual command;
Argo CD shows itself as `Synced` / `Healthy`.

**You learn:** Argo CD Applications, AppProjects, app-of-apps, sync policies.

---

## Phase 2 — Adopt existing workloads without downtime

**Goal:** every workload installed by hand is now owned by Argo CD.

General rules for adoption:

1. Use the **same release name** as the manual install — resource names derive from it.
2. Use the **same chart version** and the **same values** saved in Phase 0. Upgrade later,
   in a separate PR.
3. Review the Argo CD diff before the first sync; a large diff means the values do not match.
4. Order components with `argocd.argoproj.io/sync-wave` annotations.
5. After adoption, never run `helm upgrade` by hand; remove leftover
   `sh.helm.release.v1.*` secrets once everything is stable.

Tasks:

- [ ] **Sealed Secrets** (wave `-10`): install the controller, back up its key offline,
      install the `kubeseal` CLI. ADR-0010 accepted.
- [ ] **kube-prometheus-stack** (wave `-5`): multi-source Application (chart from the Helm
      repository, values from Git), `ServerSideApply=true` (the operator CRDs are too large
      for client-side apply).
- [ ] Configure Prometheus storage (PVC) and `retention: 1y`.
- [ ] **Grafana**: move the admin password to a SealedSecret; enable the dashboard sidecar.
- [ ] **cloudflared**: move the tunnel token to a SealedSecret; document how routes are managed.
- [ ] **Community exporter**: adopt as-is (temporary, removed in Phase 6).

**Exit criterion:** `helm list -A` is no longer the source of truth; all Applications are
`Synced` / `Healthy`; deleting a managed Deployment by hand results in Argo CD recreating it.

**You learn:** resource adoption, sync waves, server-side apply, secrets in GitOps.

---

## Phase 3 — Application

**Goal:** a tested, well-structured Go service that runs locally against the real plugs.

- [ ] Initialise the module and the layout from [repository-structure.md](repository-structure.md).
- [ ] `internal/kasa`: XOR framing, request/response, unit normalisation, relay command.
- [ ] Unit tests: encrypt/decrypt round trip with a known vector; parsing of both unit
      formats using the fixtures captured in Phase 0.
- [ ] Integration tests with a fake Kasa TCP server (timeouts, malformed responses, oversize lengths).
- [ ] `internal/config`: file + environment overrides, validation, fail fast.
- [ ] `internal/poller`, `internal/state`, `internal/stream`: parallel polling, backoff,
      on-demand re-poll, SSE fan-out with heartbeat.
- [ ] `internal/metrics`: collector implementing the [metrics model](architecture.md#7-metrics-model).
- [ ] `internal/httpapi`: routes, validation, `/healthz`, `/readyz`, server timeouts.
- [ ] Graceful shutdown on `SIGTERM` (closes SSE streams, stops the poller).
- [ ] `web/`: dependency-free UI with in-place DOM updates and SVG sparklines.
- [ ] `internal/simulator`: realistic fake plugs (`KASA_SIMULATOR_PLUGS=3`).
- [ ] `Makefile` targets: `run`, `run-mock`, `test`, `lint`, `build`, `image`.
- [ ] `golangci-lint` configuration; tests run with `-race`.
- [ ] ADRs 0002, 0003, 0008, 0011 accepted.

**Exit criterion:** `make test lint` passes; `make run` shows live data from the real plugs
and toggling a plug works.

**You learn:** idiomatic Go service structure, concurrency, testing network code.

---

## Phase 4 — CI/CD and supply chain

**Goal:** every change is verified automatically; every release produces a signed image.

- [ ] `Dockerfile`: multi-stage, `-trimpath`, distroless `static:nonroot`, `USER 65532`,
      dependency download cached in its own layer.
- [ ] `.github/workflows/ci.yaml` (pull requests): lint, test with coverage, build, Trivy
      filesystem scan, Dockerfile lint (hadolint).
- [ ] `.github/workflows/release.yaml`: release-please; on tag, build multi-arch
      (`amd64`, `arm64`) image with Buildx, push to GHCR, generate SBOM (Syft),
      scan the image (Trivy), sign image and SBOM attestation with cosign (keyless OIDC).
- [ ] `renovate.json`: Go modules, GitHub Actions (pinned by SHA), base image digest.
- [ ] Branch protection on `main`: required checks, PR reviews.
- [ ] Pull request template and `CODEOWNERS`.

**Exit criterion:** merging the release PR produces `ghcr.io/<user>/kasa-energy-monitor:v0.1.0`;
`cosign verify` succeeds against it.

**You learn:** GitHub Actions, OCI images, SBOMs, keyless signing, automated releases.

---

## Phase 5 — Helm chart

**Goal:** the application is packaged and published like a third-party product.

- [ ] Chart in `deploy/helm/kasa-energy-monitor` with `values.schema.json`.
- [ ] Templates: Deployment, Service, ConfigMap, ServiceAccount, NetworkPolicy,
      ServiceMonitor, PrometheusRule, Grafana dashboard ConfigMap (each toggleable).
- [ ] Secure defaults: Pod Security `restricted` compliant, probes, resources.
- [ ] Chart README generated with helm-docs.
- [ ] `.github/workflows/chart.yaml`: `helm lint`, `chart-testing` install on a kind
      cluster with the simulator, publish to `oci://ghcr.io/<user>/charts` on release.
- [ ] ADR-0006 accepted.

**Exit criterion:** `helm install` from the OCI registry on a kind cluster yields a Ready pod
and a populated `/metrics` endpoint, verified in CI.

**You learn:** Helm templating, schema validation, chart testing, OCI artifacts.

---

## Phase 6 — Shadow deployment and cutover

**Goal:** replace the community exporter with evidence that the new one is correct.

- [ ] Add `apps/kasa-energy-monitor.yaml` in `homelab-gitops` (namespace `kasa`, real plugs).
- [ ] Run it **in parallel** with the community exporter for at least 3 days.
- [ ] Grafana comparison panel: power reported by both exporters for the same plug; the
      difference should stay near 0.
- [ ] Route `energy.example.com` through cloudflared to the new Service.
- [ ] Cutover PR: the new dashboard becomes the default; the community exporter
      Application and the public dashboard are removed.
- [ ] Renovate configured in `homelab-gitops` to propose image/chart version bumps.

**Exit criterion:** the community exporter is gone; a release of the application reaches the
cluster only through a merged Renovate PR.

**You learn:** progressive migration, verification with data, GitOps promotion flow.

---

## Phase 7 — Observability as code

**Goal:** dashboards, alerts and notifications are versioned and documented.

- [ ] Grafana dashboard JSON in the app repo, shipped through the chart:
  - Overview: total power, plugs online, cost per hour, energy today and this month.
  - Per plug: power, voltage, current, relay state.
  - Energy: daily kWh (last 30 days), monthly kWh, cost with a `$price_per_kwh` variable.
  - Health: poll duration, poll errors, scrape status.
- [ ] Alerts from [architecture.md § 13](architecture.md#13-observability-of-the-service-itself)
      as `PrometheusRule`, with unit tests using `promtool test rules`.
- [ ] Alertmanager route to ntfy or Telegram; the token stored as a SealedSecret.
- [ ] A runbook per alert in `docs/runbooks/`, linked through the `runbook_url` annotation.
- [ ] Optional: "appliance finished" notification (power below 5 W for 5 minutes after a
      period of high load).

**Exit criterion:** unplugging a plug produces a notification on the phone within ~6 minutes,
with a link to its runbook.

**You learn:** dashboards as code, alert design, alert testing, on-call documentation.

---

## Phase 8 — Hardening

**Goal:** defence in depth for everything exposed through the tunnel.

- [ ] Cloudflare Access applications and policies for both hostnames.
- [ ] Grafana JWT authentication from the `Cf-Access-Jwt-Assertion` header; local login disabled.
- [ ] Label namespaces with `pod-security.kubernetes.io/enforce: restricted` where possible.
- [ ] NetworkPolicies for `kasa` (and `monitoring` if the CNI supports it); verify that they are enforced.
- [ ] Verify image signatures at admission (optional: Kyverno or Sigstore policy-controller).
- [ ] Back-up and restore test: Sealed Secrets key, Prometheus volume snapshot.

**Exit criterion:** an unauthenticated request to either hostname never reaches the cluster;
a pod in another namespace cannot reach the application.

**You learn:** zero-trust access, Kubernetes security primitives, admission policies.

---

## Phase 9 — Portfolio polish

**Goal:** a reviewer understands the project in five minutes and can run it in fifteen.

- [ ] README: screenshots or a short GIF of the UI and the Grafana dashboard, CI badges,
      quick start, link to the architecture.
- [ ] `make demo`: kind cluster + kube-prometheus-stack + application with simulated plugs.
- [ ] Optional: public read-only demo (`readOnly: true`, simulated plugs) behind the tunnel.
- [ ] All ADRs in final status; `docs/architecture.md` reflects reality.
- [ ] Optional: a write-up of the migration from the manual setup to GitOps.

**Exit criterion:** someone without Kasa plugs runs `make demo` and sees a working dashboard.

---

## Suggested order and effort

| Phase | Depends on | Rough effort |
|---|---|---|
| 0 Inventory | — | 1 evening |
| 1 GitOps foundation | 0 | 1–2 evenings |
| 2 Adopt existing workloads | 1 | 2–3 evenings |
| 3 Application | 0 (fixtures) | 1–2 weekends |
| 4 CI/CD | 3 | 1 weekend |
| 5 Helm chart | 4 | 1 weekend |
| 6 Shadow + cutover | 2, 5 | 1 evening + 3 days of observation |
| 7 Observability as code | 6 | 1 weekend |
| 8 Hardening | 6 | 1–2 evenings |
| 9 Polish | all | 1 weekend |

Phases 1–2 (platform) and 3 (application) are independent and can be worked on in parallel.
