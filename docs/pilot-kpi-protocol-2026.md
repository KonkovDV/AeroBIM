---
title: "AeroBIM Pilot KPI Protocol 2026"
status: active
version: "1.0.0"
last_updated: "2026-05-20"
tags: [aerobim, pilot, kpi]
---

# Pilot KPI Protocol

Agree with the customer **before** pilot start. AeroBIM supplies artifacts; the customer supplies manual baseline times and TP/FP labels.

## KPI table

| KPI | Measurement | Target (hypothesis) | Owner |
|---|---|---|---|
| Time-to-first-contradiction | Timestamp delta: package ingest → first `CROSS_DOCUMENT` issue | Lower than manual baseline | AeroBIM logs + customer timesheet |
| Confirmed findings rate | TP / (TP + FP) from engineer BCF review | ≥ 60% on pilot scope | Customer engineer |
| Review hours saved | Hours manual review − hours AeroBIM-assisted review (same package) | ≥ 20% on narrow scope | Customer |
| Traceability | Share of issues with `source_id` or provenance + GUID or `problem_zone` | 100% deterministic path | AeroBIM export |

## Data collection

1. **Baseline week:** manual review of the same package (or closest available).
2. **Pilot week:** analyze → browser review → BCF export → engineer adjudication.
3. **KPI summary:** one-page memo with counts, not revenue claims.

## Deliverables

| Artifact | Format |
|---|---|
| Validation report | JSON + HTML + BCF |
| KPI summary | Markdown/PDF (1–2 pages) |
| Limitations memo | Link to [pilot-claim-boundary-2026.md](pilot-claim-boundary-2026.md) |

## Exclusions

- No revenue or production SLA claims from repo evidence alone
- No VLM-based metrics until extraction F1 gate is green in CI
