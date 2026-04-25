# AeroBIM

[![CI](https://github.com/KonkovDV/AeroBIM/actions/workflows/ci.yml/badge.svg)](https://github.com/KonkovDV/AeroBIM/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Open-source **cross-modal semantic BIM validation** platform.

AeroBIM validates building information models (IFC) against technical specifications, 2D drawings, calculation documents, and IDS packages in a single deterministic pipeline — with full provenance tracing and BCF interoperability.

## Key Capabilities

| Capability | Status |
|---|---|
| IFC property/quantity validation (IfcOpenShell) | ✅ |
| IDS 1.0 spec validation (IfcTester) | ✅ |
| Cross-document contradiction detection | ✅ |
| Conflict taxonomy (`ConflictKind`: hard / unit-mismatch / ambiguous) | ✅ |
| Configurable contradiction severity policy | ✅ |
| Drawing annotation ↔ IFC cross-validation | ✅ |
| ISO 12006-3 tolerance algebra (ε-band) | ✅ |
| Narrative NLP → requirements (regex baseline) | ✅ |
| Clash detection (IfcClash, optional `.[clash]` extra) | ✅ |
| BCF 2.1 export | ✅ |
| BCF 3.0 export | 🔜 Planned (Iteration A.5) |
| HTML / JSON report export | ✅ |
| Browser IFC viewer (`web-ifc + Three.js`) | ✅ Initial tranche + clash-pair review |
| 2D problem-zone overlay on persisted drawing evidence | ✅ Initial tranche + asset switching |
| Deterministic PDF / OCR drawing analysis baseline | ✅ |
| Heavier VLM path (Qwen-VL / Florence-2) | 🔜 Planned |

## IFC Release Compatibility

| IFC Release | Schema | Validation Support | Notes |
|---|---|---|---|
| IFC2x3 | ISO 16739:2005 | ✅ Core | Most widely deployed; full property/quantity validation |
| IFC4 (IFC4 ADD2) | ISO 16739-1:2018 | ✅ Core | Pset naming normalised; unit assignment via `IfcUnitAssignment` |
| IFC4x3 | ISO 16739-1:2024 | ✅ Core | Alignment and infrastructure extensions; same validation kernel |

All three releases pass through the same `IfcOpenShellValidator` and `IfcTesterIdsValidator` adapters.
Pset/property name divergence between releases is surfaced as a `ValidationIssue` rather than a silent skip.
Formal parametric fixture coverage for IFC2x3 vs IFC4x3 is planned in Iteration A.4.

## BCF Roadmap

| Version | Status | Notes |
|---|---|---|
| BCF 2.1 | ✅ Stable | All export paths (`/export/bcf`); `markup.bcfzip` + viewpoint |
| BCF 3.0 | 🔜 Planned (A.5) | Experimental export alongside 2.1; version selector via query param |
| BCF API | 🔜 Roadmap | REST adapter for CDE / issue-tracker integration |

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
pip install -e ".[dev,vision]"

# Optional extras
# pip install -e ".[clash]"    # enable geometry clash detection
# pip install -e ".[docling]"  # enable non-text document extraction

# Run tests
pytest tests -v

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

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Readiness probe |
| `POST` | `/v1/validate/ifc` | Validate IFC against requirements + IDS |
| `POST` | `/v1/analyze/project-package` | Multimodal validation (spec + calc + drawing + IDS + IFC) |
| `POST` | `/v1/analyze/project-package/reinforcement-digest` | Build OpenRebar provenance digest from canonical report |
| `POST` | `/v1/analyze/project-package/submit` | Accept a same-process background analysis job for larger packages |
| `GET` | `/v1/analyze/project-package/jobs/{job_id}` | Poll async project-package job status |
| `GET` | `/v1/reports` | List persisted reports with optional `project`, `discipline`, and `passed` filters |
| `GET` | `/v1/reports/{id}` | Get report by ID |
| `GET` | `/v1/reports/{id}/source/ifc` | Download the report-scoped IFC source for browser viewing |
| `GET` | `/v1/reports/{id}/drawing-assets/{asset_id}/preview` | Download a report-scoped drawing preview for 2D evidence overlays |
| `GET` | `/v1/reports/{id}/export/json` | Download JSON export |
| `GET` | `/v1/reports/{id}/export/html` | Download HTML export |
| `GET` | `/v1/reports/{id}/export/bcf` | Download BCF 2.1 ZIP |

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

**9 domain ports** → **12 infrastructure adapters** → **13 DI tokens** — all wired in a single composition root (`bootstrap_container()`).

## Configuration

All settings are read from environment variables (see [`backend/.env.example`](backend/.env.example)):

| Variable | Default | Description |
|---|---|---|
| `AEROBIM_HOST` | `127.0.0.1` | Bind address |
| `AEROBIM_PORT` | `8080` | Bind port |
| `AEROBIM_DEBUG` | `true` | Debug mode |
| `AEROBIM_STORAGE_DIR` | `var/reports` | Report persistence directory |
| `AEROBIM_CORS_ORIGINS` | *(auto)* | Comma-separated CORS origins |
| `AEROBIM_ENV` | `development` | Environment name |
| `AEROBIM_API_BEARER_TOKEN` | *(unset)* | Optional Bearer token required for all `/v1/*` endpoints |
| `AEROBIM_CROSS_DOC_SEVERITY` | `warning` | Severity for cross-document contradictions: `error` (blocking), `warning`, `info` |

## Project Structure

```text
aerobim/
├── backend/                 # Python FastAPI backend (~1.9K LOC src, ~1.8K LOC tests)
│   ├── src/aerobim/         # Source: core → domain → application → infrastructure → presentation
│   ├── tests/               # 23 test modules (backend suite currently 171 tests + optional skips)
│   └── pyproject.toml
├── clients/revit-plugin/    # Thin authoring-side client boundary (planned)
├── docs/                    # Architecture reference, extraction dossier, backlog
├── frontend/                # Browser review shell with 3D viewer, 2D evidence overlay rails, and server-backed report filters
├── ops/                     # Standalone runbooks, env matrix, smoke path
├── samples/                 # IFC, IDS, drawing, spec fixtures
├── .github/workflows/       # CI pipeline (lint, typecheck, test, benchmark-smoke) + manual release-readiness gates
└── LICENSE                  # MIT
```

## Documentation

- [Architecture Reference](docs/06-architecture-reference.md) — canonical layer map and invariants
- [MicroPhoenix Adoption Matrix](docs/08-microphoenix-adoption-matrix.md) — extraction decisions
- [Implementation Rails](docs/09-implementation-and-verification-rails.md) — delivery and verification
- [Academic Audit](docs/10-academic-audit-and-recommendations-ru.md) — L5 hyper-deep audit
- [Execution Plan](docs/11-rebaseline-execution-plan.md) — phased next-step plan and tranche status
- [Academic Execution Plan 2026](docs/13-academic-execution-plan-2026.md) — openBIM standards roadmap (Iterations A–C)
- [Standalone Runbook](ops/standalone-runbook.md) — backend/frontend bootstrap and day-1 operations
- [Environment Matrix](ops/environment-matrix.md) — deployment variables and defaults
- [Smoke Path](ops/smoke-path.md) — local and Docker verification checklist, including the deterministic seeded runtime smoke path
- [Benchmark Packs](samples/benchmarks/README.md) — manifest-backed throughput rail for representative project-package fixtures

## Release Readiness

Use the manual GitHub Actions workflow `.github/workflows/release-readiness.yml` when preparing a release candidate.

It runs benchmark rails by default and can optionally run the full live review smoke harness with browser artifacts.
The live-smoke path now installs Playwright and Chromium inside the workflow job so browser capture is reproducible in CI.
Main CI benchmark-smoke runs now also emit a compact benchmark summary table in workflow output and artifacts.
When needed, `require_live_smoke_gate=true` enforces live-smoke execution as a mandatory policy gate for that release-readiness run.
CI benchmark-smoke now also runs advisory threshold evaluation from `samples/benchmarks/benchmark-thresholds.json` and publishes the threshold summary alongside benchmark artifacts.
Release-readiness benchmark rails now support `benchmark_threshold_mode` (`advisory` or `enforced`) plus explicit threshold profile path selection.

## Extraction From MicroPhoenix

### Kept

- `core → domain → application → infrastructure → presentation` layer discipline
- Token-based DI without magic reflection
- Explicit bootstrap composition root
- Use-case orchestration over controller-heavy logic
- Port/adapter seams for external libraries

### Deferred

- Multi-agent orchestration, event sourcing, MCP servers, vector-memory, knowledge-graph

## Stack

- **Python 3.12+**, **FastAPI**, **Uvicorn**
- **IfcOpenShell** / **IfcTester** / **IfcClash** (buildingSMART toolchain)
- **web-ifc** + **Three.js** for browser-side IFC review
- **PyMuPDF** + **RapidOCR** for deterministic PDF/OCR drawing extraction
- **Docling** (optional, document parsing)
- 5-layer Clean Architecture, constructor DI, Protocol ports

## License

[MIT](LICENSE)
