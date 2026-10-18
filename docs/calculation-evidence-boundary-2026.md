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

One compared row (`DeclaredCalcRow` → `FieldCompare`) can be cited only as the triple `element_id`, `section_id`, `parameter_id`.

`observation_status` is `COMPLETE` when both sides have that same non-empty triple. It stays `NOT_VERIFIED` when a coordinate is blank, a side is missing, the triples differ, or `field_id` is repeated. Then `TableCompareResult.observations_complete` is false.

`MATCH` is a separate question: the printed numbers agree when the absolute `Decimal` difference is at most `Decimal(str(epsilon))` (`within_epsilon`, dimensionless epsilon `0.001`). Agreement of the printed numbers is not a correct calculation, and it is not a complete observation.

## Port

`AnalysisModelIngestor` / SAF adapters — **not present** as product ports (P-007). Do not invent stubs that return green MATCH.

## Claims Lock

Forbidden: «проверка корректности расчётов», `calculation_correctness_verified`.
Allowed: calculation **сверка** with format caveats (Level B free-text numbers may not match).
