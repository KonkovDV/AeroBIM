---
title: "RT Hyperdeep Phase 0 — Baseline & Risk Register"
date: 2026-07-18
head: ad8e12d7fd28731ba6eb4bcfa9c677220ba01225
checkpoint: NO_GO
dirty_tree: clean
pr_10_11: untouched (out of scope)
---

# Phase 0 — Read-only reconnaissance

## Baseline

| Item | Value |
|------|--------|
| Branch | `main` |
| HEAD | `ad8e12d` (2026-07-18 17:39:10 +0300) |
| Dirty tree | **clean** |
| Remote | `https://github.com/KonkovDV/AeroBIM` |
| Checkpoint | **NO_GO** (RT-001/002/003 external) |
| Backend tests | **539 passed, 4 skipped** |
| Frontend tests | **25 passed** |
| Claims Lock | `audit/reports/CLAIMS_LOCK_2026_07_17.md` |

## Gate commands (Phase 0)

| Command | Result |
|---------|--------|
| `ruff format --check src tests` | PASS |
| `ruff check src tests` | PASS |
| `mypy src` | PASS |
| `pytest tests -q` | PASS (539/4 skip) |
| `evaluate_extraction --min-macro-f1 0.70` | PASS |
| `verify_bcf_structural_handoff` | PASS (T1 OK; CDE T2 NOT_VERIFIED) |
| `measure_package_sla --corpus-kind fixture` | PASS (`claim_level` fixture-only) |
| `export_runtime_baseline` | PASS |
| `frontend npm test` | PASS (25) |

## Already mitigated (prior Phase 0–3 / RT-C)

| Path | Status | Evidence |
|------|--------|----------|
| Quantity checker exception → WARNING soft-pass | **MITIGATED** | `_run_quantity_consistency` → ERROR + FAILED; `test_rt_c_quantity_infra_failure_blocks_pass` |
| Load evidence exception soft-pass | **MITIGATED** | `test_rt_c_load_infra_failure_blocks_pass` |
| MEP unexpected exception → NOT_VERIFIED | **MITIGATED** | → FAILED; `test_rt_c_mep_unexpected_failure_is_failed` |
| Raster zero annotations → OK | **MITIGATED** | → FAILED |
| calculation_match NOT_VERIFIED green pass | **MITIGATED** | `summary_passed_after_capabilities` |
| Mixed DWG+DXF as NOT_VERIFIED | **MITIGATED** | → FAILED |
| Advisory ON/OFF narrow isolation | **PARTIAL** | `test_rt_e_advisory_on_off_same_engine_and_passed` (fixture pack) |

## Open false-pass / integrity paths (hyperdeep)

### RT-HYPER-001 — Profile-aware MEP NOT_VERIFIED soft-pass
- **Severity:** CRITICAL  
- **Category:** sign-off / claims  
- **File/symbol:** `signoff_policy.summary_passed_after_capabilities`; Settings lacks `require_mep_system_clash`  
- **Trigger:** Pilot/production expects system-aware MEP; capability stays `NOT_VERIFIED` (empty graph / no customer scope) while `summary.passed` can still be true if no ERROR issues.  
- **False PASS:** **yes** under required MEP profile  
- **Proposed fix:** Canonical `SignOffCapabilityPolicy` + `require_mep_system_clash`; NOT_VERIFIED/FAILED/SKIPPED block when required.  
- **Status:** OPEN → patch Phase 2  

### RT-HYPER-002 — Review-event JSONL silent skip
- **Severity:** HIGH  
- **Category:** data-integrity / provenance  
- **File/symbol:** `FilesystemReviewEventStore.list_for_report`  
- **Trigger:** Corrupt JSONL line → `continue` with no counter/metric  
- **False PASS:** can hide missing HITL audit trail  
- **Proposed fix:** invalid_line counter + fail-closed mode for pilot/production  
- **Status:** OPEN → patch Phase 1  

### RT-HYPER-003 — Non-deterministic HITL event_id (`uuid4`)
- **Severity:** MEDIUM  
- **Category:** concurrency / tests  
- **File/symbol:** `review_events_for_hitl_regions`  
- **Trigger:** Re-analyze same report input creates duplicate escalations  
- **Proposed fix:** Deterministic `event_id` + optional `idempotency_key` from region fingerprint  
- **Status:** OPEN → patch Phase 3  

### RT-HYPER-004 — Audit store orphans (object before report commit)
- **Severity:** HIGH  
- **Category:** storage / data-integrity  
- **File/symbol:** `FilesystemAuditStore.save` / `_materialize_*`  
- **Trigger:** IFC/preview put succeeds; report JSON write fails → orphan objects; TTL may delete report JSON only  
- **Proposed fix:** Manifest + commit marker; orphan record on failure; recovery scanner seam  
- **Status:** OPEN → patch Phase 1 (minimal)  

### RT-HYPER-005 — IoU 0.05 false geometric “match”
- **Severity:** MEDIUM  
- **Category:** UX / claims  
- **File/symbol:** `mark_regions_for_hitl(iou_match=0.05)`  
- **Trigger:** Tiny overlap suppresses HITL escalation (geometric ≠ semantic)  
- **Proposed fix:** Raise default IoU; validate bbox (reject NaN/inf/inverted/zero-area)  
- **Status:** OPEN → patch Phase 3  

### RT-HYPER-006 — No single canonical capability policy object
- **Severity:** HIGH  
- **Category:** architecture / claims  
- **Trigger:** Blocking rules duplicated across settings, signoff_policy, UC ctor  
- **Proposed fix:** `capability_policy.py` SSOT used by sign-off + DI  
- **Status:** OPEN → patch Phase 2  

### RT-HYPER-007 — External blockers (not closable by code)
- **Severity:** BLOCKER (checkpoint)  
- **IDs:** RT-001 customer accuracy; RT-002 approved norm pack; RT-003 federated MEP  
- **Status:** EXTERNAL BLOCKER — checkpoint remains **NO_GO**  

## False-pass attack summary

1. Enable pilot wording without `require_mep_system_clash` → green pass with MEP NOT_VERIFIED.  
2. Corrupt review-events JSONL → UI shows empty HITL history while findings claimed escalated.  
3. Crash mid-save after object put → orphan IFC/previews without committed report.  
4. (Mitigated) Throw in quantity/load/MEP adapters — already fail-closed.

## Explicit constraints confirmation (Phase 0)

- PR #10: **not touched**  
- PR #11: **not touched**  
- Repository history: **not rewritten**  
- Destructive git: **not executed**  
