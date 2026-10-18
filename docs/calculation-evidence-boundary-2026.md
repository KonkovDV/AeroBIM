# Calculation evidence boundary (2026)

## Split (mandatory)

| Function | Status in AeroBIM |
|---|---|
| Provenance / source↔result consistency (сверка) | PARTIAL (OpenRebar digest / LOAD patterns / declared `.xlsx` & `.docx` tables via `calculation_table_compare.py` and `spreadsheet_load_evidence_adapter.py`) |
| Independent solver verification (корректность) | **NOT_IMPLEMENTED** |
| SAF/LIRA/SCAD/RFEM native ingest | missing / not claimed (`.lir`/`.spr` refused fail-closed) |
| Unit mismatch detection | required for any `MATCH` claim |

## Allowed outcomes for evidence verifier

`MATCH` (`MATCHED`) | `MISMATCH` | `SOURCE_MISSING` (`MISSING_CALC` / `MISSING_BIM`) | `SOURCE_UNVERIFIED` | `INCOMPLETE` | `NOT_VERIFIABLE` | `REVIEW_REQUIRED` | `NOT_IMPLEMENTED`

Never: «расчёт правильный».

## Observation

A declared-field comparison (`DeclaredCalcRow` → `FieldCompare`) is one row of a table. The observation unit that can be cited is the non-empty triple `element_id`, `section_id`, `parameter_id`.

`observation_status` is `COMPLETE` when both sides carry the same non-empty triple. It stays `NOT_VERIFIED` when either triple is blank, the triples differ, or the `field_id` is duplicated.

A blank coordinate, a missing side, a duplicate `field_id`, or two different triples leaves `observation_status = "NOT_VERIFIED"` (`TableCompareResult.observations_complete = False`).

`MATCH` means the printed numbers agree inside the decimal tolerance band: the absolute `Decimal` difference is at most `Decimal(str(epsilon))` (`within_epsilon`, dimensionless epsilon `0.001`), the same way as on the rest of the pack. `MATCH` does not say the calculation is correct, and it does not say the observation is complete.

## Port

`AnalysisModelIngestor` / SAF adapters — **not present** as product ports (P-007). Do not invent stubs that return green MATCH.

## Claims Lock

Forbidden: «проверка корректности расчётов», `calculation_correctness_verified`.
Allowed: calculation **сверка** with format caveats (Level B free-text numbers may not match).
