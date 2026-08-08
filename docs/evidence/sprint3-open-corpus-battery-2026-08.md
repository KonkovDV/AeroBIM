# Sprint 3 — open corpus battery

Generated: `2026-08-08T14:50:06.330380+00:00`

**claim_boundary:** Open sets lack expert TP/FP labels -> regression/timing only, NOT product accuracy. Never claim >90%.

## Summary

| Rail | Result |
|---|---|
| Fixture regression (n=7) | 7/7 (pass=True) |
| BSI TestCases (n=290) | raw 0.937931 adjusted 1.0 (pass=True) |
| IFC-Bench v1 smoke | scored=7 matched=7 |
| IFC-Bench v2 smoke | scored=7 matched=7 |

## IFC schema-suite (fixture)

| Schema | p50 ms | p95 ms | issues |
|---|---:|---:|---:|
| IFC2X3 | None | None | 6 |
| IFC4 | None | None | 4 |
| IFC4X3 | None | None | 4 |

## Reproduce

```bash
cd backend
python -m aerobim.tools.run_sprint3_open_corpus_battery
```
