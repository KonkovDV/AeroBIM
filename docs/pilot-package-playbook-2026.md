---
title: "AeroBIM Pilot Package Playbook 2026"
status: active
version: "1.0.0"
last_updated: "2026-05-20"
tags: [aerobim, pilot, playbook, moscow]
---

# Pilot Package Playbook (Moscow v1)

## Scope

Single repeatable project package for developer / design-institute pilot:

- **Disciplines:** fire-safety + structure (narrow)
- **Manifest:** [samples/benchmarks/project-package-pilot-moscow-v1.json](../samples/benchmarks/project-package-pilot-moscow-v1.json)
- **Regulatory context:** RF BIM documentation pressure (PP RF №331) — pilot does **not** claim full code compliance

## Input bundle

| Artifact | Path | Role |
|---|---|---|
| IFC4 model | `samples/ifc/walls-multi-entity.ifc` | Model truth |
| IDS package | `samples/ids/wall-fire-rating.ids` | Delivery contract |
| Fire rules | `samples/requirements/techlab-fire-safety-rules.txt` | Structured requirements |
| Technical spec | `samples/specifications/techlab-tz.txt` | Narrative synthesis |
| Calculation | `samples/calculations/techlab-area-calc.txt` | Cross-doc checks |
| Drawing evidence | `samples/drawings/techlab-annotations.txt` | 2D annotations |

## ISO 19650-lite context (optional)

Set on analyze request:

| Field | Pilot example |
|---|---|
| `stage` | `S2` |
| `information_container_id` | `cde-pilot-moscow-001` |
| `revision` | `P-01` |
| `doc_status` | `Shared` |

Fields appear in JSON/HTML exports and the browser report header when present.

## Run locally

```bash
cd backend
python -m aerobim.tools.benchmark_project_package \
  --pack ../samples/benchmarks/project-package-pilot-moscow-v1.json \
  --iterations 1 \
  --warmup-iterations 0 \
  --storage-dir ./var/reports-pilot-moscow
```

Or via HTTP `POST /v1/analyze/project-package` with the same paths inside `AEROBIM_STORAGE_DIR`.

## Expected outcomes (fixture baseline)

- IDS and IFC property checks execute without error
- Cross-document findings may appear when narrative/calculation/drawing disagree with model
- Report exports: JSON, HTML (with ISO block when fields set), BCF 2.1

Exact issue counts are environment-sensitive; treat as **regression baseline**, not marketing guarantees.

## BCF roundtrip checklist

1. Export: `GET /v1/reports/{id}/export/bcf` (default 2.1)
2. Import into Revit / Navisworks / BIMcollab
3. Verify topics carry rule messages and IFC GUIDs where available
4. Engineer marks TP/FP per topic for KPI sheet

## OpenRebar (optional structural path)

If reinforcement report is in scope:

1. `python -m aerobim.tools.openrebar_provenance_digest <result.json>`
2. Pass `reinforcement_source_digest` + `reinforcement_provenance_mode=enforced` on analyze
3. See [docs/12-openrebar-provenance-decision-table.md](12-openrebar-provenance-decision-table.md)

## LOIN mapping (pilot dossier)

For each check family document in the pilot protocol:

| Check | Purpose | Milestone | Actor |
|---|---|---|---|
| Fire rating (IDS) | Delivery compliance | S2 design | BIM manager |
| Cross-doc contradiction | Early conflict detection | S2 review | Lead engineer |
| Drawing overlay | Spatial evidence | S2 review | Discipline reviewer |
