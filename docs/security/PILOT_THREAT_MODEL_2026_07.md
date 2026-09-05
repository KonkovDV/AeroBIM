<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
---
title: "Pilot threat model (Samolet) — 2026-07"
status: active
date: 2026-07-21
last_updated: "2026-09-05"
claim_boundary: "Does not claim SSO production-ready. Checkpoint GO (regulatory_measurement_mvp); customer_go false unchanged."
---

# Pilot Threat Model (2026-07)

Engineering summary of closed RTATOM / RT-POST controls and the residual BFF gap.
This is **not** a customer penetration-test report and does **not** claim SSO
production-ready.

## Scope

| In scope | Out of scope (explicit) |
|---|---|
| Local/API abuse of AeroBIM pilot surface | Full org SSO rollout |
| Upload / path / SSRF / ACL honesty | Third-party CDE product security |
| Auth bearer / principal binding (current) | Production OIDC BFF session cookie (POST-05) |
| Evidence HTML / ZIP / XML / S3 get caps | Invented customer corpus |

## Closed control clusters (RTATOM + RT-POST)

| Cluster | Examples closed | Evidence anchors |
|---|---|---|
| **A1 tenant / ACL** | FS IFC/drawing tenant prefix; list reports tenant-scoped; cross-tenant → 404 | `CRITICAL_BLOCKERS` RTATOM-H01/H02/H03; RT-POST-02 |
| **A1 HITL / norms** | `previous_state` SSOT; `proposed_by` bound to principal | RTATOM-H04/I06/H05/I07; HITL tests |
| **A1 integrity** | Report content hash; cancel tombstone; hard clash policy gate | RTATOM-G11/G03/G01 |
| **A2.5 supply chain** | `--require-hashes` / pinned pip+uv | RTATOM A2.5 CLOSED* |
| **A3 hygiene** | CSP/nosniff/Referrer/XFO; NFKC tokens; JWKS↔issuer bind; ZIP/XML/S3 caps | RTATOM A3 CLOSED* |
| **RT-POST outbound** | SSRF guard on JWKS / bSI / OpenCDE | RT-POST-03 |
| **RT-POST uploads** | Magic/extension mismatch; `object_key` omitted; ZIP `..` reject | RT-POST-08/11 + upload tests |

## Residual — POST-05 BFF

| Item | Status |
|---|---|
| OIDC Authorization Code + PKCE BFF with HttpOnly session cookie | **DESIGNED / NOT_IMPLEMENTED** (Phase 3 lab-only; default 501) |
| Design spike | POST-05 OIDC BFF — **NOT_IMPLEMENTED** (this threat model) |
| Public honesty | `GET /v1/auth/bff` → 501; capabilities `auth_bff.status=NOT_IMPLEMENTED` |
| Dev-only | Vite loopback may inject `Authorization` — **not** production SSO |
| Token endpoint body cap | Lab exchange uses `read_http_response_capped` (1 MiB), same class as JWKS. Not SSO. |

Do **not** claim SSO / production auth until POST-05 has a production IdP, JWKS-verified identity, and FE bearer removal. Phase 3 lab cookies are not that close.

## Negative security tests (inventory)

Prefer these over narrative claims:

- `backend/tests/test_api_security.py` — traversal, 401/404, boundary rejects
- `backend/tests/test_rt_phase4_security.py` — null-byte / UNC / control chars
- `backend/tests/test_upload_content_security.py` — magic/extension mismatch
- `backend/tests/test_rt_remediation_post.py` — ACL 404 / SSRF / sign-off
- `backend/tests/test_rtatom_remediation_2026_07_20.py` — HITL forge → 400, tenant/hash honesty
- `backend/tests/test_rtatom_wave_a3_2026_07_20.py` — A3 hygiene

## Checkpoint

Product Checkpoint is **`GO`** (`regulatory_measurement_mvp`). `customer_go` stays
**false**. Residual volumes (RT-001b dual human raters, RT-001c customer corpus,
RT-002c Samolet signature, RT-003c system MEP, CDE T2) are not closed by
engineering controls in this document. Security readiness ≠ customer sign-off.
Do not write undifferentiated «RT-001/002/003 CLOSED».
