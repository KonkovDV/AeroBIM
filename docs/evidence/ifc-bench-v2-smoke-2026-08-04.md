<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
# IFC-Bench v2 smoke (open_bench_only)

**Date:** 2026-08-04; re-run 2026-08-16 (countable subset **27/1026**, not 514)  
**claim_level:** `open_bench_only`  
**closes_rt001:** false  
**Artifact:** [`ifc-bench-v2-smoke-latest.json`](ifc-bench-v2-smoke-latest.json)  
**output_sha256:** `6ca587ebe79e4d7d4cb76a5b42f9111991476568111262d5d1c06ffd059477e1`

## Denominators (honest)

| Metric | Value |
|---|---|
| total_questions | 1026 |
| scored (deterministic countable probes with local IFC) | **27** |
| matched | 27 |
| mismatched | 0 |
| exact_match_rate_on_scored | **1.0** |
| skipped / unmapped NL | 999 |
| skip_breakdown | gpl 189 / incomplete_info 110 / non_numeric_gt 66 / unmapped_nl 634 |
| first_number_on_unmapped | 634 — **not** a countable-probe backlog |
| eval-split among scored | **12** test / **15** train (published split 514/512) |

Do **not** report 100% on the full bench. Rate is over the mapped countable subset only (`27/1026`). Eval-split **514** is the published test partition, not a false-pass figure and not 12/514 product accuracy.

New verified probes this pass: `wbdg_office/arc` total railings (IfcRailing=10) and `digital_hub/heating` system count (IfcSystem=42). Schema-unsafe types (e.g. `IfcPump` on IFC2X3) are not mapped. GPLv3 projects are skipped, not errors.

## Integrity

- Questions SHA-256 measured: `e47ccd097306f5bca49b9c8ac0b4cd72f296df9f7ff7a02625b3f06c1691da9b` (matches AeroBIM pin; HF card pin `8f08f5d0…` is stale).
- Local IFCs present under `.local/ifc-bench-v2/projects` (duplex, dental_clinic, digital_hub, sixty5, wbdg_office, plus inventory-only west_riverside). GPLv3 project dirs were not downloaded.

## Claims Lock

Not product accuracy. Never claim >90% from this smoke. Checkpoint remains **NO_GO**.
