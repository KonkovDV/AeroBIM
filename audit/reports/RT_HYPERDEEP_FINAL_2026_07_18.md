---
title: "RT Hyperdeep Final Report — 2026-07-18"
head_baseline: ad8e12d7fd28731ba6eb4bcfa9c677220ba01225
checkpoint: NO_GO
release_verdict: NO_GO
engineering_lane: CONDITIONAL (fixture fail-closed improved; customer evidence still missing)
---

# Executive summary

Hyperdeep Red Team audit executed on AeroBIM `main` @ `ad8e12d` (clean tree). Phase 0 gates were green. Prior RT-C soft-pass paths (quantity/load/MEP exceptions) were already mitigated. This session closed several **remaining** false-pass / integrity gaps with atomic patches + negative tests:

| ID | Severity | Status |
|----|----------|--------|
| RT-HYPER-001 | CRITICAL | **MITIGATED** — `require_mep_system_clash` + profile policy |
| RT-HYPER-002 | HIGH | **MITIGATED** — corrupt JSONL counted; fail-closed mode |
| RT-HYPER-003 | MEDIUM | **MITIGATED** — deterministic HITL `event_id` + dedupe |
| RT-HYPER-004 | HIGH | **MITIGATED (minimal)** — commit marker + orphan record |
| RT-HYPER-005 | MEDIUM | **MITIGATED** — bbox validator; IoU default 0.25 |
| RT-HYPER-006 | HIGH | **MITIGATED** — `SignOffCapabilityPolicy` SSOT |
| RT-HYPER-007 | BLOCKER | **EXTERNAL** — RT-001/002/003 unchanged |

**Release verdict: NO_GO** (customer RT-001/002/003 open; fixture-only engineering readiness ≠ pilot readiness).

---

## Findings by severity

### BLOCKER / EXTERNAL
- **RT-HYPER-007 / RT-001/002/003** — customer accuracy, approved norm pack, federated MEP. Code cannot close.

### CRITICAL (mitigated this session)
- **RT-HYPER-001** — MEP `NOT_VERIFIED` could green-pass under pilot wording. Fix: policy + `AEROBIM_REQUIRE_MEP_SYSTEM_CLASH` / `AEROBIM_SIGNOFF_PROFILE=samolet_pilot`.

### HIGH (mitigated)
- **RT-HYPER-002** — silent JSONL skip → counter + `AuditEventCorruptionError` when `audit_fail_closed`.
- **RT-HYPER-004** — object-before-report orphans → `.committed.json` + `orphans/` record on failure.
- **RT-HYPER-006** — duplicated gating → `capability_policy.py`.

### MEDIUM (mitigated)
- **RT-HYPER-003** — `uuid4` HITL ids → sha256 fingerprint + append dedupe.
- **RT-HYPER-005** — IoU 0.05 false match → 0.25 + bbox reject NaN/inf/zero-area.

### Already mitigated pre-session (confirmed)
- Quantity/load/MEP infrastructure exception → FAILED + `passed=false`
- Raster zero annotations → FAILED
- `calculation_match` NOT_VERIFIED blocks pass
- Mixed DWG+DXF → FAILED

---

## False-pass / security / integrity attack paths

| Path | Residual |
|------|----------|
| Quantity exception soft WARNING | Closed (prior) |
| MEP NOT_VERIFIED under required profile | Closed when profile/flag set; **dev default still allows** (by design) |
| Corrupt review events hide HITL | Closed in fail-closed; open mode still degrades-with-counter |
| Orphan IFC after failed save | Recorded; **full cleanup/reconciliation CLI not yet** |
| Cross-tenant ACL | Prior tests exist; not re-audited exhaustively this session |
| Advisory mutates `passed` | Partial E2E exists; full contour isolation residual |
| Path jail / upload bombs | Prior coverage; residual fuzz matrix incomplete |

---

## Claims

| Claim | Status |
|-------|--------|
| Checkpoint NO_GO | **PRESERVED** |
| RT-001/002/003 open | **PRESERVED** |
| BCF T2 CDE | NOT_VERIFIED |
| Native DWG | NOT delivered |
| Calculation correctness | NOT_IMPLEMENTED |
| Fixture SLA ≠ customer SLA | PRESERVED |
| Marketing inflation | **NONE** |

---

## Changed files (this session)

**Plan / audit**
- `audit/reports/REDTEAM_HYPERDEEP_PLAN_2026_07_18.md`
- `audit/reports/RT_HYPERDEEP_PHASE0_2026_07_18.md`
- `audit/reports/RT_HYPERDEEP_FINAL_2026_07_18.md` (this file)
- `audit/reports/CLAIMS_LOCK_2026_07_17.md` (honesty extensions only)

**Code**
- `backend/src/aerobim/application/services/capability_policy.py` (new)
- `backend/src/aerobim/application/services/signoff_policy.py`
- `backend/src/aerobim/application/services/analyze_orchestrators.py`
- `backend/src/aerobim/application/use_cases/analyze_project_package.py`
- `backend/src/aerobim/core/config/settings.py`
- `backend/src/aerobim/domain/drawing_region_hitl.py`
- `backend/src/aerobim/domain/models.py` (`idempotency_key`)
- `backend/src/aerobim/infrastructure/adapters/filesystem_review_event_store.py`
- `backend/src/aerobim/infrastructure/adapters/filesystem_audit_store.py`
- `backend/src/aerobim/infrastructure/di/bootstrap.py`
- `backend/.env.example`

**Tests**
- `backend/tests/test_rt_hyperdeep_hardening.py` (new, 11 cases)

---

## Commands executed

| Command | Result |
|---------|--------|
| `git status` / HEAD / dirty | clean @ `ad8e12d` |
| `ruff format --check` / `ruff check` | PASS |
| `mypy src` | PASS |
| `pytest tests -q` (baseline) | PASS 539+4 skip |
| `pytest tests -q` (after patches) | **PASS 562+4 skip** |
| upload magic-byte / ACL API tests | PASS |
| `evaluate_extraction --min-macro-f1 0.70` | PASS |
| `verify_bcf_structural_handoff` | PASS (T1; CDE NOT_VERIFIED) |
| `measure_package_sla --corpus-kind fixture` | PASS |
| `export_runtime_baseline` | PASS |
| `frontend npm test` | PASS 25 |
| `npm run build` | **not re-run this session** (prior green assumed; residual) |

---

## Remaining external blockers

1. **RT-001** — customer corpus accuracy evidence  
2. **RT-002** — customer-approved norm pack + `approval_ref`  
3. **RT-003** — federated MEP scope memo + system-aware clash OK  

## Exact residual risks

- Full storage transaction/outbox + concurrent save locks not complete  
- HITL state machine (`waived`/`superseded` transitions) not fully modeled  
- Advisory E2E isolation beyond fixture pack narrow test  
- Jobs durable lease/heartbeat after process crash  
- Mutation CI gates not all wired into GitHub Actions  
- `npm run build` not re-verified in this session  

---

## Explicit confirmations

- **PR #10 untouched**  
- **PR #11 untouched**  
- **Repository history untouched** (no force-push, reset --hard, filter-repo, gc, branch/tag delete)  
- **No destructive git operations executed**  

## Release verdict

**NO_GO**

Rule applied: customer evidence missing → checkpoint NO_GO; fixture fail-closed hardening improves engineering readiness but does not equal Samolet pilot readiness.
