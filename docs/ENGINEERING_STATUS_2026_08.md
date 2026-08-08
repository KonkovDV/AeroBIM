<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
---
title: "AeroBIM Engineering Status — August 2026"
status: active
version: "1.6.6"
last_updated: "2026-08-09"
claim_boundary: "Engineering readiness only. Checkpoint NO_GO until RT-001/002/003. Fixture != customer."
---

# Engineering Status — 2026-08-09

**HEAD (docs refresh):** see [`evidence/runtime-baseline-latest.json`](evidence/runtime-baseline-latest.json)  
**last_updated:** 2026-08-09 · **v1.6.6** — Renga **ToS cite GO**; Exp A / PNST IDS runtime **18/22 clean**; baseline schema **1.4.0** (CI-attested when publishable)  
**Checkpoint:** **`NO_GO`** — RT-001 / RT-002 / RT-003 remain OPEN  
**Claims SSOT:** [`../audit/reports/CLAIMS_LOCK_2026_07_17.md`](../audit/reports/CLAIMS_LOCK_2026_07_17.md) · dated freeze [`../audit/reports/CLAIMS_LOCK_2026_07_31.md`](../audit/reports/CLAIMS_LOCK_2026_07_31.md)  
**P0 Red Team:** [`quality/RED_TEAM_P0_ROLLUP_2026_08_02.md`](quality/RED_TEAM_P0_ROLLUP_2026_08_02.md)  
**Residuals Red Team:** [`quality/RED_TEAM_ENG_RESIDUALS_2026_08_03.md`](quality/RED_TEAM_ENG_RESIDUALS_2026_08_03.md)  
**Wave-2 Red Team (К0/commercial/coverage):** [`quality/RED_TEAM_WAVE2_TRACKER_COMMERCIAL_2026_08_04.md`](quality/RED_TEAM_WAVE2_TRACKER_COMMERCIAL_2026_08_04.md)  
**Studio stamp/PII Red Team:** [`quality/RED_TEAM_GRANT_STAMP_PII_2026_08_03.md`](quality/RED_TEAM_GRANT_STAMP_PII_2026_08_03.md)  
**Qwen local:** [`architecture/QWEN38_AEROBIM_FEASIBILITY_2026_08_03.md`](architecture/QWEN38_AEROBIM_FEASIBILITY_2026_08_03.md) · [`roadmap/QWEN_LOCAL_KT2_PLAN_2026_08.md`](roadmap/QWEN_LOCAL_KT2_PLAN_2026_08.md) · [`architecture/YANDEX_AI_STUDIO_GRANT_KT2_2026_08_03.md`](architecture/YANDEX_AI_STUDIO_GRANT_KT2_2026_08_03.md)  
**Demo / P4:** [`demo-format-2026-08.md`](demo-format-2026-08.md) · Exp B [`evidence/EXPERIMENT_B_TYPICAL_REMARKS_KR_COVERAGE_2026_08.md`](evidence/EXPERIMENT_B_TYPICAL_REMARKS_KR_COVERAGE_2026_08.md) · Exp A [`evidence/EXPERIMENT_A_RENGA_PNST909_2026_08.md`](evidence/EXPERIMENT_A_RENGA_PNST909_2026_08.md) · RT Friday [`quality/RED_TEAM_KT2_FRIDAY_PACK_2026_08_05.md`](quality/RED_TEAM_KT2_FRIDAY_PACK_2026_08_05.md)  
**Release aliases:** [`RELEASE_POLICY.md`](RELEASE_POLICY.md) — `LOCAL` env alias dies after КТ#3 **2026-09-21**

## What improved (engineering — not customer GO)

| Track | Eng status | Customer |
|---|---|---|
| **P4 Experiment B (KR→AR→VK) CLOSED** | KR **≈16.7**/≈25/33/25 after #2+#4 LOGIC closed (#9/#10 MISSING_ATTRIBUTE ≈8.3pp); AR 17/25/42/17 (n=12); VK 25/50/13/13; RT-002≈17pp KR; RT-003=13pp VK | Friday speech synced; OV deferred KT#3; PNST 909 pin owner |
| **Task 2 partial package** | `ifc_path` optional on analyze; document-only mode SKIPPED/NOT_VERIFIED for IFC engines; fail-closed if clash/MEP required | Not Checkpoint GO; not product accuracy |
| **Task 7 weekly eng status** | `python -m aerobim.tools.export_weekly_eng_status` → `docs/evidence/weekly-eng-status-latest.json`; funnel = OWNER_ONLY | Never invent commercial counts |
| **Task 4 adjudication plan** | `plan_adjudication_corpus` → recommended_n=111 for interim 0.60 @ expected 0.75 | Sizes labeling only; not precision |
| **External P1/P4 research** | Renga pin + IDS inventory 18/22; SPb/Amur AR recount; GOST **21.101-2026** п.8.2.4 GUID | Owner: Renga ToS cite; DWG A/B/C |
| **P4 Experiment A (Renga ПНСТ 909)** | **ToS GO**; runtime **18/22** IDS clean; 4 out_of_pack | Evidence [`evidence/pnst909-22-scenario-runtime-latest.json`](evidence/pnst909-22-scenario-runtime-latest.json); not product accuracy |
| **Regulatory 21.101** | Marks OS/ODD/MBT; edition config; N-2 clause **8.2.4** | No full-compliance claim |
| **Demo format 2026-08** | 30–40 min script + criticality + discrepancy rule + on-prem expertise path | Ready for tracker pack |
| **Commercial ops quarantine** | Live funnel/outreach only under `.local/commercial-ops/`; public = templates | Funnel numbers = owner only |
| **LOCAL→ADVISORY alias** | Boot WARNING; remove after 2026-09-21 | Docs must not reintroduce LOCAL-only |
| **CRITICAL_BLOCKERS RT-004…017** | Closed sections lead with **СТАТУС: ЗАКРЫТО** | RT-001/002/003 still OPEN → NO_GO |
| **Eng residuals wave** | VLM smoke gate; signature deepen; OIDC Phase 2 stubs; BCF T2 checklist; DWG native fail-closed; BSI IDS n=290 CC BY-ND; bare-metal wheelhouse DEFERRED | Checkpoint NO_GO unchanged |
| **Qwen / Studio KT#2** | RT budget charge+retry+ledger; inj: no model severity; PII `/Rotate`+counters; opaque client UUID; Red Team v1.5 | Checkpoint NO_GO; PII effectiveness NOT_MEASURED |
| **Open corpora + BSI IDS** | Fixture regression n=7 + BSI TestCases profile `regression-bsi` **honest_case_count=290** (CC BY-ND unmodified) | Regression only — not product accuracy |
| **WP-07 quality protocol** | Protocol doc + `compute_quality_protocol_stats` (Wilson P/R + sample-size planner); nDCG via existing `evaluate_ranking_quality`; interim target 0.60 | Not adjudicated customer precision; never >90% |
| **WP-06 open corpora** | Profiles under `samples/benchmarks/open-corpora/`; CI smoke pins | Regression/timing only — no expert TP/FP |
| **WP-05 package completeness** | Declared inventory: mandatory PD sections, format honesty (no native DWG), cipher/specs/schedules, PD↔RD pairing; soft opt-in via request flag | Fixture-grade only; not PP-87 / customer intake |
| **WP-04 norm pack v2** | Schema 2.0.0 RASE + `execution_mode` + expert confirmation journal; loader fail-closed without `customer_approved`+approval; `list_expert_required_norm_rules` | RT-002 OPEN; fixture ≠ customer pack |
| **WP-03 signature envelope** | Presence/hash/roles + signature_alg/value presence + optional package hash bind; trust_chain always NOT_VERIFIED | Never «УКЭП проверена»; crypto adapter missing |
| **WP-02 Hybrid advisory pre-gate** | Gate on Analyze advisory + kimi smoke PUBLIC egress | Not verdict path; Checkpoint NO_GO |
| **WP-01 runtime baseline** | Schema 1.4.0: passed/skipped/failed + gates + env fingerprint + **documented_env set equality (symdiff)** + **architecture_inventory** (48/72/63) checked in CI `--check-readme` + `docs-metadata-integrity` | Not Checkpoint GO |
| **ADR-002 open-core** | **accepted** 2026-08-05; LICENSE stays MIT | Boundary defined; not commercial features delivered |
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
