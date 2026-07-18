# RED TEAM PHASE 2 — Provenance — 2026-07-18

**Phase:** 2  
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

Findings could receive **random `uuid4` finding_id**, weak `source_id=unspecified`, and BCF topics with **non-deterministic GUIDs** and missing provenance text — breaking reproducibility and export round-trip honesty.

### Inspected paths

- `ensure_finding_provenance` → audit `save` → `get` → JSON/HTML/BCF export
- `DeterminismGate` advisory merge
- `bcf_report_exporter` / `bcf3_exporter`

### Findings addressed

| ID | Severity | Category | Status |
|---|---|---|---|
| RT-P2-001 | HIGH | provenance | **MITIGATED** — deterministic SHA-256 `finding_id` |
| RT-P2-002 | HIGH | provenance / BCF | **MITIGATED** — stable BCF topic/viewpoint UUIDs + finding_id/evidence/origin in description |
| RT-P2-003 | MEDIUM | provenance | **MITIGATED** — `origin` field (`deterministic`/`advisory`); gate stamps advisory |
| RT-P2-004 | MEDIUM | provenance | **MITIGATED** — weak `unspecified` → `auto:…`; persistable rejects placeholders |
| RT-P2-005 | LOW | testing | **MITIGATED** — round-trip persist/reload/BCF test |

---

## After phase

### Changed files

- `backend/src/aerobim/domain/finding_provenance.py`
- `backend/src/aerobim/domain/models.py` (`ValidationIssue.origin`)
- `backend/src/aerobim/application/services/determinism_gate.py`
- `backend/src/aerobim/infrastructure/adapters/bcf_report_exporter.py`
- `backend/src/aerobim/infrastructure/adapters/bcf3_exporter.py`
- `backend/src/aerobim/infrastructure/adapters/filesystem_audit_store.py`
- `backend/src/aerobim/presentation/http/api.py` (HTML origin)
- `backend/src/aerobim/tools/audit_issue_traceability.py` (`auto:` not spatial anchor)
- `backend/tests/test_rt_phase2_provenance.py` (new)

### New contracts

- `compute_stable_finding_id`, `is_finding_publishable`, `FindingOrigin`
- `ValidationIssue.origin`
- BCF `_BcfTopicPayload.labels` + stable UUID seed

### Commands

| Command | Result |
|---|---|
| mypy src | PASS |
| pytest tests -q | **589 passed, 4 skipped** |

### Evidence

- `audit/reports/RED_TEAM_PHASE2_2026_07_18.md`
- `audit/evidence/phase2-command-results-2026-07-18.json`

### Claim changes

None. Checkpoint **NO_GO**. CDE import still **NOT_VERIFIED**.

### Residual risks

- Frontend panel may not yet surface `origin` explicitly (review-shell Phase 5/19).
- Full golden HTML artifact lock still residual.
- Persistence atomicity / orphan recovery → Phase 3.

### Explicit confirmation

PR #10 untouched. PR #11 untouched. Git history untouched. No destructive Git command executed.
