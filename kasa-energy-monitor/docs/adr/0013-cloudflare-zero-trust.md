# 0013. Cloudflare Zero Trust for access and identity

- **Status:** Proposed
- **Date:** 2026-11-24

## Context

Everything published through the tunnel is reachable from the internet. The UI can switch
real devices on and off, and Grafana shows the household's consumption patterns. Running an
identity provider in the homelab only for this would add more to operate than it protects.

## Decision

- Make every public hostname a self-hosted **Cloudflare Access application** with an Allow
  policy for the owner's identity only (One-time PIN first, GitHub or Google login later).
- Use the signed JWT that Access adds in `Cf-Access-Jwt-Assertion`:
  - Grafana trusts it through `[auth.jwt]` for single sign-on; the login form is disabled.
  - kasa-energy-monitor verifies it (signature, `aud`, `iss`, expiry) on the relay
    endpoint and records the user's e-mail in the audit log.
- Allow ingress to the UI port only from `cloudflared` with a NetworkPolicy, so no request
  can reach the application without passing Access.

## Consequences

- Identity is checked at Cloudflare's edge, before any traffic reaches the home network.
- No passwords to manage in the applications; one login covers both hostnames.
- Every relay change is attributable to a person.
- Stronger coupling to Cloudflare: moving away means introducing an identity-aware proxy.
- Automated clients (an uptime check, a demo) need a service token or a Bypass policy.

## Alternatives considered

- **oauth2-proxy with GitHub or Google** — portable, but one more component per hostname to
  run and secure.
- **Basic auth in each application** — weak, and duplicated in every service.
- **VPN only (WireGuard or Tailscale)** — strong, but the project could not be shown from an
  arbitrary device without installing a client.
