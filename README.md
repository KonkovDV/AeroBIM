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
| Drawing annotation ↔ IFC cross-validation | ✅ |
| ISO 12006-3 tolerance algebra (ε-band) | ✅ |
| Narrative NLP → requirements (regex baseline) | ✅ |
| Clash detection (IfcClash) | ✅ |
| BCF 2.1 export | ✅ |
| HTML / JSON report export | ✅ |
| VLM drawing analysis (Qwen-VL / Florence-2) | 🔜 Planned |

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
pip install -e ".[dev]"

# Run tests
pytest tests -v

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
| `GET` | `/v1/reports` | List persisted reports |
| `GET` | `/v1/reports/{id}` | Get report by ID |
| `GET` | `/v1/reports/{id}/export/json` | Download JSON export |
| `GET` | `/v1/reports/{id}/export/html` | Download HTML export |
| `GET` | `/v1/reports/{id}/export/bcf` | Download BCF 2.1 ZIP |

## Architecture

Five-layer Clean Architecture with strict inward dependency direction:

```
core/          DI container, tokens, config (no project imports)
domain/        Immutable models, Protocol ports, logging contract
application/   Use case orchestration (requirement fusion, cross-doc detection)
infrastructure/ Adapters: IfcOpenShell, IfcTester, Docling, IfcClash, BCF, filesystem
presentation/  FastAPI HTTP API, correlation middleware
```

**9 domain ports** → **12 infrastructure adapters** → **14 DI tokens** — all wired in a single composition root (`bootstrap_container()`).

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

## Project Structure

```text
aerobim/
├── backend/                 # Python FastAPI backend (~1.9K LOC src, ~1.8K LOC tests)
│   ├── src/aerobim/         # Source: core → domain → application → infrastructure → presentation
│   ├── tests/               # 15 test modules (0.96:1 test/source LOC ratio)
│   └── pyproject.toml
├── clients/revit-plugin/    # Thin authoring-side client boundary (planned)
├── docs/                    # Architecture reference, extraction dossier, backlog
├── frontend/                # Browser review UI (planned)
├── ops/                     # Environment and runtime notes
├── samples/                 # IFC, IDS, drawing, spec fixtures
├── .github/workflows/       # CI pipeline (lint, typecheck, test)
└── LICENSE                  # MIT
```

## Documentation

- [Architecture Reference](docs/06-architecture-reference.md) — canonical layer map and invariants
- [MicroPhoenix Adoption Matrix](docs/08-microphoenix-adoption-matrix.md) — extraction decisions
- [Implementation Rails](docs/09-implementation-and-verification-rails.md) — delivery and verification
- [Academic Audit](docs/10-academic-audit-and-recommendations-ru.md) — L5 hyper-deep audit

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
- **Docling** (optional, document parsing)
- 5-layer Clean Architecture, constructor DI, Protocol ports

## License

[MIT](LICENSE)
