# CRITICAL BLOCKERS — Samolet Checkpoint

**Operational freeze SHA:** `8efbef8fa5191ef8d6d68841f54fb1e415ae1a9b` (2026-07-17).  
**Historical Red Team freeze:** `c0c4b2b` — see `CLAIMS_LOCK_2026_07_17.md` (pre-remediation narrative; do not treat defect prose below CLOSED tables as current).  
Severity key: BLOCKER / CRITICAL / HIGH / MEDIUM / LOW.

**Checkpoint verdict:** still **`NO_GO`** (RT-001 / RT-002 / RT-003 open).

## Closed in remediation commit (2026-07-17)

| ID | Status | Evidence |
|---|---|---|
| RT-004 | **CLOSED** | `require_clash` → SKIPPED clash ⇒ FAILED + `passed=false`; `tests/test_p0_remediation_fail_closed.py` |
| RT-005 | **CLOSED** | `AuthPrincipal` + `principal_may_access_report` on report/IFC/preview/export/review; ACL tests in P0 suite |
| RT-006 | **CLOSED** | `frontend` vitest **21 passed** |
| RT-007 | **CLOSED** | `finding_id` / `evidence_refs` / `source_id` stamped + persist reject; provenance helpers |
| RT-013 | **CLOSED** | one-sided empty revision ⇒ conflict; drawings in identity collection |
| RT-014 | **CLOSED** | raster requested+analyzer+zero annotations ⇒ FAILED; bSI ERROR under `require_bsi_schema` |
| RT-015 | **CLOSED** | Postgres→FS fallback only in `dev`; non-dev re-raises |
| RT-009 | **CLOSED** | this remediation commit freezes prior dirty seams + P0 |

Still open for checkpoint: **RT-001, RT-002, RT-003** (customer/MEP blocked).  
Evidence wave (2026-07-17): RT-008 **PARTIAL** (structural T1); RT-010/011/012 honesty closed for fixture/API surface; CDE import + customer SLA still open.  
I0–I7 + Red Team remediations (2026-07-17): see `CLAIMS_LOCK_2026_07_17.md` · Track E close `CLAIMS_LOCK_2026_07_17.md` — residual honesty CLOSED; checkpoint still **NO_GO**. Next: I8a / customer RT-001/002/003 — `docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md`.

## Closed in evidence wave (2026-07-17)

| ID | Status | Evidence |
|---|---|---|
| RT-008 | **PARTIAL** | `audit/evidence/bcf-structural-handoff-2026-07-17.json`; `cde_import=NOT_VERIFIED` |
| RT-010 | **CLOSED** | `claim_labels` on reinforcement-digest + `calculation_correctness=NOT_IMPLEMENTED` |
| RT-011 | **CLOSED** | `GET /v1/system/capabilities` + ReportCapabilities honesty fields |
| RT-012 | **CLOSED** (fixture honesty) | schema 1.2.0 `audit/evidence/samolet-sla-fixture-honesty-2026-07-17.json`; customer SLA still НЕ ДОКАЗАНО |

---

### RT-001 — Customer accuracy / >90% not evidenced
- **Severity:** BLOCKER  
- **Category:** Claims / Evaluation  
- **Exact file:** `docs/evidence/tz-matrix-status-latest.json`, `domain/architecture.py::PrecisionClaim`  
- **Observed:** `customer_corpus_present=false`; F1≈0.86 on fixture only  
- **Expected:** customer corpus + ≥2 adjudicators before any product accuracy claim  
- **Reproduction:** `python -m aerobim.tools.evaluate_extraction --min-macro-f1 0.70`  
- **Impact:** Checkpoint fails if accuracy KPI presented as achieved  
- **Fix:** Keep withheld; run customer intake protocol; do not raise claims  
- **Verification:** PrecisionClaim.publishable true only with customer + adjudicators≥2  
- **Engineering readiness (2026-07-17):** protocol aligned (`dual_independent` + `agreement-template.json` + runbook `--agreement-json`) — see `pilot-claim-boundary-2026.md`. **Product HOLD** until customer corpus.  

### RT-002 — Approved norm pack absent
- **Severity:** BLOCKER  
- **Category:** Norms  
- **Exact file:** `infrastructure/adapters/json_norm_rule_pack_loader.py`, partners TZ tails  
- **Observed:** synthetic/draft packs only; loader + schema require full `approval` object for `customer_approved`/`approved` (ref-only rejected)  
- **Expected:** signed customer pack with edition/clause/jurisdiction  
- **Reproduction:** inspect samples/norm packs; `customer_corpus_present`  
- **Impact:** «проверка норм» cannot be signed off  
- **Fix:** customer pack intake; immutable version store already partial  
- **Verification:** pack load + analyze with FAILED/OK capability + hash reproducibility  
- **Engineering readiness (2026-07-17):** schema↔loader parity closed. **Product HOLD** until signed pack.  

### RT-003 — MEP system-aware clash not runtime
- **Severity:** BLOCKER (if claimed) / CRITICAL (gap honesty)  
- **Category:** MEP / Clash  
- **Exact file:** `domain/mep.py`, `docs/roadmap/MEP_SYSTEM_CLASH_GAP_2026_07.md`  
- **Symbol:** `UnconfiguredMepSystemGraphProvider` — **DI-wired** via `Tokens.MEP_SYSTEM_GRAPH_PROVIDER` in `bootstrap_container` (I2a); still raises / probe → `NOT_VERIFIED`  
- **Observed:** Generic `IfcClashDetector` only; system-aware MEP clash **not delivered**; agent scaffold returns `degraded`  
- **Expected:** system graph + intersection matrix + clearance semantics on federated IFC  
- **Impact:** MEP TZ row NOT VERIFIED — wiring ≠ capability  
- **Fix:** Do not claim delivered; wait for federated IFC + real provider  
- **Verification:** `GET /v1/system/capabilities` → `mep_system_clash=not_verified`; architecture tests  
- **Engineering readiness (2026-07-17):** honesty labeling updated. **Product HOLD** until RT-003 evidence.  

### RT-004 — Clash SKIPPED does not block pass
- **Severity:** CRITICAL  
- **Category:** Capability honesty / False pass risk  
- **Exact file:** `application/use_cases/analyze_project_package.py::_run_clash_detection`, `application/services/signoff_policy.py`  
- **Observed:** missing optional clash stack → `CapabilityState.SKIPPED` → empty results → pass allowed  
- **Expected:** For Samolet packages requiring clash, missing engine must be FAILED or explicit policy gate  
- **Reproduction:** run analyze without `ifcclash` installed; inspect `capabilities.clash`  
- **Impact:** Green report without geometric coordination work  
- **Fix:** Profile flag `require_clash=true` for pilot packages; SKIPPED→FAILED under that profile  
- **Verification:** negative test: require_clash + missing dep ⇒ `summary.passed=false`  

### RT-005 — No tenant / object isolation
- **Severity:** BLOCKER (security)  
- **Category:** API security  
- **Exact file:** `presentation/http/api.py` (`/v1/reports/{report_id}/source/ifc`, drawing preview, BCF export)  
- **Observed:** Auth is shared bearer/OIDC; authorization is not project/tenant scoped; report UUID knowledge grants artifact access  
- **Expected:** object-level ACL / tenant binding  
- **Reproduction:** authenticate with valid token; GET another report’s IFC by ID  
- **Impact:** data leakage across projects in shared deployment  
- **Fix:** bind reports to tenant/project; authorize before artifact fetch  
- **Verification:** negative API test cross-tenant denied  

### RT-006 — Frontend tests failing
- **Severity:** CRITICAL  
- **Category:** Reproducibility / Review UX  
- **Exact file:** `frontend/src/App.test.tsx`  
- **Observed:** `npm test` exit 1; 3 failures in review-shell smoke / filters / 2d panel  
- **Expected:** green review shell tests in clean env  
- **Reproduction:** `cd frontend && npm test`  
- **Impact:** HITL review path not proven  
- **Fix:** fix UI contract assertions; re-run until green  
- **Verification:** `npm test` exit 0  

### RT-007 — Finding contract incomplete vs auditor mandate
- **Severity:** CRITICAL  
- **Category:** Domain contracts / Provenance  
- **Exact file:** `domain/models.py::ValidationIssue`, `domain/architecture.py::EvidenceRef`  
- **Observed:** Missing mandatory `finding_id`, `source_refs`, `evidence_refs`, `capability`, `document_identity` on findings; `EvidenceRef` exists but is not enforced on issues  
- **Expected:** every finding bindable to source+rule+evidence  
- **Impact:** report can lose provenance; weak audit trail for Samolet  
- **Fix:** extend ValidationIssue; migration for serializers; reject persist without evidence  
- **Verification:** contract tests + mutation removing provenance must fail  

### RT-008 — BCF interoperability not evidenced beyond unit ZIP
- **Severity:** HIGH (CRITICAL if BCF claimed “ready for CDE”)  
- **Category:** Reporting  
- **Exact file:** `infrastructure/adapters/bcf_report_exporter.py`, dirty `bcf_consumers.py`  
- **Observed:** Export ZIP + in-repo dual consumers/tests; **no** saved independent CDE import artifact  
- **Expected:** structural + consumer import evidence under `audit/evidence/`  
- **Impact:** handoff claim fails  
- **Fix:** export sample → import in external tool → save screenshot/log hash  
- **Verification:** evidence file referenced from matrix  

### RT-009 — Dirty tree / uncommitted seams treated as shipped
- **Severity:** HIGH  
- **Category:** Release integrity  
- **Exact file:** git status vs SHA `c0c4b2b`  
- **Observed:** DocumentIdentity extension, revision-merge guard, idempotency, BCF consumers uncommitted  
- **Expected:** checkpoint evaluates committed artifacts only, or explicitly freezes dirty tree  
- **Impact:** false readiness if demo uses local dirty code  
- **Fix:** commit atomic slices or revert; re-baseline  

### RT-010 — Independent calculation verification absent
- **Severity:** HIGH  
- **Category:** Calculation / TZ  
- **Observed:** digest + numeric cross-compare / OpenRebar path  
- **Expected:** separate “correctness verification” only with control formula/solver identity  
- **Allowed wording:** сверка результатов PARTIAL; независимая проверка НЕ РЕАЛИЗОВАНО  

### RT-011 — DWG/DXF / CV human-level missing
- **Severity:** HIGH  
- **Category:** 2D  
- **Observed:** documented missing; OCR extra absent in env  
- **Allowed wording:** НЕ РЕАЛИЗОВАНО / ADVISORY_ONLY  

### RT-012 — SLA not published with machine+package evidence
- **Severity:** HIGH  
- **Category:** Performance  
- **Observed:** tool + stage budgets (dirty); no customer package measurement artifact in this audit freeze  
- **Allowed wording:** НЕ ДОКАЗАНО for customer комплект ≤30 мин  

---

### RT-013 — Revision guard incomplete (empty revision / drawings out of scope)
- **Severity:** HIGH  
- **Category:** Document identity  
- **Exact file:** `domain/ingestion.py::revisions_conflict`, `analyze_project_package.py::_collect_identity_sources`  
- **Observed:** Conflict only if **both** revisions non-empty; drawing sources not in identity set  
- **Expected:** AMBIGUOUS / REQUIRES_HITL when revision missing on one side; drawings in identity scope  
- **Evidence:** Architecture layer audit (session); wording SSOT: [`CLAIMS_LOCK_2026_07_17.md`](CLAIMS_LOCK_2026_07_17.md)  

### RT-014 — Soft empty-success edges (raster OK + empty OCR; bSI WARNING)
- **Severity:** HIGH  
- **Category:** Capability honesty  
- **Exact file:** analyze `_build_capabilities` (raster OK if analyzer configured); `_submit_bsi_validation` WARNING path  
- **Observed:** Empty OCR yield can still look capability-OK; remote schema WARNING may not fail pass  
- **Expected:** Explicit yield/coverage gates; schema pre-gate policy for pilot packages  
- **Evidence:** Architecture layer audit (session); wording SSOT: [`CLAIMS_LOCK_2026_07_17.md`](CLAIMS_LOCK_2026_07_17.md)  

### RT-015 — Storage fallbacks may hide enterprise misconfig
- **Severity:** HIGH  
- **Category:** Reliability / ops  
- **Exact file:** `infrastructure/di/bootstrap.py::_build_audit_report_store`  
- **Observed:** Postgres init failure always falls back to filesystem (not only in dev); S3/Redis fall back in dev  
- **Expected:** Non-dev fail-closed when configured enterprise store is required  
- **Evidence:** Architecture layer audit (session); wording SSOT: [`CLAIMS_LOCK_2026_07_17.md`](CLAIMS_LOCK_2026_07_17.md)  

### RT-016 — Published SLA evidence is fixture-microscopic
- **Severity:** HIGH  
- **Category:** SLA claims  
- **Exact file:** `docs/evidence/samolet-sla-pilot-moscow-2026-05-21.json`  
- **Observed:** `sla_pass: true` on tiny Moscow fixture (~0.01 min class), not customer комплект  
- **Expected:** Measured SLA only with package hash + sizes + machine + cold/warm  
- **Evidence:** Claims/TZ audit (session); wording SSOT: [`CLAIMS_LOCK_2026_07_17.md`](CLAIMS_LOCK_2026_07_17.md) · claim boundary: [`../../docs/pilot-claim-boundary-2026.md`](../../docs/pilot-claim-boundary-2026.md)  

### RT-017 — Advisory OFF==ON test is narrow
- **Severity:** MEDIUM  
- **Category:** Contour isolation  
- **Exact file:** `tests/test_architecture_seams.py::test_advisory_off_equals_advisory_on_for_summary_passed`  
- **Observed:** Side-call to IDS-assist stub between empty analyzes; does not toggle real OCR/CV/LLM path inside UC  
- **Expected:** Full report-hash / deterministic-findings equality under advisory feature flags  
- **Evidence:** Claims/TZ audit (session); wording SSOT: [`CLAIMS_LOCK_2026_07_17.md`](CLAIMS_LOCK_2026_07_17.md) · claim boundary: [`../../docs/pilot-claim-boundary-2026.md`](../../docs/pilot-claim-boundary-2026.md)  
- **Engineering status (2026-07-17):** **REMEDIATED** via RT-E (`tests/test_red_team_signoff_remediation.py::test_rt_e_*`) — real UC path, advisory ON/OFF; deterministic findings + `summary.passed` equality. Does **not** close RT-001/002/003 or flip **NO_GO**.  

---

**Checkpoint rule:** any of RT-001..RT-005 presented as “done” ⇒ automatic **NO_GO**.
