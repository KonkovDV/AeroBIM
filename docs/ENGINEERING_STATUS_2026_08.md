---
title: "AeroBIM Engineering Status — August 2026"
status: active
version: "1.1.0"
last_updated: "2026-08-02"
claim_boundary: "Engineering readiness only. Checkpoint NO_GO until RT-001/002/003. Fixture != customer."
---

# Engineering Status — 2026-08-02

**HEAD (docs refresh):** regenerate via `export_runtime_baseline` (see evidence artifact)  
**last_updated:** 2026-08-02  
**Checkpoint:** **`NO_GO`** — RT-001 / RT-002 / RT-003 remain OPEN  
**Claims SSOT:** [`../audit/reports/CLAIMS_LOCK_2026_07_17.md`](../audit/reports/CLAIMS_LOCK_2026_07_17.md) · dated freeze [`../audit/reports/CLAIMS_LOCK_2026_07_31.md`](../audit/reports/CLAIMS_LOCK_2026_07_31.md)

## What improved (engineering — not customer GO)

| Track | Eng status | Customer |
|---|---|---|
| **WP-03 signature envelope** | Detached `.sig.json` presence/hash/roles; `qualified_signature` ENG_PARTIAL; trust_chain always NOT_VERIFIED | Never «УКЭП проверена» |
| **WP-02 Hybrid advisory pre-gate** | `HybridRouteGate` mandatory before advisory observations; blocked → no findings; egress bytes on audit | Not verdict path; Checkpoint NO_GO |
| **WP-01 runtime baseline** | Schema 1.2.0: passed/skipped/failed + gates + env fingerprint; CI `--check-complete` | Not Checkpoint GO |
| **LIC-001 Option B** | Core PDF = `pypdfium2` + `pdfminer.six`; PyMuPDF optional `pdf-agpl` only | Not a legal opinion |
| **Extraction integrity** | OCR-aware signals when `raster` present; FAIL blocks pass | Not product render-vs-extract |
| **Public IFC corpus** | CC BY 4.0 buildingSMART samples under `samples/ifc/public/` | Not customer corpus (RT-001) |
| **P2-04 Annotation↔IFC** | Claimed GUID → `ifc_guid` only after spatial-index presence | Not human-adjudicated matching |
| **P2-02 MEP honesty** | `edge_kinds` (`co_presence`/`connects`) + optional AABB broadphase | RT-003 OPEN; never `mep_system_clash=OK` |
| **Offline** | Docker image-track smoke; bare-metal **DEFERRED** (owner) | Not “any air-gap without Docker” |
| **Checkpoint #2 pin** | Wall-guid evidence bundle pin | Live CDE T2 still NOT_VERIFIED |

## Plan / gap docs

| Doc | Role |
|---|---|
| [`roadmap/P2_02_GEOMETRY_HONESTY_PLAN_2026_08.md`](roadmap/P2_02_GEOMETRY_HONESTY_PLAN_2026_08.md) | Geometry honesty deepen plan + research anchors |
| [`roadmap/MEP_SYSTEM_CLASH_GAP_2026_07.md`](roadmap/MEP_SYSTEM_CLASH_GAP_2026_07.md) | MEP-CLASH-001 gap (updated 2026-08-01) |
| [`offline-deployment-2026.md`](offline-deployment-2026.md) | Docker offline VERIFIED; bare-metal deferred |
| [`license-policy-2026.md`](license-policy-2026.md) | LIC-001 Option B |
| [`extraction-integrity-2026.md`](extraction-integrity-2026.md) | EI signals + OCR PARTIAL |
| [`quality/CUSTOMER_PILOT_BACKLOG_2026_07_21.md`](quality/CUSTOMER_PILOT_BACKLOG_2026_07_21.md) | P2 backlog statuses |
| [`evidence/checkpoint2-evidence-bundle-latest.json`](evidence/checkpoint2-evidence-bundle-latest.json) | Fixture GO pin |

## Forbidden (unchanged)

Product accuracy >90%; customer SLA ≤30 min; native DWG; MEP delivered / `mep_system_clash=OK`; CDE_READY BCF; independent calc correctness; MIT-without-disclosure; bare-metal offline-ready; AABB/connects = verified geometric clash.

## Reproduce wall-guid demo

```bash
cd backend
python -m aerobim.tools.export_evidence_bundle \
  --pack ../samples/benchmarks/project-package-wall-guid-demo.json \
  --output ../artifacts/evidence-bundle/checkpoint2-wall-guid
```
