# Security Policy

## Scope

AeroBIM is maintained as an open-source engineering and research repository.

Security support is best effort for the active default branch and latest release line. Experimental snapshots and local forks are not guaranteed to receive fixes.

## Supported Surface

| Surface | Support |
| --- | --- |
| default branch (`main`) | best effort |
| latest release tag | supported for coordinated fixes |
| historical snapshots, local forks, generated artifacts | unsupported |

## Reporting a Vulnerability

Do not disclose exploitable details in public issues or pull requests.

Preferred channel:

1. GitHub private vulnerability reporting: https://github.com/KonkovDV/AeroBIM/security/advisories/new
2. If private reporting is temporarily unavailable, contact maintainers privately and delay public disclosure.

When reporting, include:

- affected component/path;
- minimal safe reproduction;
- impact scope;
- whether secrets or sensitive project data may be exposed.

## Response Targets

- acknowledgement within 5 business days;
- triage update within 14 calendar days;
- coordinated disclosure after fix or mitigation is available.

## In-Scope Areas

- CI/CD and workflow supply chain
- authentication and API boundary handling
- report export and persistence surfaces
- object storage adapters and optional Postgres index integration
- dependency and package security in backend/frontend pipelines

## Out of Scope

- vulnerabilities only present in downstream private forks
- social engineering and phishing not tied to this codebase
- incidents requiring access to third-party systems outside repository control

## Recommended Repository Controls

- private vulnerability reporting enabled
- secret scanning and push protection enabled
- code scanning (CodeQL or equivalent) enabled
- protected default branch with pull-request review gates

## Deployment Hardening (Wave 0–2 + RT-POST 2026-07-19)

- Non-`development`/`test` environments **require** `AEROBIM_API_BEARER_TOKEN` and/or OIDC (`AEROBIM_OIDC_ISSUER` + audience + JWKS) at startup and on every `/v1/*` call (503/401 fail-closed).
- Non-dev `AEROBIM_ENV` defaults `AEROBIM_SIGNOFF_PROFILE=production` (fail-closed clash / MEP / schema / unit_scale). Soft `AEROBIM_CLASH_AFFECTS_PASS=false` is ignored under pilot/production.
- OIDC JWT validation pins algorithms (RS256), verifies `iss`, `aud`, and `exp`; tenant claim only from `AEROBIM_OIDC_TENANT_CLAIM` (default `tenant_id`).
- Cross-tenant object ACL denials return **HTTP 404** (not 403).
- Outbound JWKS / buildingSMART Validation Service / OpenCDE fetches pass an SSRF URL allowlist guard.
- Storage path resolution rejects symlinks and path escapes under `AEROBIM_STORAGE_DIR`; ZIP members with `..` or absolute paths are rejected.
- IFC inputs larger than `AEROBIM_MAX_IFC_BYTES` (default 256 MiB) are rejected with HTTP 413.
- Optional validation engines publish `report.capabilities` so silent empty clash/IDS results cannot look like PASS.
- Upload responses omit storage `object_key` from client-visible JSON.
- Frontend may send `VITE_AEROBIM_API_BEARER_TOKEN` as `Authorization: Bearer …` for API and export downloads (BFF proxy still **NOT_IMPLEMENTED**).
- BCF API push uses OpenCDE Foundation Bearer tokens only; no proprietary hub protocol.
- HTML export uses `html.escape(..., quote=True)` for attribute contexts.
