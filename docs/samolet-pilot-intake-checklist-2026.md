---
title: "Samolet Pilot Intake Checklist 2026"
status: active
version: "1.1.0"
last_updated: "2026-07-10"
tags: [aerobim, samolet, pilot, intake]
---

# Samolet pilot intake (Week 1)

Owner: **joint** (Samolet + AeroBIM operator). Target score after completion: **8,5/10**.

**Full ask (practice-backed, July 2026):**  
RU handoff → [`partners/SAMOLET_WHAT_WE_NEED_2026_07-ru.md`](partners/SAMOLET_WHAT_WE_NEED_2026_07-ru.md)  
EN SSOT → [`partners/SAMOLET_WHAT_WE_NEED_2026_07.md`](partners/SAMOLET_WHAT_WE_NEED_2026_07.md)

## Documents

| # | Item | Owner | Done | Evidence |
|---|------|-------|------|----------|
| 1 | NDA signed | Legal | [ ] | internal memo |
| 2 | Agreed pilot **scope memo** (disciplines, stage, in/out, clash policy, remark locale) | Joint | [ ] | signed PDF |
| 3 | Copy [`project-package-samolet-pilot-v1.template.json`](../samples/benchmarks/project-package-samolet-pilot-v1.template.json) → local `project-package-samolet-pilot-v1.json` | AeroBIM | [ ] | gitignored manifest |
| 4 | IFC (+ schema) + TZ/EIR extract + calc + PD/RD PDF + 2D paths validated | Samolet | [ ] | ingest log |
| 5 | IDS 1.0 **or** property table (≥15–30 rules) for pilot disciplines | Samolet | [ ] | `.ids` / spreadsheet |
| 6 | Typical errors list (≥20 patterns with examples) | Samolet | [ ] | update `samolet-typical-errors-catalog.json` |
| 7 | Manual review baseline hours (same package) | Samolet | [ ] | [`pilot-weekly-log-2026.md`](pilot-weekly-log-2026.md) W1 |
| 8 | CDE tool name + BCF version + pilot project for import | Joint | [ ] | [`pilot-cde-handoff-2026.md`](pilot-cde-handoff-2026.md) |
| 9 | ≥2 TP/FP adjudicators named + process agreed | Joint | [ ] | [`pilot-kpi-protocol-2026.md`](pilot-kpi-protocol-2026.md) |
| 10 | TechLab pilot budget owner confirmed (2 000 000 ₽) | Samolet | [ ] | internal nomination |

## Commands (after manifest filled)

```powershell
cd AeroBIM\backend
$env:AEROBIM_PRIORITY_PROFILE = "samolet"
.\.venv-pilot\Scripts\python.exe -m aerobim.tools.map_typical_errors --output ..\docs\evidence\samolet-typical-errors-mapping.json
.\.venv-pilot\Scripts\python.exe -m aerobim.tools.measure_package_sla --pack <path-to-samolet-manifest> --max-minutes 30 --output ..\docs\evidence\internal\samolet-sla-customer.json
```

## Clash semantics (week 1 decision)

Record in case study: geometric clash (IfcClash) vs cross-document — see [`samolet-techlab-alignment-2026.md`](samolet-techlab-alignment-2026.md) and scope memo § clash policy (`AEROBIM_CLASH_AFFECTS_PASS`).

## Non-goals to confirm in scope memo

- Full SP/GOST automation  
- CV-as-sign-off on arbitrary scans  
- Autonomous engineer replacement  
- Published >90% accuracy before adjudication corpus

## Drawing AI posture (retained local SSOT)

July 2026: [../evidence/DRAWING_AI_WORLD_PRACTICE_2026_07.md](../evidence/DRAWING_AI_WORLD_PRACTICE_2026_07.md).
