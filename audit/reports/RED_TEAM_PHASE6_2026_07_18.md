# RED TEAM PHASE 6 — Jobs — 2026-07-18

**Phase:** 6  
**Checkpoint:** `NO_GO` (unchanged)  
**External blockers:** RT-001 / RT-002 / RT-003 still OPEN  

---

## Confirmations

| Constraint | Status |
|---|---|
| PR #10 untouched | Confirmed |
| PR #11 untouched | Confirmed |
| Git history untouched | Confirmed |
| No destructive Git | Confirmed |
| No unsupported capability promoted to OK | Confirmed |

---

## Scope (before)

Async jobs had idempotency + snapshot crash→FAILED, but lacked lease/heartbeat, cancel, dead-letter, and reclaim of stuck RUNNING.

### Findings addressed

| ID | Severity | Category | Status |
|---|---|---|---|
| RT-P6-001 | HIGH | concurrency | **MITIGATED** — lease + heartbeat; stale RUNNING reclaimed to FAILED |
| RT-P6-002 | HIGH | concurrency | **MITIGATED** — cancel queued immediately; running via cancel_requested + heartbeat |
| RT-P6-003 | MEDIUM | concurrency | **MITIGATED** — `CANCELLED` / `DEAD_LETTER` statuses; retry_count → dead-letter |
| RT-P6-004 | MEDIUM | API | **MITIGATED** — `POST .../jobs/{id}/cancel` |
| RT-P6-005 | LOW | concurrency | **MITIGATED** — stage_progress / heartbeat fields on job model |

---

## After phase

### Changed files

- `backend/src/aerobim/domain/models.py` (job status + lease fields)
- `backend/src/aerobim/domain/job_transitions.py`
- `backend/src/aerobim/domain/ports.py`
- `backend/src/aerobim/application/use_cases/analyze_project_package_jobs.py`
- `backend/src/aerobim/infrastructure/adapters/in_memory_analyze_project_package_job_store.py`
- `backend/src/aerobim/infrastructure/adapters/redis_analyze_project_package_job_store.py`
- `backend/src/aerobim/presentation/http/api.py`
- `backend/tests/test_rt_phase6_jobs.py` (new)

### Commands

| Command | Result |
|---|---|
| focused job tests | 12 passed |
| mypy / full pytest | see evidence |

### Residual risks

- Redis reclaim is stub (`[]`); lease enforcement is full on in-memory/default store.
- Bounded tenant concurrency quotas not yet global.
- Phase 7 openBIM correctness next.

### Explicit confirmation

PR #10/#11 untouched. Git history untouched. No destructive Git.
