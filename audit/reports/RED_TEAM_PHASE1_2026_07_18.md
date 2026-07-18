# RED TEAM PHASE 1 — Sign-off hardening — 2026-07-18

**Phase:** 1  
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

Close residual **false-pass** paths where profile-required capabilities could remain `SKIPPED` / `NOT_VERIFIED` while `summary.passed=true`.

### Inspected runtime paths

- `SignOffCapabilityPolicy.summary_passed` → `EvidenceAssembler.assemble` → `ValidationSummary.passed`
- `_build_capabilities` (schema / raster / quantity)
- `_run_quantity_consistency`
- DI `AnalyzeProjectPackageUseCase` + `signoff_profile`

### Findings addressed

| ID | Severity | Category | Status |
|---|---|---|---|
| RT-P1-001 | HIGH | false-pass / sign-off | **MITIGATED** — `require_clash` / `require_bsi_schema` now block non-OK at policy SSOT |
| RT-P1-002 | HIGH | false-pass / MEP | **MITIGATED** — unified via `required_capability_blocks_pass` |
| RT-P1-003 | MEDIUM | false-pass / IFC schema | **MITIGATED** — required schema without validator → `FAILED` |
| RT-P1-004 | MEDIUM | false-pass / raster | **MITIGATED** — requested raster without analyzer → `FAILED` (no raise-and-skip) |
| RT-P1-005 | MEDIUM | false-pass / quantity | **MITIGATED** — claims + missing checker → `NOT_VERIFIED` blocks pass; `quantity` on `ReportCapabilities` |
| RT-P1-006 | LOW | operations / frontend | **MITIGATED** — `npm run build` TS BlobPart fix |

---

## Patch plan executed

1. Expand `capability_policy` required-capability matrix (clash / schema / MEP).
2. Block `quantity=NOT_VERIFIED` like `calculation_match`.
3. Wire full `build_signoff_policy(...)` into `EvidenceAssembler` (profile + flags).
4. UC: `signoff_profile`; schema/raster/quantity honesty.
5. Persist/reconstruct `capabilities.quantity`.
6. Regression tests + frontend build fix.

### Expected invariants

- `FAILED` listed capabilities → `passed=false`
- Profile-required clash/schema/MEP → only `OK` allows pass
- `calculation_match` / `quantity` `NOT_VERIFIED` → `passed=false`
- Empty / missing raster when requested → `FAILED` → `passed=false`
- Development profile still allows optional clash `SKIPPED`

---

## After phase

### Changed files (Phase 1 delta)

- `backend/src/aerobim/application/services/capability_policy.py`
- `backend/src/aerobim/application/services/signoff_policy.py`
- `backend/src/aerobim/application/services/analyze_orchestrators.py`
- `backend/src/aerobim/application/use_cases/analyze_project_package.py`
- `backend/src/aerobim/domain/models.py` (`ReportCapabilities.quantity`)
- `backend/src/aerobim/infrastructure/adapters/filesystem_audit_store.py`
- `backend/src/aerobim/infrastructure/di/bootstrap.py`
- `backend/tests/test_rt_phase1_signoff.py` (new)
- `frontend/src/lib/api.ts` (Blob typing)

### New contracts

- `SignOffCapabilityPolicy.required_capability_blocks_pass`
- `ReportCapabilities.quantity`
- UC `signoff_profile` → policy build in evidence assembly

### Architectural decisions

- Required capabilities: **only `OK` is acceptable** (Master Prompt §6).
- Policy SSOT remains `capability_policy`; UC flags are overrides merged onto profile defaults.
- Quantity stays a first-class capability (not only folded into `ifc_validation` on FAILED).

### Tests added

- `tests/test_rt_phase1_signoff.py` — policy + UC paths for clash/schema/raster/quantity/pilot defaults

### Commands executed

| Command | Result |
|---|---|
| ruff format / check (touched) | PASS |
| mypy src | PASS (147 files) |
| pytest tests -q | **584 passed, 4 skipped** |
| frontend vitest | **25 passed** |
| frontend `npm run build` | **PASS** |

### Evidence artifacts

- This report: `audit/reports/RED_TEAM_PHASE1_2026_07_18.md`
- Command evidence: `audit/evidence/phase1-command-results-2026-07-18.json`
- Prior baseline: `audit/reports/RED_TEAM_BASELINE_2026_07_18.md`

### Claim changes

- None inflated. Checkpoint remains **NO_GO**.
- No customer accuracy / MEP system-aware / CDE claims.

### Residual risks

- Local tree still dirty (Phase 0 hyperdeep + Phase 1); not on `origin/main` until explicit commit.
- Full outbox / job lease / golden BCF (later phases).
- RT-001/002/003 external.
- Norm pack without `approval_ref` activation already fail-closed at loader; pilot “must request packs” not newly forced here.

### Explicit confirmation

PR #10 untouched. PR #11 untouched. Git history untouched. No destructive Git command executed.
