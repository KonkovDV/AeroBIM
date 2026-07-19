---
title: "AeroBIM TZ Build and Quality Requirements 2026"
status: active
version: "1.0.0"
last_updated: "2026-07-10"
tags: [aerobim, tz, build, quality]
---

# TZ Build and Quality Requirements

Fills **«Требования к коду и сборке = TBD»**.
Local quality gate: `ruff` + `mypy` + `pytest` in `backend/` (see root README «Checks before push»).

## 1. Runtime matrix

| Component | Requirement |
|-----------|-------------|
| Backend | Python **3.12+** |
| Frontend | Node **20+**, Vite |
| OS | Windows / Linux (cross-platform; no Domain `process.platform` branching) |
| Package manager | `pip` editable install; frontend `npm` |

## 2. Install profiles

| Profile | Command | Use |
|---------|---------|-----|
| Dev | `pip install -e ".[dev,raster]"` | Default contributor |
| Clash | `pip install -e ".[clash]"` | IfcClash geometry |
| Docling | `pip install -e ".[docling]"` | Office → markdown extract |
| Enterprise | `pip install -e ".[enterprise]"` | S3, Postgres, Redis, PyJWT |
| Frontend | `cd frontend && npm ci` | Review shell |

Isolated venv: `AeroBIM/backend/.venv-pilot` (not monorepo root `.venv`).

## 3. Quality gates (Definition of Done)

Every PR that touches live `src` / `tests` / metric docs:

```text
ruff format --check src tests
ruff check src tests
mypy src
pytest tests -q
```

Additional rails when relevant:

| Gate | Command / artifact |
|------|-------------------|
| Extraction F1 | `python -m aerobim.tools.evaluate_extraction --min-macro-f1 0.70` |
| Package SLA | `python -m aerobim.tools.measure_package_sla --max-minutes 30` |
| Live review smoke | `run_live_review_smoke` |
| Ablation | `python -m aerobim.tools.run_ablation_study` |
| Claim boundary | Update if README/docs claims change |

## 4. Frontend CI honesty

Frontend unit/smoke tests exist under `frontend/` but are **release-readiness / local** unless explicitly added to main CI. Do not claim “frontend always green in CI” without wiring.

## 5. Code standards

- TypeScript only in `frontend/src`; Python typed in `backend/src`.
- No fake adapter I/O without `/** @sota-stub */` + `KNOWN_BUGS` / claim-boundary tracking.
- Zod/Pydantic at API edges; domain models immutable dataclasses.
- Logging via structured logger; propagate `correlationId` on HTTP.
- Metrics only through agreed monitoring surfaces (no ad-hoc prom-client in Domain).

## 6. Atomic Delivery checklist (new capability)

1. Domain port (Protocol)
2. Infrastructure adapter
3. DI token + `bootstrap_container` wiring
4. Focused unit/integration test
5. Claim-boundary / TZ matrix row update if user-visible

## 7. Environment contract

SSOT: root README «Configuration» table + `.env.example`.
Minimum for secured demo: `AEROBIM_ENV`, `AEROBIM_API_BEARER_TOKEN`, `AEROBIM_STORAGE_DIR` (non-dev defaults to production sign-off profile).

## 8. Reproducibility

Frozen tags and evidence: [`../REPRODUCIBILITY-2026.md`](../REPRODUCIBILITY-2026.md).
Any TZ KPI number must cite pack path, commit SHA, and command output artifact under `docs/evidence/`.
