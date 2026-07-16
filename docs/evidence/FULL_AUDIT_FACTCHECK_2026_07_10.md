# AeroBIM Full Audit & Fact-Check — 2026-07-10 (internal self-audit)

**Scope:** `c:\plans\AeroBIM` live tree vs public README / capability claims  
**Author relationship:** self (internal self-audit — not an independent/external audit)  
**Method:** Static inspection + live `pytest` + live extraction gate + standards check  
**Prior audits:** `docs/archive/05-fact-check-audit.md` (2026-04-12), `docs/evidence/public-surface-factcheck-2026-05-21.md`  
**Hub:** this file supersedes stale metrics in README for audit purposes until README is corrected  
**Deep follow-up:** [`ACADEMIC_DEEP_AUDIT_2026_07_10.md`](ACADEMIC_DEEP_AUDIT_2026_07_10.md) — security/correctness/integrity finding register

---

## Executive verdict

| Area | Verdict |
|------|---------|
| Product architecture (5-layer Clean Architecture) | **PASS** |
| Domain purity / DI composition root | **PASS** (minor tool exceptions) |
| HTTP API surface (README table) | **PASS** |
| Core BIM capabilities (IFC / IDS / BCF / reports) | **PASS** |
| Russian AEC extraction gate (F1 ≥ 0.70) | **PASS** (live macro F1 ≈ **0.86**) |
| Backend tests | **PASS** (**299 passed**, 2 skipped) |
| Frontend viewer stack (web-ifc + Three.js + 2D overlay) | **PASS** (in-tree) |
| Standards positioning (IFC / IDS / BCF) | **PASS** (external) |
| README port/adapter/token counts | **FAIL** (stale) |
| README LOC claims | **FAIL** (severely understated) |
| ConflictKind marketing row | **PARTIAL** (3 of 6 kinds listed) |
| Raster capability row | **PARTIAL** (deterministic path live; “advanced” still planned) |
| April 2026 archive open-gaps | **STALE** (several gaps now closed) |

**Bottom line:** AeroBIM is a **real, testable openBIM validation product**. Functional claims hold. The main integrity issues are **stale README metrics** and **oversimplified taxonomy/marketing rows**, not fake capabilities.

---

## Live runtime evidence (2026-07-10)

| Check | Command | Result |
|-------|---------|--------|
| Backend tests | `backend/.venv/Scripts/python.exe -m pytest tests -q` | **299 passed, 2 skipped** in 5.50s |
| Extraction quality | `PYTHONPATH=src python -m aerobim.tools.evaluate_extraction --min-macro-f1 0.70` | **PASS**, `macro_f1 ≈ 0.86` |
| Test function count | `def test_` across `backend/tests/` | **303** definitions |
| Non-empty LOC `src/aerobim` | Python line count | **~7 630** |
| Non-empty LOC `tests` | Python line count | **~7 032** |

Matches prior evidence doc (2026-05-21: 299/2, F1 ≈ 0.86).

---

## Claim-by-claim matrix (README)

| # | Claim | Verdict | Evidence |
|---|-------|---------|----------|
| 1 | Five-layer Clean Architecture | **PASS** | `backend/src/aerobim/{core,domain,application,infrastructure,presentation}/` |
| 2 | Domain → no infra imports | **PASS** | Layer tests + zero infra imports in `domain/` |
| 3 | `bootstrap_container()` composition root | **PASS*** | `infrastructure/di/bootstrap.py`; `main.py` uses it. *Alternate mini-container in OpenAPI export tool only |
| 4 | “9 ports → 12 adapters → 13 tokens” | **FAIL** | Live: **13** Protocol ports (12 in `ports.py` + `StructuredLogger`), **~17** adapter classes, **18** DI tokens in `Tokens` |
| 5 | LOC ~1.9K src / ~1.8K tests | **FAIL** | Live ~7.6K / ~7.0K non-empty Python lines |
| 6 | Tests “290+” | **PASS** | 303 defs; 299 run + 2 optional skips |
| 7 | All README API routes | **PASS** | 13 routes in `presentation/http/api.py` match README table |
| 8 | IFC2x3 / IFC4 / IFC4x3 fixtures | **PASS** | `samples/ifc/` schema headers |
| 9 | IDS 1.0 via IfcTester | **PASS** | Adapter + samples; IDS 1.0 is buildingSMART final standard (Jun 2024) |
| 10 | ConflictKind hard / unit-mismatch / ambiguous | **PARTIAL** | Code has **6** kinds: hard-conflict, unit-mismatch, stage-mismatch, version-mismatch, soft-conflict-within-tolerance, ambiguous-mapping (`domain/models.py:48-78`) |
| 11 | BCF 2.1 stable + BCF 3.0 experimental | **PASS** | `export_bcf` / `export_bcf3`; `?version=3` on export route |
| 12 | ObjectStore + Local/S3 + PostgresAuditStore | **PASS** | Port + adapters + bootstrap wiring |
| 13 | RasterDrawingAnalyzer naming | **PASS** | Port + adapter + DI token `raster_drawing_analyzer` |
| 14 | Extras clash / docling / raster / enterprise | **PASS** | `pyproject.toml` optional extras |
| 15 | Russian AEC: 10 docs, 50 reqs, F1≥0.70 | **PASS** | Manifest + live gate F1 ≈ 0.86 |
| 16 | Frontend web-ifc + Three.js + 2D overlay | **PASS** | `frontend/package.json`, viewer + drawing evidence panels |
| 17 | Revit plugin planned | **PASS** | Docs-only under `clients/revit-plugin/` |
| 18 | Advanced raster “🔜 Planned” | **PARTIAL** | Deterministic OCR raster path is **live**; “advanced/non-deterministic” remains planned — README row is ambiguous |
| 19 | CI badge / workflows | **PASS** | `.github/workflows/ci.yml` (lint, mypy, pytest, benchmarks, extraction, openapi) |
| 20 | MIT license | **PASS** | `LICENSE` |
| 21 | README local doc links | **PASS** | Spot-checked linked paths exist |

\*OpenRebar evidence verifier is hard-wired in bootstrap (no dedicated DI token) — low severity.

---

## Live inventory (corrected counts)

### Domain ports (13)

From `domain/ports.py` (12) + `domain/logging.py` (`StructuredLogger`):

`RequirementExtractor`, `NarrativeRuleSynthesizer`, `DrawingAnalyzer`, `RasterDrawingAnalyzer`, `IfcValidator`, `IdsValidator`, `RemarkGenerator`, `AuditReportStore`, `ObjectStore`, `AnalyzeProjectPackageJobStore`, `ExternalEvidenceVerifier`, `ClashDetector`, `StructuredLogger`

### DI tokens (18)

`SETTINGS`, `LOGGER`, `REQUIREMENT_EXTRACTOR`, `NARRATIVE_RULE_SYNTHESIZER`, `DRAWING_ANALYZER`, `RASTER_DRAWING_ANALYZER`, `IFC_VALIDATOR`, `IDS_VALIDATOR`, `CLASH_DETECTOR`, `REMARK_GENERATOR`, `OBJECT_STORE`, `AUDIT_REPORT_STORE`, `ANALYZE_PROJECT_PACKAGE_JOB_STORE`, `VALIDATE_IFC_AGAINST_IDS_USE_CASE`, `ANALYZE_PROJECT_PACKAGE_USE_CASE`, `SUBMIT_ANALYZE_PROJECT_PACKAGE_JOB_USE_CASE`, `GET_ANALYZE_PROJECT_PACKAGE_JOB_STATUS_USE_CASE`, `ANALYZE_PROJECT_PACKAGE_JOB_RUNNER`

### Notable adapters (wired)

`IfcOpenShellValidator`, `IfcTesterIdsValidator`, `IfcClashDetector`, `StructuredRequirementExtractor`, `NarrativeRuleSynthesizer`, `StructuredDrawingAnalyzer`, `RasterDrawingAnalyzer`, `TemplateRemarkGenerator`, `LocalObjectStore` / `S3ObjectStore`, `FilesystemAuditStore` / `PostgresAuditStore`, `InMemoryAnalyzeProjectPackageJobStore`, `JsonStructuredLogger`, `OpenRebarEvidenceVerifier` (direct `new`)

---

## External standards fact-check

| Standard | AeroBIM claim | External status | Verdict |
|----------|---------------|-----------------|---------|
| IDS 1.0 | Primary portable requirement language | buildingSMART final standard (approved Jun 2024) | **PASS** |
| IFC / IfcOpenShell | Canonical model substrate | Industry-standard open IFC toolkit | **PASS** |
| BCF | Issue/export coordination | buildingSMART issue exchange (file + API roadmap) | **PASS** |
| ISO 19650-lite in reports | Stage/revision/container context | Lite metadata — not full ISO 19650 CDE claim | **PASS with boundary** |
| ISO 12006-3 ε-tolerance | Tolerance algebra | Domain-specific implementation claim — code present; formal ISO conformance not independently certified here | **PARTIAL / implementation-backed** |

---

## Drift vs prior audits

### Still accurate from April 2026 archive

- Five-layer backend, domain purity, composition root
- Frontend is real review shell (not docs-only)
- Revit plugin still docs-first
- Clash optional extra with graceful fallback

### Now outdated in April archive § gaps

| April gap | Current status |
|-----------|----------------|
| No benchmark/throughput rail | **CLOSED** — packs + CI `benchmark-smoke` |
| No async job execution | **CLOSED** — submit/poll endpoints |
| No ifcclash integration test | **CLOSED** — optional adapter tests |
| Incomplete HTTP slice (7 routes) | **CLOSED** — 13 routes documented |

### May 2025-21 public-surface fact-check

Still aligned: no AI-vendor branding in active docs; `RasterDrawingAnalyzer` rename; EN/RU split; F1 ≈ 0.86; 299/2 tests.

---

## Blind spots / residual risks

| Risk | Severity | Notes |
|------|----------|-------|
| Stale README metrics (ports/LOC) | **High** (docs integrity) | Misleads reviewers / publication packets |
| Frontend not in main CI | **Medium** | Live-smoke only in release-readiness workflow |
| Editable install flaky in local `.venv` | **Medium** | `pip install -e` failed in this session; tests ran via path; tools needed `PYTHONPATH=src` |
| ConflictKind oversimplified in README | **Medium** | 3 advertised vs 6 implemented |
| Raster “planned” vs live OCR | **Medium** | Ambiguous marketing |
| OpenRebar verifier outside DI tokens | **Low** | Atomic-delivery smell |
| Formal ISO 12006-3 / 19650 certification | **Low** | Implementation claims ≠ certified conformance |
| GitHub remote CI badge live status | **UNVERIFIABLE here** | Badge URL present; remote Actions not re-fetched |

---

## Recommended corrections (docs)

1. README architecture blurb → **13 ports / ~17 adapters / 18 DI tokens** (or define counting rules).
2. README structure → LOC **~7–8K src / ~7K tests** (state measurement method).
3. ConflictKind row → list all 6 kinds or link `domain/models.py`.
4. Split raster: “Deterministic PDF/OCR (`.[raster]`) ✅” vs “Advanced non-deterministic raster 🔜”.
5. Mark April archive gaps as historical; point to this 2026-07-10 audit.
6. Optionally add frontend unit/smoke to main CI or explicitly label as release-readiness-only.

---

## What is *not* claimed (honest boundary)

- Not a full CDE / authoring BIM suite
- Not a certified ISO 19650 product
- Not “AI/LLM product” (deterministic extraction baseline)
- Not production Coinbase / unrelated V33 scope
- Revit plugin not implemented
- Advanced non-deterministic drawing vision not shipped

---

## Related files

| Path | Role |
|------|------|
| `README.md` / `README.ru.md` | Public surface (needs metric refresh) |
| `docs/archive/05-fact-check-audit.md` | April 2026 audit (partially stale) |
| `docs/evidence/public-surface-factcheck-2026-05-21.md` | Language/rename fact-check |
| `docs/06-architecture-reference.md` | Architecture SSOT |
| `docs/pilot-claim-boundary-2026.md` | Pilot claim boundary |
| `backend/tests/` | Live verification rail |
| `samples/benchmarks/russian-aec-ground-truth.json` | Extraction corpus |
