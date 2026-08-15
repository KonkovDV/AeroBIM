<!-- claims-lint: allow-file reason="Engineering readiness pack documenting OPEN customer blockers without product GO claims" -->
---
title: "RT-001/002/003 + ODA/MEP/OIDC — engineering readiness pack"
date: "2026-08-11"
claim_boundary: "Eng readiness only. Checkpoint remains NO_GO. No customer corpus invented."
---

# Customer blockers — engineering pack (2026-08-11)

**Checkpoint:** still **`NO_GO`**. This pack advances eng scaffolding and honesty locks.
It does **not** close RT-001 / RT-002 / RT-003, native DWG, or production OIDC BFF.

Authority: [`audit/reports/CRITICAL_BLOCKERS.md`](../../audit/reports/CRITICAL_BLOCKERS.md).

## Status board

| ID | Product status | Eng status (2026-08-11) | Closes with |
|---|---|---|---|
| **RT-001** | OPEN | Protocol + publishable gates + honesty lock tests | Customer corpus + ≥2 adjudicators + κ/α + held-out + FN |
| **RT-002** | OPEN | Schema↔loader full `approval` object; synthetic promotion blocked | Signed customer pack + matching `pack_hash` |
| **RT-003** / MEP-CLASH-001 | OPEN | Domain+DI fail-closed; ENG_FIXTURE rehearsal; never `mep_system_clash=OK` | Federated customer IFC + signed scope memo + matrix + verified geometry |
| **STUB-ODA-CAD-001** | OPEN | Legal flag vs SDK honesty split; analyze uses ezdxf only | Licensed ODA/Teigha + legal review + customer DWG evidence |
| **POST-05 OIDC BFF** | NOT_IMPLEMENTED | Phase 2.5 CSRF + PKCE; Phase 3 lab cookie + nonce + HMAC when `oidc_bff_phase3_ready`; default HTTP **501** | Production IdP + JWKS identity + FE bearer removal |

## RT-001 intake (do next with customer)

1. Freeze labels schema — [`docs/quality/RT001_LABELING_PROTOCOL_RT026_2026_08_03.md`](../quality/RT001_LABELING_PROTOCOL_RT026_2026_08_03.md)
2. Fill templates under `samples/benchmarks/detection-precision/`
3. Run `python -m aerobim.tools.build_detection_labels` + `measure_adjudicator_agreement`
4. Gate: `precision_claim_publishable_with_agreement` only with `corpus_kind=customer`

## RT-002 intake

1. Customer pack with full `approval` object (not `approval_ref` alone)
2. Immutable version store + content hash
3. Loader already fail-closed — see `json_norm_rule_pack_loader.py`

## RT-003 / MEP intake

1. Federated IFC paths + signed memo (`samples/mep/federated-scope-template.json`)
2. Clearance matrix from customer (`clearance-matrix-template.json` is template only)
3. ENG_FIXTURE path (`federated-scope-verified-fixture.json`) proves honesty — capability stays `NOT_VERIFIED`

## ODA (STUB-ODA-CAD-001)

| Flag | Behavior |
|---|---|
| `AEROBIM_ODA_CAD_ENABLED=false` | `native DWG parser is not implemented` |
| `=true` without SDK | `NATIVE_DWG_ODA_ENABLED_NO_SDK_REASON` — legal gate open ≠ product |
| Analyze path | Always `EzdxfCadModelIngestor` via `CAD_MODEL_INGESTOR` |

## OIDC BFF Phase 2.5 / Phase 3 lab

Default (no lab env): **501** / `auth_bff.status=NOT_IMPLEMENTED`.

```text
AEROBIM_OIDC_BFF_CLIENT_ID=...
AEROBIM_OIDC_BFF_AUTHORIZE_URL=https://idp/.../authorize
AEROBIM_OIDC_BFF_REDIRECT_URI_ALLOWLIST=https://app.example/callback
AEROBIM_OIDC_BFF_TOKEN_URL=https://idp/.../token
AEROBIM_OIDC_BFF_CLIENT_SECRET=...
AEROBIM_OIDC_BFF_COOKIE_SECRET=...
```

`GET /v1/auth/login` issues `state` + PKCE `code_challenge` (S256) + OIDC `nonce`; `code_verifier` stays server-side.
Phase 3 lab (all of the above set) issues an HMAC-bound HttpOnly cookie after code exchange via `safe_urlopen`.
Without JWKS, `identity_verified=false`. This is **not** production SSO and does **not** bypass `require_bearer_auth` on `/v1/*`.

## Honesty lock tests

`backend/tests/test_rt_customer_blocker_honesty_lock.py` — fixture precision not publishable;
MEP/DWG contracts never OK; auth_bff NOT_IMPLEMENTED; analyze CAD ≠ ODA.

## Forbidden

- Marking Checkpoint GO / RT-001–003 CLOSED without customer evidence
- Inventing federated MEP / customer norm pack / precision corpus
- Claiming native DWG or production SSO from stubs / Phase 2.5 / Phase 3 lab cookies
