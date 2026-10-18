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

A declared-field comparison (`DeclaredCalcRow` → `FieldCompare`) is one row of a table. The observation unit that can be cited is the triple $u(r) = (\text{element\_id},\, \text{section\_id},\, \text{parameter\_id})$:

$$
\operatorname{observation}(r_{\text{calc}}, r_{\text{bim}}) = \begin{cases}
\text{COMPLETE}, & u(r_{\text{calc}}) = u(r_{\text{bim}}) \ne \varnothing, \\
\text{NOT\_VERIFIED}, & u(r_{\text{calc}}) = \varnothing \;\lor\; u(r_{\text{bim}}) = \varnothing \;\lor\; u(r_{\text{calc}}) \ne u(r_{\text{bim}}).
\end{cases}
$$

A blank coordinate, a missing side, a duplicate `field_id`, or two different triples leaves `observation_status = "NOT_VERIFIED"` (`TableCompareResult.observations_complete = False`).

`MATCH` means the printed numbers agree inside the decimal tolerance band $\lvert\delta(a, b)\rvert \le \operatorname{Decimal}(\operatorname{str}(\varepsilon))$ (`within_epsilon`, dimensionless $\varepsilon = 10^{-3}$), the same way as on the rest of the pack. `MATCH` does not say the calculation is correct, and it does not say the observation is complete.

## Port

`AnalysisModelIngestor` / SAF adapters — **not present** as product ports (P-007). Do not invent stubs that return green MATCH.

## Claims Lock

Forbidden: «проверка корректности расчётов», `calculation_correctness_verified`.
Allowed: calculation **сверка** with format caveats (Level B free-text numbers may not match).
