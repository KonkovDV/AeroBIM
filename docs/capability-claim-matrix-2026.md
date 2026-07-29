---
title: "AeroBIM Capability Claim Matrix 2026"
status: active
version: "1.0.0"
last_updated: "2026-07-28"
claim_boundary: "Sync with CLAIMS_LOCK. Checkpoint NO_GO until RT-001/002/003."
---

# Capability × Claim Matrix (TechLab / Samolet)

Companion to [`../audit/reports/CLAIMS_LOCK_2026_07_17.md`](../audit/reports/CLAIMS_LOCK_2026_07_17.md) and [`PROJECT_STATUS_AUDIT_2026.md`](PROJECT_STATUS_AUDIT_2026.md).

API honesty surface: `GET /v1/system/capabilities` schema **1.3.0** (`direction_contracts`, `bcf_t2`, `mep_intake`).

## Four gap directions (honest statuses)

| Direction | Code readiness | Fixture | Customer | Status vocabulary |
|---|---|---|---|---|
| Native DWG | MISSING (`Ezdxf` fail-closed; ODA stub off analyze) | — | — | never `dwg_dxf=ok` |
| DXF | PARTIAL optional `[cad]` | fixture TEXT/MTEXT | not claimed | never = DWG support |
| DWG→PDF/IFC route | derived provenance helper | unit | external prep | `available_as_derived_input` ≠ `dwg_supported` |
| Geometric hard clash | when ifcclash configured | fixture | — | ≠ full MEP |
| MEP system graph | co-presence / ENG_FIXTURE | FIXTURE_ONLY | BLOCKED | RT-003 OPEN |
| MEP system-aware rules | matrix schema + intake | template | BLOCKED_CUSTOMER_DATA | MEP-CLASH-001 |
| Calculation match | load/qty/cross-doc/OpenRebar | fixture | — | сверка only |
| Calculation correctness | NOT_IMPLEMENTED | — | — | no solver |
| BCF 2.1 / T1 | AVAILABLE | integration | — | structural ZIP |
| BCF T2 CDE import | NOT_VERIFIED | empty proof dir | needs sandbox | no CDE_READY |

## Forbidden until customer evidence

| Claim | Blocker | Allowed substitute |
|---|---|---|
| Product accuracy >90% | RT-001 | Fixture macro_f1 only; cite pack + SHA |
| Customer SLA ≤30 min | RT-001 / SLA honesty | Fixture SLA `claim_level=fixture_only` |
| Approved customer norm pack | RT-002 | Synthetic/draft packs only (`claim_labels`); full approval object + pack_hash required — RT-002 **OPEN** |
| MEP system clash delivered | RT-003 | `mep_system_clash=NOT_VERIFIED`; eng foundation improved — RT-003 **OPEN** |
| Native DWG analysis | — | НЕ РЕАЛИЗОВАНО (`native DWG parser is not implemented`) |
| Independent calc correctness | — | Сверка переданных результатов и источников, не расчётный решатель |
| BCF ready for CDE | RT-008 T2 | Structural ZIP **AVAILABLE**; CDE import **NOT_VERIFIED** ([ladder](architecture/BCF_EVIDENCE_LADDER_T0_T4_2026_07.md)); requires log+screenshot+hashes |
| Production-ready / external academic audit | — | Self-audit + NO_GO |
| Hybrid AI makes the public API safe for customer data / masking = anonymity | — | Route only *policy-eligible*; masking reduces disclosure, not anonymity; contour NOT wired to verdict / live egress |

## Allowed with evidence pointers

| Claim | Evidence |
|---|---|
| Deterministic IFC/IDS/cross-doc Shared-gate | pytest + ADR-001 |
| Fail-closed pilot/production sign-off | `capability_policy` + `test_rt_remediation_post` / P0 suite |
| Provenance required on persist | `finding_provenance` + tests |
| Cross-tenant ACL → 404 | ACL tests |
| SSRF guard on outbound JWKS/bSI/OpenCDE | `outbound_url.py` + tests |
| BCF 2.1/3.0 structural export | `audit/evidence/bcf-structural-handoff-2026-07-25.json` |
| HITL remark edit | frontend + review-events API |
| Extraction F1 on RU fixtures | `evaluate_extraction`; baseline JSON |
| Fixture reproducibility hash | `run_manifest.json` + `test_golden_report` |
| Hybrid AI routing foundation (classify/policy/guard/audit/gate) | `domain/hybrid/*` + 80+ tests; domain-pure, verdict-neutral (OFF==ON), fail-closed, NOT in the verdict path — [`HYBRID_AI_FINAL_REPORT`](../audit/reports/HYBRID_AI_FINAL_REPORT_2026_07_28.md) |

## Run manifest (iteration 2026-07-21)

Evidence bundles emit `run_manifest.json` with `reproducibility_hash` over deterministic engine findings + capability digest (excludes `report_id` / timestamps). Golden baseline hash pinned in `backend/tests/test_golden_report.py`. **Fixture only** — not customer accuracy.

`PackageOutcome` enum landed on `summary.outcome` (`pass` / `pass_with_warnings` / `review_required` / `blocked` / `failed`). `summary.passed` is derived only via `summary_passed_from_outcome` (true for PASS / PASS_WITH_WARNINGS). Evidence bundles prefer `summary.outcome` for `derived_outcome`.

| Reading | Signals |
|---|---|
| PASS | `summary.outcome=pass` + required caps OK |
| PASS_WITH_WARNINGS | `outcome=pass_with_warnings` (non-blocking WARNING findings) |
| BLOCKED | intake blocked or required cap not OK under hard profile (often `error_count=0`) |
| FAILED | deterministic ERROR findings / hard clash under clash_affects_pass |
| REVIEW_REQUIRED | HITL regions require review |

Checkpoint remains **NO_GO** until RT-001/002/003 customer evidence. `summary.passed` remains Shared-gate technical status — **not** Shared→Published.
