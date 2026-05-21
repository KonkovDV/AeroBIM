---
title: "Pilot Start Package 2026"
status: active
version: "1.0.0"
last_updated: "2026-05-21"
tags: [aerobim, pilot, moscow, stakeholder]
---

# Pilot Start Package (Moscow 2026)

Single entry point for customer-facing pilot kickoff. Distribute with [`pilot-claim-boundary-2026.md`](pilot-claim-boundary-2026.md) and [`samolet-techlab-alignment-2026.md`](samolet-techlab-alignment-2026.md) when the customer is Samolet / TechLab.

## Frozen baseline

| Item | Value |
|---|---|
| Git tag (frozen metrics) | `pilot-2026-pre` → commit `1a5c03e` |
| Rolling `main` | May include newer docs after `1a5c03e`; cite tag for frozen numbers |
| Evidence | [`evidence/pre-pilot-gates-evidence-2026-05-21.md`](evidence/pre-pilot-gates-evidence-2026-05-21.md) |
| Reproducibility SSOT | [`REPRODUCIBILITY-2026.md`](REPRODUCIBILITY-2026.md) |
| Extraction macro F1 | **0.86** (gate ≥ 0.70, frozen line) |
| Tests | 292 passed (pre-pilot run) |

## Pre-pilot gates (complete)

| Gate | Status |
|---|---|
| 1 Deterministic replay | pass |
| 2 Evidence rail | pass |
| 3 BCF (repository) | pass; **CDE import = week 1 action** |
| 4 FP policy | `AEROBIM_CROSS_DOC_SEVERITY=warning`, fire+structure scope |

Details: [`pilot-pre-pilot-gates-2026.md`](pilot-pre-pilot-gates-2026.md).

## Week 1 actions (joint)

1. Agree coordination tool + BCF version (2.1 default) — record in [`pilot-case-study-report-2026.md`](pilot-case-study-report-2026.md).
2. Deploy per [`pilot-deployment-2026.md`](pilot-deployment-2026.md) and [`ops/standalone-runbook.md`](../ops/standalone-runbook.md).
3. First package ingest; export BCF; begin TP/FP labels in [`pilot-weekly-log-2026.md`](pilot-weekly-log-2026.md) **Week 1** section.
4. Run weekly checklist from [`pilot-execution-runbook-2026.md`](pilot-execution-runbook-2026.md).

## Operator commands (every ingest)

```powershell
cd AeroBIM\backend
.\.venv-pilot\Scripts\python.exe -m pytest tests -q
.\.venv-pilot\Scripts\python.exe -m aerobim.tools.evaluate_extraction --min-macro-f1 0.70
.\.venv-pilot\Scripts\python.exe -m aerobim.tools.summarize_conflict_breakdown --pack samples/benchmarks/project-package-pilot-moscow-v1.json
```

## What we do not claim during pilot

See [`pilot-claim-boundary-2026.md`](pilot-claim-boundary-2026.md): no stochastic vision sign-off, no full regulatory automation, no extrapolation from fixture-only cross-doc counts.

## Support

- KPI definitions: [`pilot-kpi-protocol-2026.md`](pilot-kpi-protocol-2026.md)
- Optional extras: [`optional-adapters-smoke-2026.md`](optional-adapters-smoke-2026.md)
- Post-pilot decision (November): [`post-pilot-go-no-go-memo-2026.md`](post-pilot-go-no-go-memo-2026.md)
