---
title: "POST-05 — OIDC Backend-for-Frontend (BFF) design spike"
status: DESIGNED / NOT_IMPLEMENTED
date: 2026-07-21
anchors:
  - "OAuth 2.0 for Browser-Based Apps (IETF draft-ietf-oauth-browser-based-apps)"
  - "RFC 8725 / oauth-rfc8725bis JWT/OIDC BCP"
  - "RFC 9700 OAuth 2.0 Security BCP (PKCE for confidential clients)"
---

# POST-05: OIDC BFF design (honesty spike)

**Status:** **DESIGNED / NOT_IMPLEMENTED** (Phase 2 CSRF stubs + Phase 2.5 PKCE landed; Phase 3 pending)

This document is the Wave A3 design spike. Phase 2 stub routes (`/v1/auth/login`,
`/v1/auth/callback`, `/v1/auth/logout`) ship CSRF state binding only — no IdP
registration, no production session cookie, and no reverse-proxy cookie termination.
Phase 2.5 adds PKCE S256 (`code_challenge` on login; verifier server-side) and an
optional IdP authorize URL *draft* when `AEROBIM_OIDC_BFF_CLIENT_ID` +
`AEROBIM_OIDC_BFF_AUTHORIZE_URL` are set — responses remain **HTTP 501**.
Frontend and API must keep reporting `auth_bff.status = NOT_IMPLEMENTED` until Phase 3.

## Problem

1. Browser SPAs must not hold long-lived OAuth access/refresh bearer tokens in
   `localStorage`, memory reachable by XSS, or Vite-baked env.
2. Today's Vite loopback proxy may inject `Authorization` for **127.0.0.1 development
   only**. That path is explicitly **not** a production auth model
   (`SECURITY.md`, RTATOM-F02/F01).
3. Production builds already require reverse-proxy / BFF auth; the missing piece is the
   concrete OIDC Authorization Code + PKCE → HttpOnly session cookie contract.

## Target architecture

```
Browser ──(opaque session cookie)──► BFF / reverse-proxy
                                      │
                                      ├─ Authorization Code + PKCE with IdP
                                      ├─ server-side token vault (access/refresh)
                                      └─ attaches bearer / service token → AeroBIM API
AeroBIM API validates session cookie (same-origin BFF) OR exchanged service token
```

Normative choices (Jul 2026 BCP):

| Concern | Decision |
|---|---|
| Grant | Authorization Code + **PKCE** (even if BFF is confidential — RFC 9700) |
| Browser secret | Opaque session id only; **HttpOnly**, **Secure**, **SameSite=Lax\|Strict**, prefer `__Host-` prefix |
| Token storage | Server-side (Redis/DB/memory); never returned to JS |
| CSRF | SameSite + double-submit / Origin checks on state-changing methods |
| API trust | Prefer same-site cookie session at BFF edge; optional short-lived service token exchange to `/v1/*` |
| Dev residual | Vite loopback Authorization inject remains **dev-only**; must not appear in production builds |

## Phases

| Phase | Scope | Status |
|---|---|---|
| **1** | Design + honesty surface (`auth_bff`, this doc, `GET /v1/auth/bff` → 501) | **DONE** |
| **2** | Stub `/v1/auth/login` + callback + logout with CSRF `state` store (no production IdP) | **STUBS LANDED** (`infrastructure/auth/oidc_bff_stubs.py`); `auth_bff.status` still **NOT_IMPLEMENTED** |
| **2.5** | PKCE S256 on login + optional lab authorize URL draft (`AEROBIM_OIDC_BFF_*`) | **LANDED 2026-08-11** — still HTTP 501 / NOT_IMPLEMENTED |
| **3** | Production reverse-proxy cookie session + IdP code exchange + FE removal of any bearer inject | NOT_IMPLEMENTED |

## Honesty surface

Capabilities payload (`schema_version` ≥ 1.2.0):

```json
"auth_bff": {
  "status": "NOT_IMPLEMENTED",
  "design": "docs/architecture/POST05_OIDC_BFF_DESIGN_2026_07.md",
  "dev_proxy": "Vite loopback Authorization inject only",
  "phase_2_stubs": "login/callback/logout with CSRF state (no production session)",
  "phase_2_5_pkce": "S256 code_challenge; optional IdP URL draft via AEROBIM_OIDC_BFF_* — still 501",
  "phase_3_pending": "HttpOnly session cookie + IdP code exchange + FE bearer removal"
}
```

Public probe: `GET /v1/auth/bff` returns the same JSON with **HTTP 501** (no bearer required)
so the frontend can discover the gap without treating absence as “auth ready”.

## Out of scope (Phase 2 stubs)

- Full IdP integration tests / Keycloak / Entra registration
- Real PKCE code exchange, refresh rotation, JWKS session binding
- Production HttpOnly session cookie store
- Changing `/v1/*` bearer `Depends` to cookie-only auth

Phase 2 routes (all **501** except CSRF reject **400**):

- `GET /v1/auth/login` — issues one-time `state`
- `GET /v1/auth/callback?state=…` — validates state; no session cookie
- `POST /v1/auth/logout` — clears in-memory CSRF store only

## Acceptance for later phases

Phase 2 is “stub complete” only when login/callback/logout exist, state is bound, and
honesty still says NOT_IMPLEMENTED until phase 3 production cookie path is verified.
Phase 3 closes POST-05 when production FE never sees bearer tokens and checkpoint docs
flip `auth_bff` / POST-05 from DESIGNED/NOT_IMPLEMENTED to implemented with evidence.
