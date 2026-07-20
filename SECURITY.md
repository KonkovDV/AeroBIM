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

## Deployment Hardening (Wave 0–2 + RT-POST 2026-07-19 + RTATOM A1/A2/A3 2026-07-20)

- Non-`development`/`test` environments **require** `AEROBIM_API_BEARER_TOKEN` and/or OIDC (`AEROBIM_OIDC_ISSUER` + audience + JWKS) at startup and on every `/v1/*` call (503/401 fail-closed).
- Local `docker-compose.yml` defaults to **development**, publishes **127.0.0.1:8080 only**, and keeps `AEROBIM_ALLOW_ANONYMOUS_DEV=false` unless explicitly opted in. Shared/LAN use `docker-compose.production.yml` which **requires** `AEROBIM_API_BEARER_TOKEN` with no default.
- Non-dev `AEROBIM_ENV` rejects soft `AEROBIM_SIGNOFF_PROFILE=development|fixture` (must be `production` or `samolet_pilot`).
- OIDC JWKS is fetched only via SSRF-guarded `safe_urlopen` (no unguarded `PyJWKClient` HTTP).
- OIDC JWKS hostname must match issuer hostname unless listed in `AEROBIM_OIDC_JWKS_EXTRA_HOSTS` (multi-host IdP allowlist).
- Frontend never embeds bearer tokens; Vite loopback proxy may inject `Authorization` in dev only. Production builds require reverse-proxy / BFF auth (POST-05 still **NOT_IMPLEMENTED**).
- Non-dev `AEROBIM_ENV` defaults `AEROBIM_SIGNOFF_PROFILE=production` (fail-closed clash / MEP / schema / unit_scale). Soft `AEROBIM_CLASH_AFFECTS_PASS=false` is ignored under pilot/production.
- OIDC JWT validation pins algorithms (RS256), verifies `iss`, `aud`, and `exp`; tenant claim only from `AEROBIM_OIDC_TENANT_CLAIM` (default `tenant_id`).
- Cross-tenant object ACL denials return **HTTP 404** (not 403).
- Outbound JWKS / buildingSMART Validation Service / OpenCDE fetches pass an SSRF URL allowlist guard; DNS is resolved once and connections are IP-pinned; non-global addresses (incl. CGNAT `100.64/10`) are blocked.
- Redis (`AEROBIM_REDIS_URL`) and Postgres (`AEROBIM_DB_URL`) are SSRF-gated at settings load when not localhost / unix socket; Postgres→FS fallback is fail-closed under `audit_fail_closed` / hard profiles.
- Tenant-scoped filesystem artifact reads assert `tenants/{encoded}/` prefix; `safe_storage_token` / path jail apply **NFKC** before encode/jail; encodes `/\_:` to avoid prefix collisions.
- HITL transitions use server event-store SSOT for `previous_state`; norm-pack actors bind to authenticated subject.
- Committed reports carry content hash; get denies tampered JSON. Cancelled analyze jobs discard report artifacts.
- Soft sign-off `summary.passed=true` stamps `authoritative=false` (not a Shared→Published production verdict). Hard profiles force cross-doc ERROR and OpenRebar provenance enforcement.
- List `/v1/reports` always filters by principal `tenant_id` when set (even with ACL soft-off).
- Upload quota `reserve` is rolled back on promote/object-store failure; hard profiles bake default daily upload quotas when unset.
- OIDC JWTs without `kid` are rejected; JWKS key selection requires a matching `kid` (and `use=sig` when advertised).
- OIDC principals must carry a non-empty tenant claim — never fall back to `AEROBIM_API_TENANT_ID`.
- OpenAPI `/docs`/`/redoc`/`/openapi.json` are disabled outside development/test.
- CORS request headers are allowlisted (`Authorization`, `Content-Type`, `Idempotency-Key`, `X-Request-ID`, `Accept`); `*` origins rejected outside development.
- HTTP responses set `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `X-Frame-Options: DENY`, and an API-safe CSP (`default-src 'none'`…); HTML export uses a slightly relaxed CSP (`style-src 'unsafe-inline'; img-src data:`).
- Production compose publishes `127.0.0.1:8080` only; LAN exposure requires a reverse proxy.
- Soft `development`/`fixture` sign-off profiles cannot weaken pilot/production capability gates; evidence-bundle PASS claims are evaluated under production policy.
- Backend image base is digest-pinned (`python:3.12-slim@sha256:…`); CI/Docker install from hashed locks via `pip install --require-hashes` (pip/uv bootstrap pin residual only).
- PDF raster/preview uses PyMuPDF on authenticated uploads — keep patched; treat untrusted PDF rendering as residual host risk (sandbox not yet shipped).
- Storage path resolution rejects symlinks and path escapes under `AEROBIM_STORAGE_DIR`; report JSON reads use `open_storage_file` (POSIX `O_NOFOLLOW` when available). ZIP path inspect streams via `ZipFile(path)` without `read_bytes`; members with `..` or absolute paths are rejected (including BCF consumers via `inspect_zip_bytes`).
- IFC inputs larger than `AEROBIM_MAX_IFC_BYTES` (default 256 MiB) are rejected with HTTP 413; frontend WASM IFC memory is capped at 256 MiB.
- Optional validation engines publish `report.capabilities` so silent empty clash/IDS results cannot look like PASS.
- Upload responses omit storage `object_key` from client-visible JSON.
- Drawing preview responses use an allowlisted Content-Type; client Blob creation mirrors that allowlist.
- BCF API push uses OpenCDE Foundation Bearer tokens only; no proprietary hub protocol.
- HTML export uses `html.escape(..., quote=True)` for attribute contexts.
