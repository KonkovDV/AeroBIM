---
title: "Samolet Pilot Intake Checklist 2026"
status: active
version: "1.0.0"
last_updated: "2026-05-21"
tags: [aerobim, samolet, pilot, intake]
---

# Samolet pilot intake (Week 1)

Owner: **joint** (Samolet + AeroBIM operator). Target score after completion: **8,5/10**.

## Documents

| # | Item | Owner | Done | Evidence |
|---|------|-------|------|----------|
| 1 | NDA signed | Legal | [ ] | internal memo |
| 2 | Agreed pilot scope memo (disciplines, gates) | Joint | [ ] | email / PDF |
| 3 | Copy [`project-package-samolet-pilot-v1.template.json`](../samples/benchmarks/project-package-samolet-pilot-v1.template.json) → local `project-package-samolet-pilot-v1.json` | AeroBIM | [ ] | gitignored manifest |
| 4 | IFC + IDS + TZ + calc + 2D paths validated | Samolet | [ ] | ingest log |
| 5 | Typical errors list (≥20 patterns) | Samolet | [ ] | update `samolet-typical-errors-catalog.json` |
| 6 | Manual review baseline hours (same package) | Samolet | [ ] | [`pilot-weekly-log-2026.md`](pilot-weekly-log-2026.md) W1 |
| 7 | CDE tool name + BCF version | Joint | [ ] | [`pilot-cde-handoff-2026.md`](pilot-cde-handoff-2026.md) |
| 8 | TP/FP adjudication process agreed | Joint | [ ] | [`pilot-kpi-protocol-2026.md`](pilot-kpi-protocol-2026.md) |

## Commands (after manifest filled)

```powershell
cd AeroBIM\backend
$env:AEROBIM_PRIORITY_PROFILE = "samolet"
.\.venv-pilot\Scripts\python.exe -m aerobim.tools.map_typical_errors --output ..\docs\evidence\samolet-typical-errors-mapping.json
.\.venv-pilot\Scripts\python.exe -m aerobim.tools.measure_package_sla --pack <path-to-samolet-manifest> --max-minutes 30 --output ..\docs\evidence\internal\samolet-sla-customer.json
```

## Clash semantics (week 1 decision)

Record in case study: geometric clash (IfcClash) vs cross-document — see [`samolet-techlab-alignment-2026.md`](samolet-techlab-alignment-2026.md) § Clash policy.
