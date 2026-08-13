<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
# IFC-Bench v2 smoke (open_bench_only)

**Date:** 2026-08-04; re-run 2026-08-14 (countable subset **9/1026**, not 514)  
**claim_level:** `open_bench_only`  
**closes_rt001:** false  
**Artifact:** [`ifc-bench-v2-smoke-latest.json`](ifc-bench-v2-smoke-latest.json)

## Denominators (honest)

| Metric | Value |
|---|---|
| total_questions | 1026 |
| scored (deterministic countable probes with local IFC) | **9** |
| matched | 9 |
| mismatched | 0 |
| exact_match_rate_on_scored | **1.0** |
| skipped / unmapped NL | 1017 |

Do **not** report 100% on the full bench. Rate is over the mapped countable subset only (`9/1026`).

## Integrity

- Questions SHA-256 measured: `e47ccd097306f5bca49b9c8ac0b4cd72f296df9f7ff7a02625b3f06c1691da9b` (matches AeroBIM pin; HF card pin `8f08f5d0…` is stale).
- Local IFCs: duplex `arc`/`mep`, dental_clinic `arc`.

## Claims Lock

Not product accuracy. Never claim >90% from this smoke. Checkpoint remains **NO_GO**.
