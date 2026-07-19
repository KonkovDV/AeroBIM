---
title: "Citeable evidence (jury / FAIR)"
status: active
version: "2.1.0"
last_updated: "2026-07-19"
---

# Evidence fixtures

Only **citeable** snapshots for TechLab review and reproducibility. Phase-command dumps and operator scratch are local (`.local/`).

Red Team note (2026-07-19): fixture metrics ≠ product accuracy; SLA JSON is fixture-only; BCF structural T1 ≠ CDE import.

| File | Role |
|------|------|
| [`runtime-baseline-latest.json`](runtime-baseline-latest.json) | Runtime LOC / test baseline |
| [`samolet-sla-pilot-moscow-2026-05-21.json`](samolet-sla-pilot-moscow-2026-05-21.json) | Fixture SLA (not customer) |
| [`tz-matrix-status-latest.json`](tz-matrix-status-latest.json) | TZ matrix status |
| [`benchmark-report-2026-05-21.md`](benchmark-report-2026-05-21.md) | Academic benchmark snapshot |

Audit honesty gates: [`../../audit/evidence/`](../../audit/evidence/) · Claims Lock: [`../../audit/reports/CLAIMS_LOCK_2026_07_17.md`](../../audit/reports/CLAIMS_LOCK_2026_07_17.md) · see [`REPRODUCIBILITY-2026.md`](../REPRODUCIBILITY-2026.md).
