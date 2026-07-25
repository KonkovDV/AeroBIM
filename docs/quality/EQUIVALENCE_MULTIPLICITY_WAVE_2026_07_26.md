---
title: "Equivalence gate (TOST) + multiplicity control for system comparison"
status: done
version: "1.0.0"
last_updated: "2026-07-26"
claim_boundary: "TOST verdicts hold only at the pre-specified SESOI margin on the shared fixture corpus; never customer accuracy (RT-001). Checkpoint stays NO_GO."
---

# Wave M — Equivalence testing + multiplicity control (2026-07-26)

## External anchors (Jul 2026)

| Domain | Anchor |
|---|---|
| TOST origin | Schuirmann 1987 — two one-sided tests for bioequivalence |
| CI-inclusion form | Berger & Hsu 1996 — equivalence at α iff the (1−2α) CI ⊂ (−margin, +margin) |
| SESOI margins | Lakens 2017 (primer) / Lakens, Scheel & Isager 2018 (tutorial) — margin must be a pre-specified smallest effect size of interest; 90% CI at α=0.05 |
| Bootstrap variant | Robinson & Froese 2004; R `equivalence` package (Robinson) — TOST wrapped in bootstrap |
| LLM-eval practice | OpenReview 2026 "An Equivalence-Test Audit of LLM Logprob Calibration" — TOST with pre-specified margins + paired-bootstrap inference as the right primitive for audit-class claims |
| FWER control | Holm 1979 — step-down Bonferroni, valid under arbitrary dependence |
| NLP multiplicity practice | Dror, Baumer, Bogomolov & Reichart 2017 (TACL) — replicability analysis: Bonferroni-family corrections across multiple comparisons |
| Never-zero p | Phipson & Smyth 2010 — add-one estimator carried over to bootstrap tail p-values |

## Gaps closed (both declared in Wave L "Explicitly NOT claimed")

1. **No equivalence gate.** `--fail-on-regression` tests H0 "no difference" —
   non-rejection can never certify "the refactor changed nothing" (absence of
   evidence ≠ evidence of absence). Extractor/dependency bumps that *should*
   be behavior-preserving (docling pin bumps, pure refactors) had no
   statistically defensible safety gate.
2. **No multiple-comparison correction** across the four reported metrics —
   the artifact invited cherry-picking a nominally significant secondary.

## Delivered (code + test)

- `domain/eval_statistics.py`:
  - `equivalence_tost` — paired cluster-bootstrap TOST in the Berger–Hsu
    CI-inclusion form: equivalence at α iff the (1−2α) percentile CI of
    metric(B)−metric(A) lies strictly inside (−margin, +margin); one-sided
    bootstrap tail p-values with the add-one estimator (never zero);
    `p_tost = max(p_lower, p_upper)`; **margin (SESOI) has no default — it
    must be pre-specified**; fail-closed: `n < 5` clusters → `stable=False`
    and `equivalent` forced False (a tiny corpus cannot certify equivalence);
  - `holm_bonferroni` (+ `HolmResult`) — Holm 1979 step-down adjustment with
    the running-max monotonicity step, cap at 1, valid under arbitrary
    dependence.
- `tools/compare_extraction_runs.py` (artifact `schema_version` 1.1.0):
  - every metric now carries `holm_adjusted_p` + `significant_after_holm`;
    `multiple_comparisons` block names the method, family size, and macro-F1
    as the single pre-registered primary endpoint (the regression gate is
    unchanged — Holm qualifies the descriptive secondaries);
  - `--equivalence-margin` adds a per-metric `equivalence` TOST block;
  - `--fail-on-nonequivalence` — refactoring-safety gate: exit 1 unless
    macro-F1 TOST declares equivalence at the pre-specified margin (rejects
    both real shifts *and* under-powered corpora — fail-closed in the
    direction opposite to `--fail-on-regression`).
- `tests/test_equivalence_and_multiplicity.py` — 15 tests with
  hand-computed references: degenerate-CI identity case (p = 1/(B+1) by
  add-one); uniform 1/3 shift → `p_upper = 1`, not equivalent at 0.05 but
  equivalent at 0.5 (margin-relativity by design); n=3 withholds the verdict;
  Holm worked example (0.01, 0.02, 0.03, 0.20) → (0.04, 0.06, 0.06, 0.20)
  with the running-max step shown on (0.04, 0.05) → (0.08, 0.08); cap at 1;
  CLI exit codes for both gate directions; margin required by the gate.

## Statistical notes (for the record)

- TOST and the regression test answer *different questions*; a run can be
  simultaneously "no significant regression" and "not equivalent" — that is
  the under-powered case the new gate is designed to catch.
- The bootstrap TOST inherits Wave K/L's exchangeable unit (the fixture) and
  percentile method; a degenerate resampling distribution (all diffs equal)
  yields a point CI, which is the correct limiting behavior.
- Holm was chosen over Benjamini–Hochberg deliberately: the family is small
  (4 metrics) and the artifact feeds go/no-go gates, where FWER — not FDR —
  is the right error to control (Dror et al. 2017 make the same call for
  accept/reject verdicts in NLP).

## Explicitly NOT claimed

- No default margin: an unjustified SESOI would be pseudo-rigor (Lakens
  2018); the margin is a per-invocation engineering decision that must be
  recorded with the run.
- TOST equivalence on fixtures never implies customer-corpus equivalence
  (RT-001 unchanged).
- Holm is applied within the 4-metric family of one comparison, not across
  comparisons over time (sequential/always-valid inference is a separate
  design). **Closed by Wave O:**
  [`SEQUENTIAL_EVALUE_WAVE_2026_07_26.md`](SEQUENTIAL_EVALUE_WAVE_2026_07_26.md)
  (e-process regression monitor, Ville-type anytime-valid control).

## Gate evidence (2026-07-26 local)

`ruff format/check` PASS · `mypy src` 195 files PASS · `pytest tests -q`
**1023 passed, 7 skipped**.
