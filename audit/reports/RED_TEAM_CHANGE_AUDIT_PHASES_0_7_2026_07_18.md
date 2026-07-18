# RED TEAM CHANGE AUDIT — Phases 0–7 — 2026-07-18

**Scope:** Local dirty-tree Red Team work after Master Prompt Phases 0–7.  
**Committed HEAD:** `ad8e12d` (`main` = `origin/main`) — **unchanged**.  
**Checkpoint:** **`NO_GO`**  
**External blockers still OPEN:** RT-001 (customer corpus), RT-002 (approved norms), RT-003 (federated MEP).

---

## 1. Executive verdict

Phases **0–7 are implemented locally** (uncommitted). Gates are green (**616 pytest / mypy clean**). Absolute constraints held: no PR #10/#11 edits, no history rewrite, no force-push, no capability falsely promoted to OK. **Do not treat the tree as pilot-ready** — external blockers remain, and Master Phases **8–10** are not done.

---

## 2. Constraint compliance

| Constraint | Evidence |
|---|---|
| PR #10 / #11 untouched | Still on `main` @ `ad8e12d`; no other branch checked out; no push |
| No destructive Git | No `reset --hard`, `clean -fd`, filter-repo, force-push |
| No commit/push | Dirty tree only; user did not request commit |
| AI must not own `summary.passed` | Sign-off still via `summary_passed_after_capabilities` + capability policy |
| No unsupported → OK | Schema SPF-only → `NOT_VERIFIED` under `require_bsi_schema`; BCF XSD → `not_run` |

---

## 3. Phase coverage map

| Phase | Theme | Local status | Key artifacts |
|---|---|---|---|
| 0 | Baseline | Done | `RED_TEAM_BASELINE_2026_07_18.md` |
| 1 | Sign-off honesty | Done | `capability_policy.py`, `test_rt_phase1_signoff.py` |
| 2 | Provenance | Done | `finding_provenance.py`, stable finding_id / BCF GUID |
| 3 | Persistence | Done | `persistence.py`, commit/TTL/orphan reconcile |
| 4 | Security | Done | path jail, upload content/quota/zip, no quarantine leak |
| 5 | HITL | Done | `review_state_machine.py`, actor/reason/idempotency |
| 6 | Jobs | Done | lease/heartbeat/cancel/`DEAD_LETTER` |
| 7 | openBIM | Done (this session) | schema/IDS/GlobalId/cross-doc/BCF honesty |
| 8–10 | Tenancy / corpus / GO | **Not started** | — |

---

## 4. Dirty tree inventory (high-signal)

### New (untracked)

- Domain: `ifc_globalid.py`, `persistence.py`, `review_state_machine.py`, `capability_policy.py`
- Security: `upload_content.py`, `upload_quota.py`, `zip_limits.py`
- Tooling: `reconcile_audit_orphans.py`
- Tests: `test_rt_phase{1..7}_*.py`, hyperdeep/upload/ACL suites
- Reports/evidence: `audit/reports/RED_TEAM_*`, `audit/evidence/phase*-command-results-*.json`

### Modified (tracked)

- Analyze / sign-off / jobs / models / ports / DI / HTTP API
- Schema validator, IDS auditor, IFC validator, BCF exporters/consumers
- Audit stores, path jail, settings, frontend Blob/API types
- Partner readiness / claims lock docs (peripheral to RT gates)

---

## 5. Gate evidence (latest)

| Gate | Result |
|---|---|
| `python -m pytest` | **616 passed, 4 skipped** |
| `python -m mypy src/aerobim` | **Success (149 files)** |
| Phase 7 focused | `test_rt_phase7_openbim.py` green |

---

## 6. Residual risk register

| Risk | Severity | Notes |
|---|---|---|
| RT-001/002/003 external | **BLOCKER** | Cannot close NO_GO with code alone |
| Redis job reclaim stub | MEDIUM | In-memory lease full; Redis reclaim still thin |
| No real bSI / EXPRESS | HIGH for production OK | Honest `NOT_VERIFIED` under require_bsi |
| No real BCF XSD run | MEDIUM | Honest `not_run` |
| IDS allowlist conservatism | LOW | May reject uncommon facets until expanded |
| Tenant concurrency quotas | MEDIUM | Phase 8 territory |
| Federated MEP / corpus | BLOCKER | Phase 9+ / RT-003 |
| Uncommitted volume | PROCESS | Large dirty tree — needs curated commit plan when asked |

---

## 7. What “done” does **not** mean

- Not a GO for Samolet pilot sign-off.
- Not permission to start VLM/GraphRAG productization.
- Not evidence that customer IFC/IDS/norms corpus was exercised end-to-end.
- Not a substitute for Phases 8–10.

---

## 8. Recommended next step

**Phase 8** (tenancy / ACL / isolation depth) only after operator confirms priority; otherwise freeze and curate commits when requested. Keep checkpoint **NO_GO** until RT-001/002/003 close with external evidence.
