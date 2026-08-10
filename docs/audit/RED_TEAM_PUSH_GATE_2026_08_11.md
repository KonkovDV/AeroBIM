<!-- claims-lint: allow-file reason="Red Team audit evidence; documents OPEN residuals without Checkpoint GO" -->
---
title: "Red Team audit — 2026-08-11 (push gate)"
claim_boundary: "Eng findings only. Checkpoint NO_GO unchanged."
---

# Red Team audit + remediation (2026-08-11)

## Suite

Pre-fix: `1 failed` (OpenAPI snapshot drift from Phase 2.5 `auth_bff` fields) / 2054 passed.  
Post-fix: regenerate snapshot + close HIGH/MEDIUM residuals below.

## Findings closed this pass

| Sev | Finding | Fix |
|---|---|---|
| P0 | OpenAPI snapshot drift | `AEROBIM_UPDATE_OPENAPI_SNAPSHOT=1` |
| HIGH | Norm-pack index/object keys allowed `:` (NTFS ADS) | `safe_storage_token` in `object_store_norm_pack_version_store` |
| HIGH | `LocalObjectStore` accepted `:` keys | reject in `_normalise_key` |
| HIGH | Yandex+kimi refuse bypass via IP host | provider=yandex + unknown/IP host → refuse; explicit non-Yandex markers exempt |
| MED | OIDC lab open `redirect_uri` | `AEROBIM_OIDC_BFF_REDIRECT_URI_ALLOWLIST` exact match required for `idp_redirect_url` |

## Still OPEN (by design)

- RT-001 / RT-002 / RT-003 Checkpoint **NO_GO** (customer evidence)
- STUB-ODA-CAD-001 / MEP-CLASH-001 / OIDC Phase 3
- Uncommitted local IFC release benchmark timings (left dirty; fixture_only)

## Honesty

No flip of `summary.passed`, `auth_bff=implemented`, `mep_system_clash=OK`, or `dwg_dxf=OK`.
