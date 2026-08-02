---
title: "AeroBIM Engineering Status — August 2026"
status: active
version: "1.5.0"
last_updated: "2026-08-03"
claim_boundary: "Engineering readiness only. Checkpoint NO_GO until RT-001/002/003. Fixture != customer."
---

# Engineering Status — 2026-08-03

**HEAD (docs refresh):** see [`evidence/runtime-baseline-latest.json`](evidence/runtime-baseline-latest.json)  
**last_updated:** 2026-08-03  
**Checkpoint:** **`NO_GO`** — RT-001 / RT-002 / RT-003 remain OPEN  
**Claims SSOT:** [`../audit/reports/CLAIMS_LOCK_2026_07_17.md`](../audit/reports/CLAIMS_LOCK_2026_07_17.md) · dated freeze [`../audit/reports/CLAIMS_LOCK_2026_07_31.md`](../audit/reports/CLAIMS_LOCK_2026_07_31.md)  
**P0 Red Team:** [`quality/RED_TEAM_P0_ROLLUP_2026_08_02.md`](quality/RED_TEAM_P0_ROLLUP_2026_08_02.md)  
**Residuals Red Team:** [`quality/RED_TEAM_ENG_RESIDUALS_2026_08_03.md`](quality/RED_TEAM_ENG_RESIDUALS_2026_08_03.md)

## What improved (engineering — not customer GO)

| Track | Eng status | Customer |
|---|---|---|
| **Eng residuals wave** | VLM smoke gate; signature deepen; OIDC Phase 2 stubs; BCF T2 checklist; DWG native fail-closed; BSI IDS n=290 CC BY-ND; bare-metal wheelhouse DEFERRED | Checkpoint NO_GO unchanged |
| **Open corpora + BSI IDS** | Fixture regression n=7 + BSI TestCases profile `regression-bsi` **honest_case_count=290** (CC BY-ND unmodified) | Regression only — not product accuracy |
| **WP-07 quality protocol** | Protocol doc + `compute_quality_protocol_stats` (Wilson P/R + sample-size planner); nDCG via existing `evaluate_ranking_quality`; interim target 0.60 | Not adjudicated customer precision; never >90% |
| **WP-06 open corpora** | Profiles under `samples/benchmarks/open-corpora/`; CI smoke pins | Regression/timing only — no expert TP/FP |
| **WP-05 package completeness** | Declared inventory: mandatory PD sections, format honesty (no native DWG), cipher/specs/schedules, PD↔RD pairing; soft opt-in via request flag | Fixture-grade only; not PP-87 / customer intake |
| **WP-04 norm pack v2** | Schema 2.0.0 RASE + `execution_mode` + expert confirmation journal; loader fail-closed without `customer_approved`+approval; `list_expert_required_norm_rules` | RT-002 OPEN; fixture ≠ customer pack |
| **WP-03 signature envelope** | Presence/hash/roles + signature_alg/value presence + optional package hash bind; trust_chain always NOT_VERIFIED | Never «УКЭП проверена»; crypto adapter missing |
| **WP-02 Hybrid advisory pre-gate** | Gate on Analyze advisory + kimi smoke PUBLIC egress | Not verdict path; Checkpoint NO_GO |
| **WP-01 runtime baseline** | Schema 1.2.0: passed/skipped/failed + gates + env fingerprint; CI `--check-complete` | Not Checkpoint GO |
| **OIDC BFF POST-05** | Phase 2 stubs (login/callback/logout + CSRF); `auth_bff` stays NOT_IMPLEMENTED | Phase 3 needs IdP |
| **BCF T2** | Verifier `--checklist` dry-run; pack STATUS stays NOT_VERIFIED | Needs real CDE log/screenshot/hashes |
| **LIC-001 Option B** | Core PDF = `pypdfium2` + `pdfminer.six`; PyMuPDF optional `pdf-agpl` only | Not a legal opinion |
| **P2-04 Annotation↔IFC** | Claimed GUID → `ifc_guid` only after spatial-index presence | Not human-adjudicated matching |
| **P2-02 MEP honesty** | `edge_kinds` + optional AABB broadphase | RT-003 OPEN; never `mep_system_clash=OK` |
| **Offline** | Docker image-track smoke; bare-metal **DEFERRED** (`offline_bundle wheelhouse` exits 2) | Not “any air-gap without Docker” |
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
| [`pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md`](pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md) | WP-07 quality measurement protocol |
| [`../samples/benchmarks/open-corpora/README.md`](../samples/benchmarks/open-corpora/README.md) | WP-06 open corpora profiles |
| [`quality/RED_TEAM_P0_ROLLUP_2026_08_02.md`](quality/RED_TEAM_P0_ROLLUP_2026_08_02.md) | P0 self Red Team rollup |
| [`evidence/checkpoint2-evidence-bundle-latest.json`](evidence/checkpoint2-evidence-bundle-latest.json) | Fixture GO pin |

## Forbidden (unchanged)

Product accuracy >90%; customer SLA ≤30 min; native DWG; MEP delivered / `mep_system_clash=OK`; CDE_READY BCF; independent calc correctness; MIT-without-disclosure; bare-metal offline-ready; AABB/connects = verified geometric clash; open-corpora binary match / timing as product precision.

## Reproduce wall-guid demo

```bash
cd backend
python -m aerobim.tools.export_evidence_bundle \
  --pack ../samples/benchmarks/project-package-wall-guid-demo.json \
  --output ../artifacts/evidence-bundle/checkpoint2-wall-guid
```
