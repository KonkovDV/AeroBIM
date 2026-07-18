# RED TEAM BASELINE — AeroBIM — 2026-07-18

**Phase:** 0 (read-only)  
**Code changes in this phase:** none (product source not edited)  
**Evidence:** `audit/evidence/baseline-command-results-2026-07-18.json`

---

## Absolute confirmations

| Constraint | Status |
|---|---|
| PR #10 untouched | **Confirmed** — no PR refs, branches, or PR objects modified |
| PR #11 untouched | **Confirmed** |
| Git history untouched | **Confirmed** — no rewrite, amend, filter-repo, force-push |
| No destructive Git command executed | **Confirmed** — no `reset --hard`, `clean -fd`, branch/tag deletion, `gc`, reflog expire |
| Repository deletion not requested or performed | **Confirmed** |

---

## Git baseline

| Field | Value |
|---|---|
| Branch | `main` |
| HEAD SHA | `ad8e12d7fd28731ba6eb4bcfa9c677220ba01225` |
| HEAD short | `ad8e12d` |
| Last commit date | 2026-07-18 17:39:10 +0300 |
| Last commit subject | `feat: Phase 0–3 pilot hardening — honesty UI, provenance, cross-doc HITL` |
| Remote | `origin` → `https://github.com/KonkovDV/AeroBIM` |
| Dirty tree | **YES** — 34 paths (local uncommitted work retained, not deleted) |

### Committed vs local

**Committed state (origin/main = HEAD):** `ad8e12d` only.

**Local-only (uncommitted) — baseline inventory, not merged as release:**

Modified:

- `audit/reports/CLAIMS_LOCK_2026_07_17.md`
- `backend/.env.example`
- `backend/src/aerobim/application/services/analyze_orchestrators.py`
- `backend/src/aerobim/application/services/signoff_policy.py`
- `backend/src/aerobim/application/use_cases/analyze_project_package.py`
- `backend/src/aerobim/core/config/settings.py`
- `backend/src/aerobim/core/security/__init__.py`
- `backend/src/aerobim/domain/drawing_region_hitl.py`
- `backend/src/aerobim/domain/models.py`
- `backend/src/aerobim/infrastructure/adapters/filesystem_audit_store.py`
- `backend/src/aerobim/infrastructure/adapters/filesystem_review_event_store.py`
- `backend/src/aerobim/infrastructure/di/bootstrap.py`
- `backend/src/aerobim/presentation/http/api.py`
- `docs/evidence/runtime-baseline-latest.json` (refreshed by Phase 0 `export_runtime_baseline`)
- `docs/partners/TECHLAB_TASK_07_READINESS_2026.md`

Untracked:

- Hyperdeep audit reports (`REDTEAM_HYPERDEEP_*`, `RT_HYPERDEEP_*`, `P0_EXECUTION_*`)
- `docs/partners/AEROBIM_STRATEGIC_ASSESSMENT_2026_07.md`
- `capability_policy.py`, `upload_content.py`, `upload_quota.py`, `zip_limits.py`
- `review_state_machine.py`, `reconcile_audit_orphans.py`
- Tests: `test_rt_hyperdeep_*`, `test_upload_*`, `test_api_object_acl.py`
- `audit/evidence/bcf-structural-handoff-2026-07-18.json`

**Policy:** local patches preserved. Subsequent Master Prompt phases must treat them as baseline local state and apply further work via atomic patches without wiping this tree.

---

## Inventory snapshot

| Metric | Value | Notes |
|---|---|---|
| Backend `aerobim` `.py` files (glob) | 161 | Includes local untracked modules |
| mypy reported source files | 147 | Tool count may exclude some paths |
| Backend `test_*.py` files (glob) | 87 | Includes local new tests |
| Backend test functions (export baseline) | 581 | Fixture/tool metric |
| pytest collected result | **575 passed, 4 skipped** | Working tree |
| Frontend `.ts`/`.tsx` under `src` | 17 | Glob |
| Frontend vitest | **25 passed / 5 files** | Working tree |
| API routes in `api.py` | 21 | See evidence JSON |
| Core runtime deps | fastapi, uvicorn, multipart, ifcopenshell, ifctester, starlette, pymupdf | `pyproject.toml` |
| Optional extras | raster, clash, docling, cad, vision, enterprise, dev | |
| CI workflows | `ci.yml`, `release-readiness.yml`, `academic-benchmark-release.yml` | |

---

## Command results (working tree)

| Command | Exit | Classification |
|---|---|---|
| `ruff format --check src tests` | 0 | **passed** |
| `ruff check src tests` | 0 | **passed** |
| `mypy src` | 0 | **passed** |
| `pytest tests -q` | 0 | **passed** (575 / 4 skipped) |
| `evaluate_extraction --min-macro-f1 0.70` | 0 | **passed** — **fixture only** |
| `verify_bcf_structural_handoff` | 0 | **passed** — structural OK; **CDE import NOT_VERIFIED** |
| `measure_package_sla --corpus-kind fixture` | 0 | **passed** — **fixture SLA only** |
| `export_runtime_baseline` | 0 | **passed** — wrote evidence metrics |
| `frontend npm ci` | n/a | **skipped_existing_modules** (not re-run) |
| `frontend npm test` | 0 | **passed** (25) |
| `frontend npm run build` | **2** | **code_failure** |

### Failed command detail

**`npm run build` → code_failure**

- Exact file: `frontend/src/lib/api.ts`
- Exact symbol / line: `fetchDrawingAssetPreviewBlobUrl` ≈ L110 `new Blob([bytes])`
- Observed: `Type 'Uint8Array<ArrayBufferLike>' is not assignable to type 'BlobPart'`
- Expected: clean `tsc` + vite build
- Impact: frontend production bundle gate red; vitest still green
- Phase 0 action: **documented only** — not fixed (no code changes)

---

## Canonical product model (baseline lock)

**Is:** Reproducible openBIM validation kernel and expert review assistant for IFC, IDS, and cross-document project evidence.

**Is not:** full CDE; Revit runtime; autonomous certification; independent structural solver; native DWG analyzer; human-level CV; Solibri/BIMcollab/Navisworks replacement; autonomous compliance agent.

**Pipeline (canonical):**

`INGESTION → NORMALIZATION → SCHEMA VALIDATION → DETERMINISTIC VALIDATION → CROSS-DOCUMENT ALIGNMENT → ADVISORY ANALYSIS → DETERMINISM GATE → EVIDENCE BUNDLE → HITL REVIEW → JSON/HTML/BCF EXPORT`

Invariant: deterministic path owns `summary.passed`; AI is advisory; expert owns sign-off.

---

## Capability / claims snapshot (epistemic statuses)

Statuses below use Master Prompt vocabulary only.

| Capability / claim | Status | Evidence class |
|---|---|---|
| Deterministic IFC/IDS validation path | `VERIFIED_ON_FIXTURE` | pytest + IDS/IFC suites |
| Extraction macro-F1 ≥ 0.70 | `VERIFIED_ON_FIXTURE` | evaluate_extraction; **not** customer |
| Fixture package SLA | `VERIFIED_ON_FIXTURE` | measure_package_sla |
| Customer accuracy / >90% | `BLOCKED` | **RT-001** |
| Customer-approved norm pack | `BLOCKED` | **RT-002** |
| Federated MEP system-aware clash | `BLOCKED` / `NOT_VERIFIED` without customer scope | **RT-003** |
| Generic clash (IfcClash extra) | `OPTIONAL` | clash extra |
| BCF 2.1 structural ZIP | `VERIFIED_ON_FIXTURE` | verify_bcf_structural_handoff |
| BCF CDE import | `NOT_VERIFIED` | explicit in handoff tool |
| Calculation matching | `PARTIAL` / contract matching | do not claim independent correctness |
| Calculation correctness | `NOT_IMPLEMENTED` | |
| OCR / raster evidence | `EXPERIMENTAL` / fixture-bound | empty OCR must not auto-OK (local patches claim mitigation — still working-tree) |
| DXF via ezdxf | `OPTIONAL` | not native DWG |
| LLM/VLM/GraphRAG in sign-off | `NOT_IMPLEMENTED` (must remain out of deterministic path) | |
| Frontend production build | `NOT_VERIFIED` / gate **failed** | TS Blob typing |

---

## External blockers (open)

| ID | Status | Why code alone cannot close |
|---|---|---|
| **RT-001** | OPEN / EXTERNAL | Customer corpus + accuracy protocol + ≥2 experts |
| **RT-002** | OPEN / EXTERNAL | Customer-approved norm pack + approval_ref |
| **RT-003** | OPEN / EXTERNAL | Federated MEP scope memo + system-aware evidence |

**Checkpoint:** **`NO_GO`**

---

## Risk register (Phase 0 — observational)

Severity ranking for next phases (does not close findings):

| Priority | Theme | Residual risk | Suggested Master phase |
|---|---|---|---|
| P0 | Frontend build red | Ship gate broken on `api.ts` Blob typing | Phase 9 / small API fix phase after Phase 1 start |
| P0 | Dirty tree vs committed | Local hardening not on `origin/main`; dual baselines | Commit only on explicit user request |
| P0 | False-pass / MEP required | Local `capability_policy` exists uncommitted; committed tree may differ | Phase 1 verify on both states |
| P1 | Persistence / orphans | Local commit markers + orphan CLI uncommitted | Phase 3 |
| P1 | Audit JSONL fail-closed | Local review store hardening uncommitted | Phase 5 |
| P1 | Upload / tenancy | Local magic-byte, zip limits, quotas, ACL tests uncommitted | Phase 4 |
| P2 | Jobs lease/heartbeat | Crash recovery incomplete per prior residual notes | Phase 6 |
| P2 | Advisory ON/OFF full matrix | Unit stubs ≠ use-case integration completeness | Phase 8 |
| EXT | RT-001/002/003 | Customer evidence | Phase 10 only |

---

## False-pass map (baseline hypotheses)

Observed from prior audits + local uncommitted policy (to be re-proven in Phase 1 against committed + working tree):

1. Required capability `SKIPPED` / `NOT_VERIFIED` / `FAILED` / `MISSING` must block `summary.passed` under `samolet_pilot` / `production`.
2. Quantity / MEP / schema exceptions must not degrade to WARNING-only with pass.
3. Empty OCR / zero annotations ≠ OK.
4. `calculation_match` NOT_VERIFIED blocks pass; correctness remains NOT_IMPLEMENTED.
5. Norm pack without `approval_ref` cannot be customer-approved / sign-off eligible.
6. Advisory ON/OFF must not change deterministic finding set or `passed`.
7. Generic IfcClash ≠ MEP system-aware OK.

---

## Claims drift check

- Claims Lock still asserts **NO_GO** and forbids closing RT-001/002/003 without customer evidence.
- Fixture F1 / SLA / BCF structural success **must not** be reworded as customer metrics, CDE-ready, or production-ready.
- Local CLAIMS_LOCK edits (dirty) are honesty-only; Phase 0 does not treat them as released.

---

## Undocumented / dual-state behavior

- Working-tree gates include uncommitted hyperdeep hardening; **committed-only** gates were not re-run on a clean checkout (would require stash/destructive ops — **not performed**).
- `npm ci` skipped due to existing `node_modules` — lockfile freshness **NOT_VERIFIED** this run.
- BCF XSD consumer validation reported `xsd_status: not_configured` in handoff output.
- Enterprise S3/Postgres paths require extras; filesystem fallback production policy needs Phase 4 confirmation.

---

## Phase 0 deliverables

| Artifact | Path |
|---|---|
| Baseline report | `audit/reports/RED_TEAM_BASELINE_2026_07_18.md` |
| Command evidence | `audit/evidence/baseline-command-results-2026-07-18.json` |

**Release recommendation after Phase 0 alone:** **`NO_GO`** (unchanged). External blockers open; frontend build failed; local patches not committed.

---

## Stop rule

Phase 0 complete. **Await explicit instruction to start Phase 1** (sign-off hardening).  
Do not advance to VLM / GraphRAG / “smart” analysis until false-pass, provenance, tenancy, persistence, and audit integrity are closed.
