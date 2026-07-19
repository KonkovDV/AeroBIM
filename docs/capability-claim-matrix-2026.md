---
title: "AeroBIM Capability Claim Matrix 2026"
status: active
version: "1.0.0"
last_updated: "2026-07-19"
claim_boundary: "Sync with CLAIMS_LOCK. Checkpoint NO_GO until RT-001/002/003."
---

# Capability × Claim Matrix (TechLab / Samolet)

Companion to [`../audit/reports/CLAIMS_LOCK_2026_07_17.md`](../audit/reports/CLAIMS_LOCK_2026_07_17.md) and [`PROJECT_STATUS_AUDIT_2026.md`](PROJECT_STATUS_AUDIT_2026.md).

## Forbidden until customer evidence

| Claim | Blocker | Allowed substitute |
|---|---|---|
| Product accuracy >90% | RT-001 | Fixture macro_f1 only; cite pack + SHA |
| Customer SLA ≤30 min | RT-001 / SLA honesty | Fixture SLA `claim_level=fixture_only` |
| Approved customer norm pack | RT-002 | Synthetic/draft packs only |
| MEP system clash delivered | RT-003 | `mep_system_clash=NOT_VERIFIED` |
| Native DWG analysis | — | НЕ РЕАЛИЗОВАНО |
| Independent calc correctness | — | Сверка PARTIAL only |
| BCF ready for CDE | RT-008 T2 | Structural ZIP OK; import НЕ ДОКАЗАНО |
| Production-ready / external academic audit | — | Self-audit + NO_GO |

## Allowed with evidence pointers

| Claim | Evidence |
|---|---|
| Deterministic IFC/IDS/cross-doc Shared-gate | pytest + ADR-001 |
| Fail-closed pilot/production sign-off | `capability_policy` + `test_rt_remediation_post` / P0 suite |
| Provenance required on persist | `finding_provenance` + tests |
| Cross-tenant ACL → 404 | ACL tests |
| SSRF guard on outbound JWKS/bSI/OpenCDE | `outbound_url.py` + tests |
| BCF 2.1/3.0 structural export | `audit/evidence/bcf-structural-handoff-2026-07-18.json` |
| HITL remark edit | frontend + review-events API |
| Extraction F1 on RU fixtures | `evaluate_extraction`; baseline JSON |

## Derived package outcome (no enum yet)

| Reading | Signals |
|---|---|
| PASS | `summary.passed=true` + required caps OK |
| PASS_WITH_WARNINGS | `passed=true` with non-blocking WARNING findings (expert judgement; enum not shipped) |
| BLOCKED | `passed=false` because required cap not OK under pilot/production (often `error_count=0`) |
| FAILED | deterministic ERROR findings / adapter infra failure / `passed=false` |
| REVIEW_REQUIRED | open findings awaiting HITL accept/reject (`drawing_regions.hitl_required` / review-events) |

Until the package enum lands (Wave 2), experts derive the reading from `summary.passed` + `capabilities.*` + HITL state. Evidence bundles expose the same mapping as `derived_outcome` (`PASS` / `BLOCKED` / `FAILED`).

`summary.passed` remains Shared-gate technical status — **not** Shared→Published.
