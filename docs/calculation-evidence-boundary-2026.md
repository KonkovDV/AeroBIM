# Calculation evidence boundary (2026)

## Split (mandatory)

| Function | Status in AeroBIM |
|---|---|
| Provenance / source↔result consistency (сверка) | PARTIAL (OpenRebar digest / LOAD patterns) |
| Independent solver verification (корректность) | **NOT_IMPLEMENTED** |
| SAF/LIRA/SCAD/RFEM native ingest | missing / not claimed |
| Unit mismatch detection | required for any MATCH claim |

## Allowed outcomes for evidence verifier

`MATCHED` | `MISMATCH` | `INCOMPLETE` | `NOT_VERIFIABLE` | `REVIEW_REQUIRED`

Never: «расчёт правильный».

## Port

`AnalysisModelIngestor` / SAF adapters — **not present** as product ports (P-007). Do not invent stubs that return green MATCH.

## Claims Lock

Forbidden: «проверка корректности расчётов», `calculation_correctness_verified`.
Allowed: calculation **сверка** with format caveats (Level B free-text numbers may not match).
