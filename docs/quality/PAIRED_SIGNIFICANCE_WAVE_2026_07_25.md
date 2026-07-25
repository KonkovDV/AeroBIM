---
title: "Paired significance testing for system comparison"
status: done
version: "1.0.0"
last_updated: "2026-07-25"
claim_boundary: "Paired verdicts describe the shared fixture corpus only; never customer accuracy (RT-001); non-significant ≠ equivalent. Checkpoint stays NO_GO."
---

# Wave L — Paired significance testing (2026-07-25)

## External anchors (Jul 2026)

| Domain | Anchor |
|---|---|
| Protocol | statsforevals.com — test-selection protocol for NLP/LLM comparisons (bootstrap, permutation, Wilcoxon, McNemar) |
| Exact variant | Zmigrod et al. 2022 (ETH) — exact paired-permutation testing for structured statistics |
| Never-zero p | Phipson & Smyth 2010 — Monte-Carlo permutation p-values must use the add-one estimator |
| Harness enforcement | arXiv 2511.06701 — harnesses should call `paired_permutation_pvalue` structurally, not leave rigor to authors |
| Classic | Noreen 1989; Dror et al. 2018 ("Hitchhiker's Guide" to significance in NLP) |

## Gap closed

Wave K honestly declared "no significance testing between systems". Yet the
real comparison target exists: extractor upgrades (docling bumps, synthesis
rule changes) were judged by eyeballing Δmacro-F1 with no notion of whether
the delta exceeds fixture-sampling noise.

## Delivered (code + test)

- `domain/eval_statistics.py`:
  - `paired_permutation_test` — two-sided paired sign-flip test on aligned
    fixtures; **exact enumeration of all 2ⁿ flips for n≤12** (`exact=True`,
    p from the full null distribution), Monte-Carlo with **add-one** estimator
    otherwise (p can never be 0); deterministic given seed;
  - `paired_bootstrap_diff_ci` — percentile CI of metric(B)−metric(A) with
    **joint index resampling** (pairing preserved); corroborates the
    permutation verdict when the CI excludes zero.
- `tools/compare_extraction_runs.py` — CLI: aligns two
  `extraction_quality_report` artifacts by `fixture_id`, reports per-metric
  observed diff + exact/MC p-value + diff CI + `significant` flag; surfaces
  unaligned fixtures; `--fail-on-regression` exits 1 on a significant
  macro-F1 drop (CI-ready regression gate); deterministic seed.
- `tests/test_paired_significance.py` — 11 tests with **hand-enumerated
  references**: n=2 uniform improvement → p = 2/4 = 0.5 (all four masks
  written out); n=10 uniform improvement → p = 2/1024; single pair → p = 1;
  identical systems → p = 1 and diff CI degenerate at 0; MC determinism and
  add-one positivity; CLI shape/regression-exit/disjoint-id cases.

## Statistical notes (for the record)

- The fixture is the exchangeable unit (documents), consistent with Wave K's
  cluster bootstrap — instance-level flips would overstate n.
- Two-sided by construction (|diff| ≥ |observed|); exact path needs no seed.
- The `--fail-on-regression` gate tests H0 "no difference", so it cannot
  certify equivalence; an equivalence (TOST) gate would be a separate design.

## Explicitly NOT claimed

- No multiple-comparison correction across the four reported metrics (single
  primary metric macro-F1 drives the regression gate; others are descriptive).
  **Closed by Wave M:** [`EQUIVALENCE_MULTIPLICITY_WAVE_2026_07_26.md`](EQUIVALENCE_MULTIPLICITY_WAVE_2026_07_26.md)
  (Holm-adjusted p-values + TOST equivalence gate).
- Fixture-corpus verdicts only; RT-001 unchanged.

## Gate evidence (2026-07-25 local)

`ruff format/check` PASS · `mypy src` 195 files PASS · `pytest tests -q`
**1008 passed, 7 skipped**.
