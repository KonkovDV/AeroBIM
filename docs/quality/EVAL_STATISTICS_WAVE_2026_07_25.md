---
title: "Evaluation statistics: bootstrap CIs + κ/α agreement"
status: done
version: "1.0.0"
last_updated: "2026-07-25"
claim_boundary: "CIs and agreement quantify fixture-label uncertainty; they never upgrade fixture evidence to customer evidence (RT-001). Checkpoint stays NO_GO."
---

# Wave K — Academic-grade evaluation statistics (2026-07-25)

## External anchors (Jul 2026)

| Domain | Anchor |
|---|---|
| Error-bar reporting | NeurIPS Paper Checklist — error bars mandatory, method stated; ACL Responsible-NLP checklist — bootstrap 1000 resamples, 95% CI (seen applied in 2026.acl-long checklists) |
| Bootstrap | Efron & Tibshirani 1993 — percentile bootstrap; **cluster** resampling because the fixture (document) is the sampling unit (instances within a document are not i.i.d.) |
| Agreement | Cohen 1960 (κ); Krippendorff 2019 (nominal α, coincidence-matrix formulation, customary α≥0.667 cut-off) |
| Internal gate | `precision_claim_publishable_with_agreement` (RT-001) — previously consumed hand-made agreement JSON; **no calculator existed in-repo** |

## Gaps closed

1. Benchmark artifacts reported **point estimates only** (macro-F1≈0.86) — not
   publishable by 2026 reporting norms; uncertainty was invisible.
2. The RT-001 κ/α gate had no in-repo, deterministic, tested implementation of
   κ or α — agreement artifacts had to be produced by hand.

## Delivered (code + test)

- `domain/eval_statistics.py` (pure stdlib, deterministic):
  - `cluster_bootstrap_cis` — percentile bootstrap over **fixtures** (B=1000
    default, α=0.05, fixed seed 20260725); returns per-metric
    `BootstrapCI{point, lower, upper, replicates, seed, n_clusters, stable}`;
    `stable=False` honesty flag when n_clusters < 5;
  - `cohen_kappa` — two-annotator nominal κ;
  - `krippendorff_alpha_nominal` — ≥2 annotators, missing labels tolerated,
    coincidence-matrix formulation (α = 1 − (n−1)Σo_ck/(n²−Σn_c²));
  - `agreement_artifact` — emits the exact shape the RT-001 gate consumes
    (`cohen_kappa`, `krippendorff_alpha`, `pass_threshold_0_60`,
    `pass_alpha_0_67`), thresholds κ≥0.60 / α≥0.67.
- `tools/evaluate_extraction.py`: artifact gains an `uncertainty` block
  (method, resampling unit, replicates, seed, per-metric CIs, claim boundary);
  new `--bootstrap` / `--seed` flags; all additive — legacy consumers intact.
- `tests/test_eval_statistics.py` — 15 tests incl. **hand-computed reference
  values** (κ = 0.24/0.44 = 0.5454…; nominal α = 1 − 18/66 = 0.7272…),
  seed-determinism, degenerate perfect-corpus CI, small-n instability flag,
  end-to-end integration with the RT-001 publishability gate (high agreement
  passes, systematic disagreement blocks).

## Live result on the RU fixture corpus

`evaluate_extraction --min-macro-f1 0.70` → macro-F1 **0.86, 95% CI [0.78, 0.94]**
(cluster bootstrap, n=10 fixtures, seed 20260725). The interval makes the
forbidden ">90% accuracy" claim visibly indefensible even on fixtures.

## Explicitly NOT claimed

- No significance testing between systems (no comparison target yet).
- CIs on fixtures ≠ customer accuracy; RT-001 still requires customer corpus,
  ≥2 adjudicators, held-out split, FN tracking — unchanged.

## Gate evidence (2026-07-25 local)

`ruff format/check` PASS · `mypy src` 194 files PASS · `pytest tests -q`
**997 passed, 7 skipped**.
