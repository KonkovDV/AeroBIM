<!-- claims-lint: allow-file reason="In-repo KT#3 workplan; 25.08 caps/cloud as non-claims; NO_GO; RT stay OPEN" -->
---
title: "In-repo workplan after 25.08 customer answers"
date: "2026-08-27"
last_updated: "2026-08-28"
status: active
version: "1.2.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Repo work split after the 25.08 questionnaire. Channel received is not a
  hashed pack in git. Not product accuracy. Not customer SLA. Not native
  RVT/NWD. Not OIDC BFF live. Not LIRA solver. Streaming IFC not shipped.
  Checkpoint NO_GO.
---

# In-repo workplan (after 25.08 answers)

Customer answers 25.08 named formats, size caps, HTTPS/closed storage, LIRA **compare**, remark shape, two roles. That **does not** close RT-001/002b/003.

**Speech:** do not say «нет данных заказчика». Say: channel received; hashed pack **not** in git; machine intake status stays `BLOCKED_NO_CUSTOMER_DATA` (meaning git pack absent).

Owner-machine inventory (byte counts, file-type shares, pack hashes) stays **outside** this tree.

## Already in `main` (do not re-sell as a plan)

| Item | Where |
|---|---|
| Native RVT/NWD/DWG fail-closed | `validate_native_autodesk_toolchain`; upload/analyze/ZIP members |
| Ingest caps 500 MB office / 1.5 GB model | `SAMOLET_STATED_*`; analyze/WASM stay **256 MiB** |
| LIRA = compare, not solver | `calculation_compare`; `native_lir=not_implemented` |
| xlsx/docx declared-field compare | `compare_declared_tables` + office adapter; PDF fragile; `.lir` closed |
| HTTP `.lir`/`.spr` honesty 415 | `NATIVE_LIRA_CLOSED_REASON`; ZIP members after zip-bomb inspect |
| IFC streaming / disk R-tree **design** | `streaming_design_snapshot`; parser not implemented; cap unchanged |
| Spatial index JSON sidecar | dump of in-memory `IfcSpatialIndex`; not disk R-tree; not analyze |
| Remark essence + clause + storey/axis | Storey from `IfcBuildingStorey`; axis = `IfcGridAxis.AxisTag` only — **not** nearest grid intersection |
| Two role aliases | `expert` HITL; `user` viewer |
| HTTPS required flag | `https_required` on capabilities payload |
| OIDC BFF | `auth_bff=NOT_IMPLEMENTED` (default 501) |
| Speech/docs parity with 25.08 | Jury/tracker cards forbid «нет данных»; cloud ask ≠ OIDC live |

## In-repo next (this tree)

| Pri | Task | Done when | Forbidden |
|---|---|---|---|
| 0 | Keep CI green; commit **CI-attested** runtime pin only | typecheck + pytest + frontend vitest + `attested_by=ci` artifact | Minting a runtime pin from local pytest |
| 2 | Unsigned SP 63/20 **template** only if needed | `closes_rt002: false`; not `customer_approved` | Relabel as RT-002b CLOSED |
| 4 | Implement streaming IFC / disk R-tree | Parser + RSS measurement; default cap still 256 MiB until measured | Silent raise of `AEROBIM_MAX_IFC_BYTES` |
| 5 | Browser OIDC BFF | Explicit 501 until implemented | Demo login as production SSO |

## Owner-only (not git)

Hashed inventory of the customer channel; dual raters; Samolet signature on an acceptance profile; federated MEP IFC for RT-003; written data-handling order; catalog questionnaire / legal entity.

## KT#3 still FAILED (say so)

Native RVT/NWD/DWG, calculation **correctness**, signed Samolet profile, CDE import T2, product accuracy >90% on their packs.
