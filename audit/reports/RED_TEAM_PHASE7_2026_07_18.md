# RED TEAM PHASE 7 — openBIM Correctness — 2026-07-18

**Phase:** 7  
**Checkpoint:** `NO_GO` (unchanged)  
**External blockers:** RT-001 / RT-002 / RT-003 still OPEN  

---

## Confirmations

| Constraint | Status |
|---|---|
| PR #10 untouched | Confirmed (HEAD still `ad8e12d` on `main`; no branch checkout / push) |
| PR #11 untouched | Confirmed (same) |
| Git history untouched | Confirmed |
| No destructive Git | Confirmed |
| No unsupported capability promoted to OK | Confirmed — SPF-only under `require_bsi_schema` → `NOT_VERIFIED`; BCF XSD → `not_run` |

---

## Scope (before)

False-pass / honesty gaps in openBIM contour:

1. SPF `FILE_SCHEMA` pre-gate could green-pass while `require_bsi_schema` demanded real schema cert.
2. IDS unsupported facets / empty applicability could be silently skipped.
3. No GlobalId invalid/duplicate integrity scan.
4. Cross-doc contradictions lacked `match_method` / origin / evidence_refs.
5. BCF structural verifier could report XSD `passed` without running XSD validation.

### Findings addressed

| ID | Severity | Category | Status |
|---|---|---|---|
| RT-P7-001 | HIGH | false-pass / schema | **MITIGATED** — unsupported `FILE_SCHEMA` → ERROR; SPF-only + `require_bsi_schema` → `NOT_VERIFIED` |
| RT-P7-002 | HIGH | false-pass / IDS | **MITIGATED** — unsupported facet + empty applicability fail-closed |
| RT-P7-003 | MEDIUM | integrity / GUID | **MITIGATED** — invalid + duplicate GlobalId ERROR findings on `IfcRoot` |
| RT-P7-004 | MEDIUM | provenance / cross-doc | **MITIGATED** — `match_method`, `origin`, `evidence_refs` on contradictions |
| RT-P7-005 | MEDIUM | false-pass / BCF | **MITIGATED** — XSD presence without run → `not_run` (never fake `passed`) |

---

## After phase

### Changed files (Phase 7)

- `backend/src/aerobim/domain/ifc_globalid.py` (new)
- `backend/src/aerobim/domain/models.py` (`match_method`)
- `backend/src/aerobim/infrastructure/adapters/basic_ifc_schema_validator.py`
- `backend/src/aerobim/infrastructure/adapters/xml_ids_document_auditor.py`
- `backend/src/aerobim/infrastructure/adapters/ifc_open_shell_validator.py`
- `backend/src/aerobim/infrastructure/adapters/bcf_consumers.py`
- `backend/src/aerobim/application/use_cases/analyze_project_package.py`
- `backend/tests/test_rt_phase7_openbim.py` (new)
- `backend/tests/test_ifc_open_shell_validator.py` (expect `IfcRoot` scan)

### Commands

| Command | Result |
|---|---|
| `pytest tests/test_rt_phase7_openbim.py` (+related) | passed |
| `pytest` (full) | **616 passed, 4 skipped** |
| `mypy src/aerobim` | **Success: no issues found in 149 source files** |

### Residual risks

- Full EXPRESS / bSI remote certificate still required for production schema OK under pilot.
- IDS facet allowlist is conservative; rare legal IDS facets may need explicit expansion.
- GlobalId scan covers `IfcRoot` via ifcopenshell; malformed models without `IfcRoot` skip quietly.
- Real XSD validation still not implemented (`not_run` is honest, not a substitute).
- Phases 8–10 (tenancy depth / federated MEP corpus / GO criteria) not started.
- External blockers RT-001/002/003 remain open → checkpoint stays **NO_GO**.

### Explicit confirmation

PR #10/#11 untouched. Git history untouched. No destructive Git. No commit/push.
