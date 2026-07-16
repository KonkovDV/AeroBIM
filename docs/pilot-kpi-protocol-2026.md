---
title: "AeroBIM Pilot KPI Protocol 2026"
status: active
version: "1.2.0"
last_updated: "2026-07-10"
tags: [aerobim, pilot, kpi, samolet, techlab, tz]
---

# Pilot KPI Protocol

Agree with the customer **before** pilot start. AeroBIM supplies artifacts; the customer supplies manual baseline times and TP/FP labels.

TZ mapping: [`tz/TZ_COMPLIANCE_MATRIX_2026.md`](tz/TZ_COMPLIANCE_MATRIX_2026.md).
Samolet alignment SSOT: [`samolet-techlab-alignment-2026.md`](samolet-techlab-alignment-2026.md).

## TZ KPI vs Pilot KPI

| TZ criterion | Pilot / repo operational target | How measured | When claimable |
|---|---|---|---|
| Clash accuracy >90% | Interim: confirmed findings (TP rate) ≥ **60%** on pilot scope | Engineer adjudication of clash/`SPATIAL-*` issues | >90% only after labeled corpus + published precision/recall |
| Inconsistency accuracy >90% | Same interim ≥60% TP on cross-doc / missing-element issues | Adjudication log | Same as above |
| Calc error detection | Cross-doc + OpenRebar findings on agreed pack | Issue counts + TP/FP | Qualitative until labeled set |
| Remark quality RU/EN | RU templates; EN templates (P0); HITL edit acceptance rate | `review-kpi` + spot review | Never “auto-perfect” without HITL |
| Package ≤30 min | Wall-clock analyze on **agreed** corpus ≤ 30 min | `measure_package_sla` | Fixture ≠ customer until re-run |
| UI / cognitive load | Priority profile + filterable remarks (P0) | Pilot survey / time-to-triage | Qualitative |

**Honesty rule:** do not put «>90%» in README, pitch, or claim boundary **Verified** until evidence exists under `docs/evidence/` with pack hash + commit SHA.

## Pilot KPI table

| KPI | Measurement | Target (hypothesis) | Owner |
|---|---|---|---|
| Time-to-first-contradiction | Timestamp delta: package ingest → first `CROSS_DOCUMENT` issue | Lower than manual baseline | AeroBIM logs + customer timesheet |
| Confirmed findings rate | TP / (TP + FP) from engineer BCF review | ≥ 60% on pilot scope | Customer engineer |
| Review hours saved | Hours manual review − hours AeroBIM-assisted review (same package) | ≥ 20% on narrow scope | Customer |
| Traceability | Share of issues with `source_id` or provenance + GUID or `problem_zone` | 100% deterministic path | AeroBIM export |
| Package SLA (Samolet / TZ) | Wall-clock `analyze/project-package` on **agreed** corpus | ≤ **30 min** | [`measure_package_sla`](../backend/src/aerobim/tools/measure_package_sla.py) |
| Remark edit HITL | `edited_remark` / `accepted` events via review-kpi | Tracked (no hard gate in MVP) | AeroBIM + reviewer |

### SLA measurement (fixture rail)

```powershell
cd AeroBIM\backend
$env:AEROBIM_PRIORITY_PROFILE = "samolet"
.\.venv-pilot\Scripts\python.exe -m aerobim.tools.measure_package_sla `
  --pack ..\samples\benchmarks\project-package-pilot-moscow-v1.json `
  --max-minutes 30 `
  --output ..\docs\evidence\samolet-sla-pilot-moscow-2026-05-21.json
```

Fixture pass does **not** prove SLA on customer production packages — only on the agreed pilot corpus after intake.

### Path to TZ >90%

1. Freeze agreed package + typical-error catalog labels (`expected_rule_id`, modality).
2. Run analyze; export issues.
3. Fill [`samolet-kpi-adjudication-template-2026.md`](samolet-kpi-adjudication-template-2026.md).
4. Compute precision/recall per class (clash, cross-doc, missing).
5. Publish `docs/evidence/tz-kpi-*.json` — only then update claim boundary.

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
- No non-deterministic drawing metrics until extraction F1 gate is green in CI
- No public >90% accuracy claims without labeled adjudication evidence
