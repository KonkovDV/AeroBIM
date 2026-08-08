<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
# Sprint 2 — Samolet TZ Baseline Matrix

**Date:** 2026-08-06  
**Checkpoint:** **NO_GO**  
**claim_level:** `synthetic_only` / `fixture_only`  
**Rule:** Never upgrade to plain `VERIFIED` without customer evidence.

Allowed statuses only:

`VERIFIED_FIXTURE_ONLY` | `SYNTHETIC_ONLY` | `PARTIAL` | `NOT_VERIFIED` | `BLOCKED_BY_CUSTOMER_DATA` | `MISSING`

| Area | Status | Evidence / note |
|---|---|---|
| IFC / IDS / property checks | `VERIFIED_FIXTURE_ONLY` | Sprint 2 planted IFC mutations + IDS wall-fire fixtures; `run_sprint2_synthetic_baseline` |
| Cross-document load/calc mismatch | `SYNTHETIC_ONLY` | Level-B calculation_text defects in GT; not customer calcs |
| Drawing / PDF / OCR / degraded | `SYNTHETIC_ONLY` | drawing-advisory synthetic cases + `generate_degraded_scans` protocol reference |
| Geometric clashes | `NOT_VERIFIED` | `geometric_clash_between_systems` = not_planted_runnable; clashes_count=0 honesty |
| MEP system-aware clash | `NOT_VERIFIED` | Unconfigured / scaffold DI ≠ delivered MEP clash |
| Severity mapping | `PARTIAL` | Engine severities on fixtures; customer Critical/Major/Minor/Info mapping **proposed**, not approved |
| Provenance / reproducibility hash | `VERIFIED_FIXTURE_ONLY` | Dataset + baseline `reproducibility_hash` on synthetic cases |
| HITL review events | `VERIFIED_FIXTURE_ONLY` | API/UI fixture path; not customer workflow sign-off |
| BCF export | `PARTIAL` | Structural export tests; **not** CDE-ready BCF claim |
| SLA ≤30 min | `BLOCKED_BY_CUSTOMER_DATA` | Fixture p95 ≠ customer SLA |
| P / R / F1 (detection) | `SYNTHETIC_ONLY` | Measured on planted set only; `customer_precision_claim_publishable=false` |
| Customer validation / dual adjudication | `BLOCKED_BY_CUSTOMER_DATA` | RT-001 open; intake gate false |
| Native DWG product claim | `MISSING` | Forbidden claim |
| Calc independence (engineered recalculation) | `NOT_VERIFIED` | Cross-doc number check ≠ independent calc |
| Agreement κ/α / nDCG | `BLOCKED_BY_CUSTOMER_DATA` | Labels absent → N/A in baseline report |

## Explicit forbidden upgrades

- Do **not** mark product accuracy, >90%, production-ready, native DWG, delivered MEP clash, calc independence, CDE-ready BCF, or customer SLA as verified from fixtures.
- Cross-check: [`audit/reports/TZ_RUNTIME_MATRIX.md`](../../audit/reports/TZ_RUNTIME_MATRIX.md), Claims Lock, `docs/evidence/sprint2-baseline-report.json`.
