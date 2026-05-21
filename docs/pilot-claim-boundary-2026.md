---
title: "AeroBIM Pilot Claim Boundary 2026"
status: active
version: "1.0.0"
last_updated: "2026-05-21"
tags: [aerobim, pilot, claims, evidence]
---

# AeroBIM Pilot Claim Boundary

This document separates **verified repository evidence** from **roadmap intent** for pilot and accelerator communications.

**Stakeholder distribution:** share with [`pilot-start-package-2026.md`](pilot-start-package-2026.md) at pilot kickoff.

## Verified (may be claimed with evidence)

| Claim | Evidence source |
|---|---|
| Deterministic IFC + IDS + cross-document validation | `pytest` suite, benchmark packs |
| Multimodal project-package analysis | `POST /v1/analyze/project-package`, benchmark manifests |
| BCF 2.1 export (default) and BCF 3.0 opt-in | Export tests, `GET /v1/reports/{id}/export/bcf` |
| Browser review shell (3D + 2D evidence) | Frontend tests, `run_live_review_smoke` (overlay rectangle + preview asset) |
| OpenRebar provenance digest chain | Contract schema, digest endpoint, enforced mode |
| ISO 19650-lite context fields on reports | Optional request/report fields, HTML export section |
| Extraction quality metrics (RU fixtures) | `evaluate_extraction` tool, macro F1 ≥ 0.70 on ground truth, CI gate |
| Samolet-style priority profile (optional) | `AEROBIM_PRIORITY_PROFILE=samolet` boosts fire/cross-doc triage |
| Package SLA on pilot fixture pack | `measure_package_sla` — see `docs/evidence/samolet-sla-*.json` (fixture only) |

## Planned (do not claim as deployed)

| Item | Status |
|---|---|
| Optional raster vision drawing path | Planned behind `VisionDrawingAnalyzer` port |
| Stochastic text extraction training | Not in pilot sign-off path |
| Full OIDC multi-tenant auth | Post-pilot (static bearer sufficient for pilot VM) |
| arq/Redis async queue | Post-pilot (in-process jobs sufficient) |
| BCF API / OpenCDE integration | Post-pilot |
| Production rollout / confirmed revenue | Requires customer documents outside repo |

## Non-claims (explicit boundaries)

1. AeroBIM is **decision-support** for engineering QA, not a licensed-engineer replacement.
2. AeroBIM does **not** assert full regulatory code compliance across all document types.
3. AeroBIM does **not** claim to outperform Solibri globally — only a bounded open pilot path.
4. Stochastic (model-based) text extraction is **not** used for pilot sign-off; deterministic regex path meets F1 gates in CI.

## Reproducibility baseline

```bash
cd backend
python -m venv .venv-pilot
.venv-pilot\Scripts\activate   # Windows
pip install -e ".[dev,vision]"
python -m ruff format --check src tests
python -m ruff check src tests
python -m mypy src
pytest tests -q
python -m aerobim.tools.export_runtime_baseline
```

Use an **isolated** virtual environment under `AeroBIM/backend/.venv-pilot`, not the monorepo root `.venv`.

## Sync surfaces

Keep aligned with:

- [docs/startups/Novator/AEROBIM_APPLICATION_PACKET_2026.md](../docs/startups/Novator/AEROBIM_APPLICATION_PACKET_2026.md)
- [README.md](../README.md) Scientific Reporting Standard section
