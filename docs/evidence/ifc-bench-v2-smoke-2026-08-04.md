<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
# IFC-Bench v2 smoke (open_bench_only)

**Date:** 2026-08-04; re-run 2026-08-14 (countable subset **17/1026**, not 514)  
**claim_level:** `open_bench_only`  
**closes_rt001:** false  
**Artifact:** [`ifc-bench-v2-smoke-latest.json`](ifc-bench-v2-smoke-latest.json)  
**output_sha256:** `17378fe4e57021fad25c036862ce35199aadabc27c75524d753daf4bcbe84721`

## Denominators (honest)

| Metric | Value |
|---|---|
| total_questions | 1026 |
| scored (deterministic countable probes with local IFC) | **17** |
| matched | 17 |
| mismatched | 0 |
| exact_match_rate_on_scored | **1.0** |
| skipped / unmapped NL | 1009 |

Do **not** report 100% on the full bench. Rate is over the mapped countable subset only (`17/1026`). Eval-split 514 remains unmapped NL — not a 514 false-pass figure.

Local IFC now includes dental `mep`/`str` on disk; those files feed inventory, not extra scored QA unless a countable probe maps.

## Integrity

- Questions SHA-256 measured: `e47ccd097306f5bca49b9c8ac0b4cd72f296df9f7ff7a02625b3f06c1691da9b` (matches AeroBIM pin; HF card pin `8f08f5d0…` is stale).
- Local IFCs: duplex `arc`/`mep`, dental_clinic `arc`/`mep`/`str` (5 files).

## Claims Lock

Not product accuracy. Never claim >90% from this smoke. Checkpoint remains **NO_GO**.
