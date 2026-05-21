---
title: "Pilot Execution Runbook 2026"
status: active
version: "1.0.0"
last_updated: "2026-05-20"
tags: [aerobim, pilot, operations]
---

# Pilot Execution Runbook (8–12 weeks)

Operational rhythm for the Moscow pilot. KPI definitions: [`pilot-kpi-protocol-2026.md`](pilot-kpi-protocol-2026.md).

**Kickoff package:** [`pilot-start-package-2026.md`](pilot-start-package-2026.md) (stakeholders + week 1 checklist).

## Before week 1

1. Complete gates 1–5 in [`pilot-pre-pilot-gates-2026.md`](pilot-pre-pilot-gates-2026.md).
2. Create frozen tag per [`pilot-frozen-tag-protocol-2026.md`](pilot-frozen-tag-protocol-2026.md).
3. Agree BCF tool + version (2.1 or 3.0) with customer — record in [`pilot-case-study-report-2026.md`](pilot-case-study-report-2026.md).

## Weekly loop

| Day | Activity | Owner |
|---|---|---|
| Mon | Ingest package, run analysis, export BCF | AeroBIM operator |
| Tue–Thu | Engineer review in CDE, label TP/FP | Customer |
| Fri | Fill [`pilot-weekly-log-2026.md`](pilot-weekly-log-2026.md) | Joint |

## Per-run checklist

```bash
cd backend
python -m pytest tests -q
python -m aerobim.tools.evaluate_extraction --min-macro-f1 0.70
# analyze pilot package (API or benchmark manifest)
python -m aerobim.tools.summarize_conflict_breakdown --pack samples/benchmarks/project-package-pilot-moscow-v1.json
export AEROBIM_PRIORITY_PROFILE=samolet   # Windows: $env:AEROBIM_PRIORITY_PROFILE='samolet'
python -m aerobim.tools.measure_package_sla --pack ../samples/benchmarks/project-package-pilot-moscow-v1.json --max-minutes 30
python -m aerobim.tools.map_typical_errors --output ../docs/evidence/samolet-typical-errors-mapping.json
```

Samolet intake: [`samolet-pilot-intake-checklist-2026.md`](samolet-pilot-intake-checklist-2026.md). Closure: [`samolet-compliance-scorecard-2026.md`](samolet-compliance-scorecard-2026.md).

Browser review: [`ops/smoke-path.md`](../ops/smoke-path.md) steps 8–10 (2D overlay + exports).

## Scope control

- Disciplines: fire + structure only (Gate 4).
- Severity: `AEROBIM_CROSS_DOC_SEVERITY` documented in deployment guide.
- No learned-model drawing sign-off path during pilot.

## End of pilot

1. Complete KPI table in case study report.
2. Run post-pilot decision memo: [`post-pilot-go-no-go-memo-2026.md`](post-pilot-go-no-go-memo-2026.md).
3. Choose branch A/B/C in [`post-pilot-fork-2026.md`](post-pilot-fork-2026.md).
