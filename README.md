# AeroBIM

[Русская версия](README.ru.md)

[![CI](https://github.com/KonkovDV/AeroBIM/actions/workflows/ci.yml/badge.svg)](https://github.com/KonkovDV/AeroBIM/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Open-source **acceptance-criteria assistant** for openBIM packages (IFC + IDS + cross-document evidence).

AeroBIM runs a deterministic Shared-gate style check (ISO 19650 framing: evidence for *Shared*, not contractual *Published* authorization). It fuses IFC property/quantity checks, IDS, drawings, and calculation text into a single report with explicit capability honesty, finding provenance, and BCF **ZIP export**. Independent CDE import and customer accuracy claims remain **out of scope until evidenced**.

> **Checkpoint (2026-07-17):** Samolet TechLab Task 07 status is **`NO_GO`** until customer corpus, customer-approved norm pack, and MEP federated scope are evidenced ([RT-001/002/003](audit/reports/CRITICAL_BLOCKERS.md)). Claims SSOT: [`audit/reports/CLAIMS_LOCK_2026_07_17.md`](audit/reports/CLAIMS_LOCK_2026_07_17.md).

## Key Capabilities

Statuses below are **repository / fixture** capabilities unless marked otherwise. Optional extras and fail-closed policies govern whether a green `summary.passed` is honest.

| Capability | Status | Evidence level | Notes |
|---|---|---|---|
| IFC property/quantity validation (IfcOpenShell) | Available | fixture | IFC2x3 / IFC4 / IFC4x3 kernel |
| IDS 1.0 validation (IfcTester) | Available | fixture | Requested path fail-closed when misconfigured |
| Cross-document contradiction detection | Available | fixture | `ConflictKind` taxonomy (subset) |
| Configurable contradiction severity policy | Available | fixture | — |
| Drawing annotation ↔ IFC cross-validation | Available | fixture | Raster OCR path optional |
| ISO 12006-3 tolerance algebra (ε-band) | Available | fixture | — |
| Narrative text → requirements (deterministic regex) | Available | fixture | Not an LLM sign-off contour |
| Russian AEC extraction benchmark (fixture corpus) | Available | fixture | macro_f1 on fixtures ≠ product accuracy |
| ISO 19650-lite metadata on reports | Available | fixture | Stage/revision/container fields only — not a CDE product |
| Clash detection (IfcClash) | Optional extra | optional-extra | `.[clash]`; `capabilities.clash`; under `require_clash`, SKIPPED→FAILED |
| Report capability honesty (`ok`/`skipped`/`failed`/`missing`/…) | Available | fixture | FAILED blocks `summary.passed`; honesty surface via `/v1/system/capabilities` |
| Finding provenance (`finding_id`, `source_id`, `evidence_refs`) | Available | fixture | Persist reject if missing |
| Tenant / object ACL on report artifacts | Available | fixture | Bearer/OIDC principal + report `tenant_id` |
| BCF 2.1 / 3.0 ZIP export | Available | fixture (T1) | Structural + dual-consumer verified; **CDE import NOT VERIFIED (T2)** |
| OpenCDE BCF API push | Foundation | experimental | Not a substitute for T2 import proof |
| HTML / JSON report export | Available | fixture | — |
| Browser IFC viewer (`web-ifc` + Three.js) | Available | fixture | — |
| 2D problem-zone overlay | Available | fixture | — |
| Deterministic PDF text (PyMuPDF) | Available | core | — |
| Image OCR (RapidOCR) | Optional extra | optional-extra | `.[raster]`; zero-yield → FAILED when requested |
| DWG native analysis | Missing / Failed | — | Fail-closed without ODA; never OK |
| DXF via CadModelIngestor | Not verified | — | Optional ezdxf; honesty never OK |
| Human-level CV / drawing literacy | Missing | — | Explicit `MISSING` (OCR degrade ≠ VLM) |
| MEP system-aware clash | Not verified | — | DI-wired Unconfigured provider; not delivered |
| Independent calculation *correctness* | Not implemented | — | OpenRebar path = **match/сверка**, not solver verification |
| Frontend vitest review-shell | Green locally | release-readiness | **21** passed; not in main CI job |
| Customer accuracy >90% / approved norms | Blocked | customer | See Claims Lock |

## IFC Release Compatibility

| IFC Release | Schema | Validation Support | Notes |
|---|---|---|---|
| IFC2x3 | ISO 16739:2005 | ✅ Core | Most widely deployed; full property/quantity validation |
| IFC4 (IFC4 ADD2) | ISO 16739-1:2018 | ✅ Core | Pset naming normalised; unit assignment via `IfcUnitAssignment` |
| IFC4x3 | ISO 16739-1:2024 | ✅ Core | Alignment and infrastructure extensions; same validation kernel |

All three releases pass through the same `IfcOpenShellValidator` and `IfcTesterIdsValidator` adapters.
Pset/property name divergence between releases is surfaced as a `ValidationIssue` rather than a silent skip.
IFC2x3, IFC4, and IFC4x3 fixture files live in `samples/ifc/`.
See [`docs/ifc-compatibility-matrix.md`](docs/ifc-compatibility-matrix.md) for the formal compatibility matrix and per-feature degradation rules.

## BCF Evidence Ladder

| Tier | Status | Notes |
|---|---|---|
| BCF 2.1 ZIP export | Available (stable default) | `/v1/reports/{id}/export/bcf` |
| BCF 3.0 ZIP export | Experimental | `?version=3` |
| T1 structural + dual-consumer agreement | Evidenced | [`audit/evidence/bcf-structural-handoff-2026-07-17.json`](audit/evidence/bcf-structural-handoff-2026-07-17.json) |
| OpenCDE BCF API push | Foundation | `/export/bcf-api/push` — hub sync not a T2 substitute |
| T2 independent CDE import | **NOT VERIFIED** | [`audit/evidence/cde-import-proof/STATUS.json`](audit/evidence/cde-import-proof/STATUS.json) |

Forbidden wording until T2: “BCF ready for CDE”, “CDE interoperable”.

## Enterprise Storage Foundation

Iteration B.1 has started with a compatibility-first storage foundation:

- `ObjectStore` domain port for binary artifacts (`put/get/delete/presign`);
- `LocalObjectStore` for current local/runtime flows;
- `S3ObjectStore` for S3/MinIO-compatible buckets via optional enterprise extras;
- `PostgresAuditStore` foundation that adds a Postgres report-summary index while keeping full payload round-tripping on the existing JSON/object path;
- `AEROBIM_REPORT_TTL_DAYS` retention knob for persisted report payloads.

Current behaviour is intentionally safe-by-default:

- without enterprise extras, AeroBIM keeps working with local storage;
- when `AEROBIM_DB_URL` and enterprise dependencies are available, report summaries are indexed in Postgres;
- IFC source binaries and persisted drawing previews are stored behind the `ObjectStore` abstraction, so S3/MinIO rollout no longer requires HTTP contract changes.

## Quick Start

```bash
# Clone
git clone https://github.com/KonkovDV/AeroBIM.git
cd AeroBIM/backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install
pip install -e ".[dev,raster]"

# Optional extras
# pip install -e ".[clash]"    # enable geometry clash detection
# pip install -e ".[docling]"  # enable non-text document extraction
# pip install -e ".[enterprise]"  # enable S3/Postgres enterprise storage adapters

# Run tests
pytest tests -q

# Extraction quality gate (Russian AEC corpus)
python -m aerobim.tools.evaluate_extraction --min-macro-f1 0.70
python -m aerobim.tools.evaluate_detection_precision \
  --labels ../samples/benchmarks/detection-precision/labels-synthetic.json \
  --detections ../samples/benchmarks/detection-precision/detections-synthetic.json \
  --min-precision 0.6 --min-recall 0.6 --min-f1 0.6

# Seed one deterministic runtime smoke report
python -m aerobim.tools.seed_smoke_report

# Or run the full live review smoke chain in one command
python -m aerobim.tools.run_live_review_smoke

# Or run the baseline throughput rail against the representative benchmark pack
python -m aerobim.tools.benchmark_project_package --iterations 1 --warmup-iterations 0

# Or run the second fire-compliance benchmark profile explicitly
python -m aerobim.tools.benchmark_project_package --pack ../samples/benchmarks/project-package-fire-compliance.json --iterations 1 --warmup-iterations 0

# Or run the stress multisource benchmark profile explicitly
python -m aerobim.tools.benchmark_project_package --pack ../samples/benchmarks/project-package-stress-multisource.json --iterations 1 --warmup-iterations 0

# Start server
python -m aerobim.main
# → http://127.0.0.1:8080/health
```

## Local Quality Gate

Before pushing to `main`, run the same baseline checks used by CI:

```bash
cd AeroBIM/backend
python -m ruff format --check src tests
python -m ruff check src tests
python -m mypy src
pytest tests -q
```

If `ruff format --check` reports files to reformat, run:

```bash
python -m ruff format src tests
```

## Benchmarks and Evidence

Verified capabilities are backed by tests, API contracts, or persisted report artifacts. Planned / missing contours (DWG, human CV, MEP system clash, calculation *correctness*, customer accuracy) are explicit on `GET /v1/system/capabilities` and in the Claims Lock.

```bash
cd backend
python -m aerobim.tools.benchmark_project_package --iterations 1 --warmup-iterations 0
python -m aerobim.tools.measure_package_sla --corpus-kind fixture
python -m aerobim.tools.verify_bcf_structural_handoff
python -m aerobim.tools.run_ablation_study
python -m aerobim.tools.generate_benchmark_report --output-dir ../docs/evidence
python -m aerobim.tools.export_runtime_baseline
```

| Topic | Document |
|---|---|
| Claims lock (forbidden / allowed wording) | [audit/reports/CLAIMS_LOCK_2026_07_17.md](audit/reports/CLAIMS_LOCK_2026_07_17.md) |
| Claims × evidence matrix | [audit/reports/CLAIMS_EVIDENCE_MATRIX.md](audit/reports/CLAIMS_EVIDENCE_MATRIX.md) |
| Critical blockers / checkpoint | [audit/reports/CRITICAL_BLOCKERS.md](audit/reports/CRITICAL_BLOCKERS.md) |
| Claim boundary (pilot / publication) | [docs/pilot-claim-boundary-2026.md](docs/pilot-claim-boundary-2026.md) |
| Publication evidence pack | [docs/academic-publication-evidence-2026.md](docs/academic-publication-evidence-2026.md) |
| Annotation protocol (RU corpus) | [docs/annotation-protocol-2026.md](docs/annotation-protocol-2026.md) |
| Benchmark packs | [samples/benchmarks/README.md](samples/benchmarks/README.md) |
| Audit evidence (T1 BCF, SLA 1.2, intake gate) | [audit/evidence/](audit/evidence/) |

Throughput and F1 figures are environment-specific and **fixture-scoped** unless `corpus_kind=customer` and adjudication gates pass. Publish pack paths, CLI flags, machine fingerprint, and artifact hashes with any performance claim. Cite via [CITATION.cff](CITATION.cff) or [docs/CITATION.bib](docs/CITATION.bib).

## API Endpoints

| `GET` | `/v1/system/capabilities` | Static honesty surface (DWG/CV/MEP/calculation claim boundary) |
| `GET` | `/health` | Readiness probe |
| `POST` | `/v1/validate/ifc` | Validate IFC against requirements + IDS |
| `POST` | `/v1/analyze/project-package` | Multimodal validation (spec + calc + drawing + IDS + IFC) |
| `POST` | `/v1/analyze/project-package/reinforcement-digest` | OpenRebar provenance digest (**сверка** labels; not correctness verification) |
| `POST` | `/v1/analyze/project-package/submit` | Accept a same-process background analysis job for larger packages |
| `GET` | `/v1/analyze/project-package/jobs/{job_id}` | Poll async project-package job status |
| `POST` | `/v1/uploads` | Multipart document ingest; returns storage-relative `path` for analyze |
| `GET` | `/v1/reports` | List persisted reports with optional `project`, `discipline`, and `passed` filters |
| `GET` | `/v1/reports/{id}` | Get report by ID |
| `POST` | `/v1/reports/{id}/review-events` | Append HITL review telemetry (does not affect pass/fail) |
| `GET` | `/v1/reports/{id}/review-events` | List review events for a report |
| `GET` | `/v1/reports/{id}/review-kpi` | Aggregate triage/acceptance KPIs |
| `GET` | `/v1/reports/{id}/source/ifc` | Download the report-scoped IFC source for browser viewing |
| `GET` | `/v1/reports/{id}/drawing-assets/{asset_id}/preview` | Download a report-scoped drawing preview for 2D evidence overlays |
| `GET` | `/v1/reports/{id}/export/json` | Download JSON export |
| `GET` | `/v1/reports/{id}/export/html` | Download HTML export |
| `GET` | `/v1/reports/{id}/export/bcf` | Download BCF 2.1 ZIP by default; use `?version=3` for BCF 3.0 |

`POST /v1/analyze/project-package` also supports optional OpenRebar provenance fields:

- `reinforcement_report_path`: path (inside `AEROBIM_STORAGE_DIR`) to an OpenRebar canonical `*.result.json` report;
- `reinforcement_source_digest`: expected SHA-256 digest for report provenance fingerprint checks.
- `reinforcement_waste_warning_threshold_percent`: optional waste threshold (percent) for coordination warnings.
- `reinforcement_provenance_mode`: `advisory` (default) or `enforced` to escalate OpenRebar provenance warnings into blocking errors.

Use `/v1/analyze/project-package/reinforcement-digest` to generate `reinforcement_source_digest` directly from a stored OpenRebar report before calling project-package analysis.

For offline or CI shell workflows, use:

`python -m aerobim.tools.openrebar_provenance_digest <path-to-openrebar-result.json>`

When provided, AeroBIM adds cross-document warnings if:

- OpenRebar report contract ID is unexpected;
- OpenRebar optimizer indicates fallback master solver usage;
- OpenRebar master-problem strategy does not indicate a HiGHS-backed path;
- project context mismatches (`project_name` vs `metadata.projectCode`);
- supplied provenance digest does not match report fingerprint.
- reported `summary.totalWastePercent` exceeds the configured warning threshold.

## Architecture

Five-layer Clean Architecture with strict inward dependency direction:

```
core/          DI container, tokens, config (no project imports)
domain/        Immutable models, Protocol ports, logging contract
application/   Use case orchestration (requirement fusion, cross-doc detection)
infrastructure/ Adapters: IfcOpenShell, IfcTester, Docling, IfcClash, BCF, filesystem
presentation/  FastAPI HTTP API, correlation middleware
```

Infrastructure now also includes an artifact `ObjectStore` seam plus an optional Postgres summary-index adapter for Iteration B.1.

**20 domain ports** → **30 infrastructure adapters** → **28 DI tokens** — all wired in a single composition root (`bootstrap_container()`).
Report payloads include an explicit `capabilities` object (`ok` / `skipped` / `failed`) so optional engines (clash, IDS, unit scale, raster, schema) cannot silently look like a clean PASS. **Any `FAILED` capability forces `summary.passed=false`.**

## Configuration

All settings are read from environment variables (see [`backend/.env.example`](backend/.env.example)):

| Variable | Default | Description |
|---|---|---|
| `AEROBIM_HOST` | `127.0.0.1` | Bind address |
| `AEROBIM_PORT` | `8080` | Bind port |
| `AEROBIM_DEBUG` | `false` | Debug mode (also enables localhost CORS defaults when origins unset) |
| `AEROBIM_STORAGE_DIR` | `var/reports` | Report persistence directory |
| `AEROBIM_CORS_ORIGINS` | *(auto)* | Comma-separated CORS origins |
| `AEROBIM_ENV` | `development` | Environment name; non-dev requires bearer/OIDC (fail-closed) |
| `AEROBIM_API_BEARER_TOKEN` | *(unset)* | Bearer for `/v1/*`; required unless `AEROBIM_ALLOW_ANONYMOUS_DEV` |
| `AEROBIM_ALLOW_ANONYMOUS_DEV` | `false` | Opt-in anonymous API in development/test only (`from_env`) |
| `AEROBIM_CLASH_AFFECTS_PASS` | `false` | When `true`, hard clashes fail the report (`summary.passed`) |
| `AEROBIM_MAX_IFC_BYTES` | `268435456` | Max IFC size (256 MiB, aligned with bSI Validation Service) |
| `AEROBIM_CROSS_DOC_SEVERITY` | `warning` | Severity for cross-document contradictions: `error` (blocking), `warning`, `info` |
| `AEROBIM_DB_URL` | *(unset)* | Optional Postgres URL for report summary indexing |
| `AEROBIM_REPORT_TTL_DAYS` | *(unset)* | Optional TTL for persisted report payloads; unset means unlimited retention |
| `AEROBIM_S3_BUCKET` | *(unset)* | Optional S3/MinIO bucket for object storage |
| `AEROBIM_S3_ENDPOINT_URL` | *(unset)* | Optional MinIO/custom S3 endpoint |
| `AEROBIM_S3_REGION` | `us-east-1` | Signing region for S3-compatible storage |
| `AEROBIM_S3_ACCESS_KEY_ID` | *(unset)* | Optional access key for S3-compatible storage |
| `AEROBIM_S3_SECRET_ACCESS_KEY` | *(unset)* | Optional secret key for S3-compatible storage |
| `AEROBIM_S3_PREFIX` | `aerobim` | Prefix applied to object keys in S3-compatible storage |

## Project Structure

```text
aerobim/
├── backend/                 # Python FastAPI backend (see generated baseline below)
│   ├── src/aerobim/         # Source: core → domain → application → infrastructure → presentation
│   ├── tests/               # Backend test suite (see generated baseline below)
│   └── pyproject.toml
├── clients/revit-plugin/    # Thin authoring-side client boundary (planned)
├── docs/                    # Architecture reference, extraction dossier, backlog
├── frontend/                # Browser review shell with 3D viewer, 2D evidence overlay rails, and server-backed report filters
├── ops/                     # Standalone runbooks, env matrix, smoke path
├── samples/                 # IFC, IDS, drawing, spec fixtures
├── .github/workflows/       # CI pipeline (lint, typecheck, test, benchmark-smoke) + manual release-readiness gates
└── LICENSE                  # MIT
```

<!-- AEROBIM_RUNTIME_BASELINE:BEGIN -->
<!-- regenerated by: python -m aerobim.tools.export_runtime_baseline -->
Backend src ~16247 LOC; tests ~11434 LOC; 456+ test functions; extraction macro_f1=0.86 (fixture corpus; not product accuracy)
<!-- AEROBIM_RUNTIME_BASELINE:END -->

## Documentation

- [Claims lock](audit/reports/CLAIMS_LOCK_2026_07_17.md) — forbidden/allowed public wording (SSOT)
- [Critical blockers](audit/reports/CRITICAL_BLOCKERS.md) — checkpoint NO_GO register
- [Red Team delta (post-remediation)](audit/reports/RED_TEAM_DELTA_2026_07_17.md) — atomic re-verification after P0/evidence wave
- [Repository hygiene](docs/REPOSITORY-HYGIENE-2026.md) — what to commit vs gitignore vs CI artifacts
- [Reproducibility (FAIR/CODE)](docs/REPRODUCIBILITY-2026.md) — frozen tag, commands, evidence manifest
- [Pilot start package](docs/pilot-start-package-2026.md) — Moscow pilot kickoff (tag `pilot-2026-pre`, gates, week 1)
- [Documentation map](docs/README.md) — Tier 0 / pilot / archive router
- [Architecture Reference](docs/06-architecture-reference.md) — canonical layer map and invariants
- [Standards Roadmap 2026](docs/13-academic-execution-plan-2026.md) — openBIM iterations A–C
- [Archived docs](docs/archive/README.md) — MicroPhoenix extraction, rebaseline, April 2026 audits
- [Enterprise Storage](docs/14-enterprise-storage-foundation.md) — ObjectStore and Postgres index
- [Publication Evidence](docs/academic-publication-evidence-2026.md) — reproducibility commands
- [Local Quality Gate](docs/15-local-quality-gate.md) — CI-parity formatting/lint/type/test commands before push
- [Standalone Runbook](ops/standalone-runbook.md) — backend/frontend bootstrap and day-1 operations
- [Environment Matrix](ops/environment-matrix.md) — deployment variables and defaults
- [Smoke Path](ops/smoke-path.md) — local and Docker verification checklist, including the deterministic seeded runtime smoke path
- [Benchmark Packs](samples/benchmarks/README.md) — manifest-backed throughput rail for representative project-package fixtures

## Git commits

Use [scripts/git_commit.ps1](scripts/git_commit.ps1) or the VS Code task **AeroBIM: commit (single author)** so history stays single-author without `Co-authored-by` trailers. Enable the repo hook:

```bash
git config core.hooksPath .githooks
```

See [docs/contributor-git-2026.md](docs/contributor-git-2026.md).

**GitHub publication:** [docs/github-readiness-audit-2026-05-20.md](docs/github-readiness-audit-2026-05-20.md), [docs/PROJECT-AUDIT-2026-05-20.md](docs/PROJECT-AUDIT-2026-05-20.md). Suggested repo About — [.github/repository-metadata.md](.github/repository-metadata.md).

## Governance

- [Contributing](CONTRIBUTING.md)
- [Contributor Git policy](docs/contributor-git-2026.md)
- [Security Policy](SECURITY.md)
- [Citation Metadata](CITATION.cff)
- [Support](SUPPORT.md)
- [Maintainers](MAINTAINERS.md)
- [Release Policy](RELEASE_POLICY.md)

## Release Readiness

Use the manual GitHub Actions workflow `.github/workflows/release-readiness.yml` when preparing a release candidate.

It runs benchmark rails by default and can optionally run the full live review smoke harness with browser artifacts.
The live-smoke path now installs Playwright and Chromium inside the workflow job so browser capture is reproducible in CI.
Main CI benchmark-smoke runs now also emit a compact benchmark summary table in workflow output and artifacts.
When needed, `require_live_smoke_gate=true` enforces live-smoke execution as a mandatory policy gate for that release-readiness run.
CI benchmark-smoke now also runs advisory threshold evaluation from `samples/benchmarks/benchmark-thresholds.json` and publishes the threshold summary alongside benchmark artifacts.
Release-readiness benchmark rails now support `benchmark_threshold_mode` (`advisory` or `enforced`) plus explicit threshold profile path selection.

## Stack

- **Python 3.12+**, **FastAPI**, **Uvicorn**
- **IfcOpenShell** / **IfcTester** / **IfcClash** (buildingSMART toolchain)
- **web-ifc** + **Three.js** for browser-side IFC review
- **PyMuPDF** for deterministic PDF text; **RapidOCR** only when `.[raster]` is installed
- **Docling** (optional, document parsing)
- 5-layer Clean Architecture, constructor DI, Protocol ports

## License

[MIT](LICENSE)
