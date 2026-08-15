<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
# IFC-Bench v2 smoke (open_bench_only)

**Date:** 2026-08-04; re-run 2026-08-15 (countable subset **25/1026**, not 514)  
**claim_level:** `open_bench_only`  
**closes_rt001:** false  
**Artifact:** [`ifc-bench-v2-smoke-latest.json`](ifc-bench-v2-smoke-latest.json)  
**output_sha256:** `64cd4cff0867190a77762248b223bb5900f05cc10770c9cc61916c882bb74ea6`

## Denominators (honest)

| Metric | Value |
|---|---|
| total_questions | 1026 |
| scored (deterministic countable probes with local IFC) | **25** |
| matched | 25 |
| mismatched | 0 |
| exact_match_rate_on_scored | **1.0** |
| skipped / unmapped NL | 1001 |
| eval-split among scored | **12** test / **13** train (published split 514/512) |

Do **not** report 100% on the full bench. Rate is over the mapped countable subset only (`25/1026`). Eval-split **514** is the published test partition, not a false-pass figure and not 12/514 product accuracy.

New Hub files used for probes: `digital_hub` (arc/heating/ventilation), `sixty5/str` (not the 342 MB `arc.ifc`), `wbdg_office` (mep/str). `west_riverside_hospital` is on disk (IFC2X3+IFC4 twins) but has **0** v2 QA rows — inventory only. SHA-256 skipped for IFC larger than 80 MiB.

## Integrity

- Questions SHA-256 measured: `e47ccd097306f5bca49b9c8ac0b4cd72f296df9f7ff7a02625b3f06c1691da9b` (matches AeroBIM pin; HF card pin `8f08f5d0…` is stale).
- Local IFCs present: **19** files under `.local/ifc-bench-v2/projects` (duplex, dental_clinic, digital_hub, sixty5, wbdg_office). GPLv3 project dirs were not downloaded.

## Claims Lock

Not product accuracy. Never claim >90% from this smoke. Checkpoint remains **NO_GO**.
