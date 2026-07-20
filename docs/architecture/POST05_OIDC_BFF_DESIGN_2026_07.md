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

**Status:** **DESIGNED / NOT_IMPLEMENTED**

This document is the Wave A3 design spike only. It does **not** ship login/callback/logout
code, IdP registration, session store, or reverse-proxy cookie termination. Frontend and
API must keep reporting `auth_bff.status = NOT_IMPLEMENTED` until phases 2–3 land.

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
| **1** | Design + honesty surface (`auth_bff`, this doc, `GET /v1/auth/bff` → 501) | **THIS SPIKE** |
| **2** | Stub `/v1/auth/login` + callback + logout with CSRF `state` store (no production IdP) | NOT_IMPLEMENTED |
| **3** | Production reverse-proxy cookie session + IdP wiring + FE removal of any bearer inject | NOT_IMPLEMENTED |

## Honesty surface

Capabilities payload (`schema_version` ≥ 1.2.0):

```json
"auth_bff": {
  "status": "NOT_IMPLEMENTED",
  "design": "docs/architecture/POST05_OIDC_BFF_DESIGN_2026_07.md",
  "dev_proxy": "Vite loopback Authorization inject only"
}
```

Public probe: `GET /v1/auth/bff` returns the same JSON with **HTTP 501** (no bearer required)
so the frontend can discover the gap without treating absence as “auth ready”.

## Out of scope (this spike)

- Full IdP integration tests / Keycloak / Entra registration
- Real PKCE code exchange, refresh rotation, JWKS session binding
- Cookie session store implementation
- Changing `/v1/*` bearer `Depends` to cookie-only auth

## Acceptance for later phases

Phase 2 is “stub complete” only when login/callback/logout exist, state is bound, and
honesty still says NOT_IMPLEMENTED until phase 3 production cookie path is verified.
Phase 3 closes POST-05 when production FE never sees bearer tokens and checkpoint docs
flip `auth_bff` / POST-05 from DESIGNED/NOT_IMPLEMENTED to implemented with evidence.
