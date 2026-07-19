# RED TEAM PHASE 8 — Tenancy / ACL / Isolation — 2026-07-19

**Phase:** 8  
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

Report ACL existed, but the **job plane** was a global namespace: no `tenant_id`, no get/cancel ACL, global idempotency, upload-only quotas, and `validate_ifc` did not stamp tenant.

### Findings addressed

| ID | Severity | Category | Status |
|---|---|---|---|
| RT-P8-001 | HIGH | tenancy / jobs | **MITIGATED** — `tenant_id` on `AnalyzeProjectPackageJob` |
| RT-P8-002 | HIGH | tenancy / ACL | **MITIGATED** — job get/cancel enforce object ACL |
| RT-P8-003 | HIGH | tenancy / idempotency | **MITIGATED** — idempotency keyed per tenant |
| RT-P8-004 | HIGH | tenancy / spoof | **MITIGATED** — ACL-on binds principal tenant; client cannot override |
| RT-P8-005 | MEDIUM | tenancy / validate | **MITIGATED** — `validate_ifc` stamps `tenant_id` onto report |
| RT-P8-006 | MEDIUM | concurrency | **MITIGATED** — `AEROBIM_MAX_CONCURRENT_ANALYZE_JOBS_PER_TENANT` → 429 |
| RT-P8-007 | MEDIUM | contour isolation | **MITIGATED** — advisory ERROR demoted; cannot raise engine ERROR count |

---

## After phase

### Changed files (Phase 8)

- `domain/models.py`, `domain/object_acl.py`, `domain/ports.py`
- `application/use_cases/analyze_project_package_jobs.py`
- `application/use_cases/validate_ifc_against_ids.py`
- job stores (in-memory + redis)
- `presentation/http/api.py`, `core/config/settings.py`, `.env.example`
- `tests/test_rt_phase8_tenancy.py` (new)

### Commands

| Command | Result |
|---|---|
| focused Phase 8 + job tests | 14 passed |
| `pytest` (full) | **622 passed, 4 skipped** |
| `ruff check src tests` | passed |

### Residual risks

- Redis reclaim still stub (`[]`) — Phase 6 residual unchanged.
- Norm-pack HITL endpoints not yet tenant-owned.
- Object keys not yet prefixed `tenants/{tid}/…` (defense-in-depth).
- Advisory full matrix across OCR/CV/LLM feature flags still narrower than production matrix.
- Phases 9–10 and RT-001/002/003 remain open → **NO_GO**.

### Explicit confirmation

PR #10/#11 untouched. Git history untouched. No destructive Git.
