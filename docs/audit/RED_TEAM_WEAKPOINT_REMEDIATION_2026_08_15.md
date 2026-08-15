<!-- claims-lint: allow-file reason="Red Team audit evidence; documents OPEN residuals without Checkpoint GO" -->
---
title: "Red Team audit — weak-point remediation (2026-08-15)"
claim_boundary: "Eng findings only. Checkpoint NO_GO unchanged."
---

# Red Team audit + remediation (2026-08-15)

## Scope

Uncommitted weak-point remediation: IfcClash tiny-wall skip, native DWG honesty, use-case/DI/CLI split, OIDC BFF Phase 3 lab path, BCF T2 tooling (STATUS stays `NOT_VERIFIED`).

Independent security-review of the diff: **no Critical/High**. Honesty surfaces unchanged (`auth_bff` default `NOT_IMPLEMENTED`, `dwg_native=NOT_IMPLEMENTED`, BCF T2 `claim_allowed: false`). `/v1/auth/session` is not an API bearer bypass (`require_bearer_auth` ignores BFF cookies). Session IDs are server-generated.

## Findings closed this pass

| Sev | Finding | Fix |
|---|---|---|
| MED | Unguarded token exchange (`urllib.request.urlopen`) — SSRF + outbound-guard CI fail | `safe_urlopen`; boot SSRF on `AEROBIM_OIDC_BFF_TOKEN_URL`; adapter listed in outbound invariant |
| MED | Unverified JWT `sub`/`email` bound into lab session | JWKS `OidcTokenValidator` when registered; else `identity_verified: false` |
| MED | Callback used stored `redirect_uri` without re-check | Exact allowlist match required before token exchange |
| MED | Unsigned JWT nonce not bound to CSRF `state` | Login issues `nonce`; callback requires `id_token.nonce` match |
| MED | Opaque session id in cookie without integrity | HMAC-SHA256 (`session_id.hexdigest`) via `AEROBIM_OIDC_BFF_COOKIE_SECRET` |
| LOW | GET `/v1/auth/login\|callback` unbounded | Same per-client budget as analyze POSTs when `AEROBIM_HTTP_RATE_LIMIT_PER_MINUTE>0` |

## Still OPEN (by design)

- RT-001 / RT-002 / RT-003 Checkpoint **NO_GO** (customer evidence)
- STUB-ODA-CAD-001 / MEP-CLASH-001 / OIDC production IdP
- BCF T2 CDE import `NOT_VERIFIED` (`claim_allowed: false`)
- Lab mock IdP without JWKS: session exists, `identity_verified=false`
- Partial IfcClash skip: capability can stay OK while tiny products are omitted (all-skipped still fail-closed)
- Lab session cookie HMAC + nonce bind + GET auth rate-limit (this pass) do **not** make `auth_bff` production

## Honesty

No flip of `summary.passed`, `auth_bff=implemented`, `mep_system_clash=OK`, `dwg_dxf=OK`, or BCF T2 `VERIFIED`.
