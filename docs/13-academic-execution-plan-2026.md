---
title: "AeroBIM Academic Execution Plan 2026"
status: active
version: "1.0.0"
last_updated: "2026-04-25"
tags: [aerobim, plan, academic, openBIM, roadmap]
---

# AeroBIM Academic Execution Plan 2026

Formal roadmap derived from the April 2026 external academic audit of **KonkovDV/AeroBIM**.
Structured into three delivery iterations aligned with (A) production hygiene and current
openBIM standards, (B) enterprise-scale infrastructure, and (C) research-grade validation.

References: `docs/10-academic-audit-and-recommendations-ru.md` (internal prior art),
`docs/11-rebaseline-execution-plan.md` (active wave tracking).

---

## Audit Summary (April 2026)

### Confirmed Strengths

| Area | Assessment |
|---|---|
| Architecture | 5-layer Clean Architecture, port/adapter, constructor DI — high engineering maturity |
| Requirement modelling | IDS as contract, ε-tolerance algebra (ISO 12006-3), SourceKind provenance |
| Cross-modal pipeline | IFC + IDS + text spec + calculation + 2D drawing in single deterministic pipeline |
| BCF interoperability | BCF 2.1 export with viewpoint + markup; consumable by coordination tools |
| Browser review shell | `web-ifc + Three.js`, IFC GUID isolate, 2D evidence overlay, deep links |
| OpenRebar provenance | SHA-256 digest chain, contract ID gate, solver fallback detection |
| Benchmark rail | 3 canonical packs, CI artifact publishing, threshold governance |

### Identified Gaps (Priority Order)

| Gap | Standard / Reference | Priority |
|---|---|---|
| BCF version: only 2.1, no 3.0 | buildingSMART BCF 3.0 | P0 |
| ISO 19650 lifecycle context (stage, CDE, EIR) | ISO 19650-1/-2 | P0 |
| Cross-doc conflict taxonomy (no `ConflictKind`) | internal — domain model | P1 ✅ |
| Severity policy for contradictions (hardcoded WARNING) | internal — settings | P1 ✅ |
| No typed quantity/unit abstraction | UCUM / ISO 80000 | P1 |
| Provenance generalisation: OpenRebar-specific | internal — domain port | P1 |
| Storage: in-memory + filesystem only | production infra | P1 |
| AuthN: static Bearer only | OIDC / JWT RFC 7519 | P1 |
| bSDD term normalisation not present | buildingSMART bSDD | P2 |
| No precision/recall metrics for requirement extraction | NLP evaluation | P2 |
| No open benchmark dataset protocol | reproducible research | P2 |

> ✅ = completed in the same session as this plan was created.

---

## Iteration A — Production Hygiene + openBIM Standards (2–4 weeks)

**Goal:** close the most visible gaps against current buildingSMART standards and
bring the codebase to a defensible production baseline.

### A.1 — ConflictKind Taxonomy ✅ *Completed 2026-04-25*

**What shipped:**
- `ConflictKind` enum added to `domain/models.py`:
  `HARD_CONFLICT`, `UNIT_MISMATCH`, `STAGE_MISMATCH`, `VERSION_MISMATCH`,
  `SOFT_CONFLICT_WITHIN_TOLERANCE`, `AMBIGUOUS_MAPPING`.
- `ValidationIssue.conflict_kind: ConflictKind | None` — populated for all
  `CROSS_DOCUMENT` findings.
- `_classify_conflict_kind()` in use case: detects unit encoding divergence
  (SI normalisation path) vs hard value conflict vs ambiguous mapping.
- 214 backend tests passing, mypy clean.

**Rationale (academic):** distinguishing genuine value conflicts from unit-encoding
artefacts directly reduces false-positive contradiction rates in practice.  Enables
downstream consumers (CI gates, enterprise QA) to apply per-kind policies rather than
treating all contradictions as equally severe (cf. user audit §4.3).

### A.2 — Configurable Severity Policy for Cross-Document Contradictions ✅ *Completed 2026-04-25*

**What shipped:**
- `Settings.cross_doc_contradiction_severity: str = "warning"` — reads from
  `AEROBIM_CROSS_DOC_SEVERITY` env var; accepted values: `error`, `warning`, `info`.
- `AnalyzeProjectPackageUseCase` now takes `cross_doc_severity: str = "warning"` and
  converts to `Severity` at construction time.
- Bootstrap wires `cross_doc_severity` from `Settings`.
- `.env.example` documents `AEROBIM_CROSS_DOC_SEVERITY`.

**Rationale (academic):** enterprise delivery gates require operator-configurable
blocking criteria.  A hardcoded WARNING level makes the tool advisory-only regardless
of contractual strictness desired by the appointing party (cf. user audit §4.3, §5.1).

### A.3 — OpenAPI Contract Export + CI Gate

**Goal:** make the API contract a reproducible CI artifact; catch breaking changes early.

**Deliverables:**
1. `scripts/export_openapi.py` — starts a test FastAPI application instance, dumps
   `/openapi.json`, writes to `docs/openapi.json`.
2. CI step in `ci.yml` (`openapi-contract` job): runs export, uploads artifact.
3. `docs/openapi.json` committed to repository as human-readable baseline.
4. Optional diff gate: fail CI if schema changed without explicit flag.

**Verification:** CI artifact present per commit; diff shows on PR.

### A.4 — IFC Release Compatibility Matrix

### A.4 — IFC Release Compatibility Matrix ✅ *Completed 2026-04-25*


**What shipped:**
- `docs/ifc-compatibility-matrix.md` — feature matrix: IFC2x3 / IFC4 / IFC4x3, per-feature
  column (property sets, Qto naming, unit assignment, classification), degradation rules.
- `samples/ifc/wall-pset-ifc2x3.ifc` — minimal IFC2x3 fixture with Pset_WallCommon
  (FireRating=REI60) and BaseQuantities Pset (IFC2x3 naming for quantity sets).
- `samples/ifc/wall-pset-ifc4x3.ifc` — minimal IFC4x3 fixture with Pset_WallCommon
  and Qto_WallBaseQuantities.
- `tests/test_ifc_release_compatibility.py` — 5 parametric tests: IfcOpenShell opens
  all three releases, Pset_WallCommon.FireRating=REI60 confirmed in all, IDS validation
  passes on all, schema header assertions. Tests skip gracefully if IfcOpenShell/IfcTester
  not installed (offline environments).
- 244 backend tests passing (30 new), mypy clean.

**Rationale:** buildingSMART Compatibility Policy for ISO 16739-1 makes schema
evolution a first-class concern; users need to know which checks apply to IFC2x3
projects vs IFC4x3 (cf. user audit §3.2).

### A.5 — BCF 3.0 Experimental Export ✅ *Completed 2026-04-25*
---
**What shipped:**
- `infrastructure/adapters/bcf3_exporter.py` — BCF 3.0 ZIP exporter: `bcf.version`
  declares VersionId=3.0; `markup.bcf` uses BCF 3.0 structure (no XML namespace,
  `<Header>`, `<Comments>`, `<Viewpoints>` with Guid attr); `viewpoint.bcfv` has
  `Coloring` before `Visibility` (BCF 3.0 XSD order).
- `GET /v1/reports/{id}/export/bcf?version=3` (or `?version=3.0`) — BCF 3.0 output;
  default (`?version=2.1` or omitted) stays BCF 2.1 for backward compatibility.
- `tests/test_bcf3_exporter.py` — 25 tests: archive structure, version declaration,
  markup BCF 3.0 required fields, viewpoint element order, IFC GUID propagation,
  clash export, HTTP endpoint version switching (2.1 default, 3 → 3.0, unknown → 2.1).
- 244 backend tests passing, mypy clean.

**Rationale:** buildingSMART toolchain (Revit 2025+, Navisworks 2025, BIMcollab)
increasingly defaults to BCF 3.0; the `?version=3` opt-in minimises adoption friction
while keeping 2.1 as the stable default (cf. user audit §3.3).
## Iteration B — Enterprise Infrastructure (1–2 months)

### B.1 — Postgres Report Index + S3-Compatible Artifact Store

**Goal:** replace filesystem audit store with Postgres (report metadata) +
S3/MinIO (binary artifacts: IFC, PDF, BCF).

**Deliverables:**
1. `domain/ports.py` — add `ObjectStore` port (put / get / delete / presign).
2. `infrastructure/adapters/s3_object_store.py` — boto3-backed adapter; `/** @sota-stub */`
   until CI has MinIO sidecar.
3. `infrastructure/adapters/postgres_audit_store.py` — SQLAlchemy 2.x async adapter.
4. Alembic migration: `reports` table with report metadata, foreign key to artifacts.
5. `bootstrap.py` DI switch: filesystem → Postgres + S3 when `AEROBIM_DB_URL` is set.
6. Retention / TTL policy: `AEROBIM_REPORT_TTL_DAYS` (default: unlimited).

**Exit criteria:** full backend suite passes against Postgres + MinIO in CI.

### B.2 — Async Task Queue (Celery / arq)

**Goal:** decouple heavy analysis from HTTP request cycle with a real task queue.

**Deliverables:**
1. `domain/ports.py` — `TaskQueue` port (enqueue / result / cancel).
2. `infrastructure/adapters/arq_task_queue.py` — arq + Redis adapter.
3. Worker entrypoint: `python -m aerobim.worker` as separate process.
4. `POST /v1/analyze/project-package/submit` now enqueues to Redis;
   `GET /v1/analyze/project-package/jobs/{job_id}` polls arq.
5. In-memory store retained for dev/testing via `AEROBIM_USE_INMEMORY_JOBS=true`.

### B.3 — OIDC/JWT Authentication

**Goal:** replace static bearer with token-based auth suitable for multi-user deployment.

**Deliverables:**
1. `domain/ports.py` — `ITokenVerifier` port.
2. `infrastructure/adapters/oidc_token_verifier.py` — validates JWT with
   JWKS endpoint (Azure AD / Keycloak compatible).
3. `Settings.oidc_jwks_uri: str | None` — when set, OIDC mode active;
   static bearer falls back for dev when both are set.
4. Role claims: `viewer` (read reports), `reviewer` (submit jobs), `admin` (all).
5. Audit log: `POST /v1/analyze/*` writes structured log entry: `{user_id, action, timestamp}`.

### B.4 — ISO 19650 Lifecycle Context

**Goal:** attach delivery-stage and CDE context to validation requests and reports.

**Deliverables:**
1. `ValidationRequest` new optional fields:
   - `stage: str | None` — delivery stage (e.g. `"S0"`, `"S1"`, `"LOD200"`, `"LOD400"`).
   - `information_container_id: str | None` — CDE container identifier.
   - `revision: str | None` — document revision string.
   - `doc_status: Literal["WIP", "Shared", "Published", "Archived"] | None`.
2. `ValidationReport` carries these fields through to JSON/HTML/BCF output.
3. Report HTML template adds an "ISO 19650 context" section when `stage` is present.
4. No breaking change: all new fields are optional with `None` default.

---

## Iteration C — Research-Grade Validation (3–6 months)

### C.1 — Typed Quantity/Unit Abstraction

**Goal:** replace string-based unit fields with `Quantity(value: Decimal, unit: Unit)`
to eliminate unit-encoding divergence as a source of false contradictions.

**Design:**
- `domain/quantities.py`: `Unit` enum (LENGTH_M, AREA_M2, VOLUME_M3, ANGLE_RAD, DIMENSIONLESS, …)
  and `Quantity` frozen dataclass.
- `domain/unit_normaliser.py`: parse raw string → `Quantity`; output: `(canonical_unit, si_value)`.
- `ParsedRequirement.quantity: Quantity | None` (alongside existing `expected_value`/`unit` for
  backward compatibility).
- `_detect_cross_document_contradictions` uses `Quantity` comparison where available,
  string fallback otherwise.
- Unit provenance: track origin (IDS, text, drawing, IFC unit assignment).

### C.2 — Generalised External Evidence Provenance Port

**Goal:** lift OpenRebar provenance checks into a reusable `ExternalEvidenceProvenanceCheck`
domain abstraction usable for any external calculation report.

**Design:**
- `domain/ports.py` — `ExternalEvidenceVerifier` port:
  ```python
  def verify(evidence: Mapping[str, Any], policy: EvidencePolicy) -> list[ValidationIssue]
  ```
- `EvidencePolicy`: `expected_contract_id`, `expected_digest`, `severity_class_map`, `enforced_classes`.
- `infrastructure/adapters/openrebar_evidence_verifier.py` — current OpenRebar logic refactored
  as a concrete `ExternalEvidenceVerifier`.
- Ready to accept structural calculation reports, energy analysis, fire-compliance reports.

### C.3 — bSDD Term Normalisation

**Goal:** map property names extracted from text/IDS to buildingSMART bSDD URIs for
terminology-stable cross-project rule portability.

**Design:**
- `infrastructure/adapters/bsdd_term_mapper.py` — offline lookup table (bSDD export JSON)
  mapping common property names / Russian/English variants to `bsdd_uri`.
- `ParsedRequirement.bsdd_uri: str | None`.
- Report HTML: "Terminology-normalised" badge on requirements with resolved URIs.

### C.4 — Precision/Recall Benchmark Protocol

**Goal:** establish formal NLP evaluation metrics for requirement extraction quality.

**Design:**
- `samples/benchmarks/annotation/` — manual ground-truth annotation format:
  `{document_id, expected_requirements: [{rule_id, ifc_entity, property_name, expected_value, unit}]}`.
- `aerobim.tools.evaluate_extraction` — runs extractor over annotated documents,
  computes precision / recall / F1 per category.
- `samples/benchmarks/benchmark-extraction-quality.json` — quality baseline manifest.
- CI optional `benchmark-extraction-quality` job: advisory thresholds, publishes
  metrics as artifacts.

### C.5 — Reproducible Benchmark Report (Publication-Grade)

**Goal:** produce a self-contained benchmark report suitable for supplementary material
in a conference submission or arXiv preprint.

**Deliverables:**
1. `scripts/generate_benchmark_report.py` — runs all benchmark packs + extraction quality,
   captures `{platform, python_version, dep_versions, ifc_release, params}`, renders
   Markdown + HTML report.
2. `docs/benchmark-report-template.md` — template with: hypothesis, metrics, fixtures used,
   model version, dependency hash, results table, sensitivity analysis section.
3. CI artifact for every release tag.

---

## Dependency Graph

```
A.1 (ConflictKind) ✅ → C.1 (Typed Quantity) → C.2 (Provenance Port)
A.2 (Severity Policy) ✅
A.3 (OpenAPI CI) — independent
A.4 (IFC Matrix) — independent
A.5 (BCF 3.0) → B.1 (Postgres) [for artifact storage]
B.1 (Postgres) → B.2 (Task Queue)
B.3 (OIDC) — independent of B.1/B.2
B.4 (ISO 19650 context) — independent; can ship with A wave
C.3 (bSDD) — depends on stable ParsedRequirement schema
C.4 (Precision/Recall) — depends on ground-truth fixture set
C.5 (Benchmark Report) — depends on C.4
```

---

## Verification Rail

| Iteration | Gate |
|---|---|
| A.1, A.2 | backend suite (214 tests), mypy, ruff |
| A.3 | CI artifact + diff check |
| A.4 | parametric pytest over IFC2x3 + IFC4x3 fixtures |
| A.5 | BCF 3.0 export regression tests |
| B | Postgres + MinIO CI sidecar integration tests |
| C.4 | precision/recall ≥ 0.70 on annotated fixture set |

---

## References

| Standard | Version | Relevance |
|---|---|---|
| buildingSMART IDS | v1.0 (final) | requirement contract language |
| buildingSMART BCF | 3.0 | cross-tool issue collaboration |
| ISO 16739-1 | 2018 + IFC4x3 | IFC schema and compatibility policy |
| ISO 19650-1/-2 | 2018 | information management, EIR/CDE lifecycle |
| ISO 12006-3 | 2022 | tolerance algebra, ε-bands |
| buildingSMART bSDD | 2024 API | property/class dictionary |
| UCUM | v2.1 | unit code system |
| OWASP API Security | Top 10 2023 | API hardening baseline |
| RFC 7519 | JWT | token format for OIDC |
