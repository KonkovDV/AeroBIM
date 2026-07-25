# Red Team Audit — Statistical Surfaces (Waves K–O), 2026-07-26

**Scope:** `domain/eval_statistics.py`, `domain/ranking_quality.py`,
`domain/sequential_inference.py`, `tools/compare_extraction_runs.py`,
`tools/evaluate_ranking_quality.py`, `tools/sequential_regression_monitor.py`.
**Method:** hypothesis-driven runtime probes (throwaway script, deleted after
the audit); every finding below was **confirmed by execution**, then fixed,
then pinned by a kill-test in `tests/test_rt_stats_surfaces_2026_07_26.py`.

## Findings and fixes

| ID | Severity | Confirmed exploit (runtime output) | Fix |
|----|----------|------------------------------------|-----|
| RT-A | **Critical** | `equivalence_tost(..., replicates=0)` → `equivalent=True` with CI `[0, 0]` while the observed diff was **0.333 against a 0.05 margin** — a free equivalence certificate with zero bootstrap evidence. Same degenerate-CI hole in `scalar_cluster_bootstrap_ci` (CI `[0,0]` around point 0.9). | All five bootstrap/MC entry points (`cluster_bootstrap_cis`, `scalar_cluster_bootstrap_ci`, `paired_permutation_test` MC path, `paired_bootstrap_diff_ci`, `equivalence_tost`) now reject `replicates < 1`. |
| RT-B | **High** | Python `json.loads` accepts `NaN`; a labels file with `priority_score: NaN` reached `tie_aware_ndcg`, where NaN breaks both sorting and tie-group equality: **nDCG 0.964 vs 0.689 depending on input order** — the permutation-invariance guarantee was silently void. | `tie_aware_ndcg` rejects non-finite scores (fail closed); covered at both the domain and CLI artifact levels. |
| RT-C | **High** | The shared comparison loader accepted `true_positives: -5` and duplicate `fixture_id` rows (silent last-wins) — poisoned artifacts could shift p-values/CIs without a trace. | `_load_fixture_counts` rejects negative confusion counts and duplicate fixture ids; 10 MB input-size guard added (parity with `evaluate_detection_precision`). |
| RT-D | Medium | Monitor state persisted `wealth` rounded to 6 dp (`4.508348173337161` → `4.508348`): martingale drift accumulates across CLI restarts and can matter near the Ville threshold. | State dict is the persistence format — full float precision for `p_value`/`e_value`/`wealth`; round-trip is bit-exact (test). |
| RT-E | Medium | Tampered state `alpha=0.999999` loaded fine → Ville threshold **1.000001** (alarm fires on almost any run); unknown `calibrator` fell through to the mixture branch silently. | `_state_from_dict` routes parameters through the same validation as fresh state; wealth must be positive and finite. |
| RT-F | Low | `--alpha`/`--calibrator` silently ignored when a state file exists (alpha-shopping trap); duplicate/non-positive `--cutoffs` collapsed summary keys. | Explicit stderr warning on parameter conflict; cutoffs must be unique positive integers. |

## What was checked and found sound

- One-sided permutation p-values include the identity flip (super-uniform —
  valid calibrator inputs); add-one estimator intact on all MC paths.
- `update_e_process` rejects duplicate `run_id` (no evidence double-count);
  `rejected` latch is monotone (safe-testing semantics).
- Holm running-max monotonicity and cap at 1; kappa/alpha domain checks.
- Tie-aware nDCG cutoff handling verified against full permutation
  enumeration (existing Wave N tests).
- No network/exec/path-traversal surfaces in the audited tools (local file
  CLIs; paths are user-owned inputs).

## Gate evidence (post-fix, 2026-07-26 local)

`ruff format/check` PASS · `mypy src` 199 files PASS · `pytest tests -q`
**1069 passed, 7 skipped** (12 new RT kill-tests). Probe script re-run
post-fix: first exploit now raises `ValueError` (fail closed).

## Claim boundary

Fixes harden the *fixture-corpus* evaluation toolchain; nothing here
upgrades fixture evidence to customer evidence (RT-001). Checkpoint stays
**NO_GO**.
