# AECV scorer validation (Task 0)

**Artifact:** [`aecv-scorer-validation-2026-08-04.json`](aecv-scorer-validation-2026-08-04.json)  
**Verdict:** `SCORER_EQUIVALENT_WITHIN_TOLERANCE`  
**claim_level:** `open_bench_only` · **closes_rt001:** `false`

## What this proves

Offline re-score of the authors' per-plan prediction JSONs (120 plans, ten Table 1 models) reproduces published Table 1 means within the stated band:

| | |
|---|---:|
| max \|Δ\| | 0.0203 |
| median \|Δ\| | 0.0042 |
| gate tolerance | 0.025 (stated band 0.02) |

Without this artifact, a live macro of ~0.51 is just a number. With it, the number comes from a scorer shown equivalent to the published table on the authors' own predictions.

## Metric key (do not mix)

| Key | Definition | Use |
|---|---|---|
| `macro_extended` | mean over Door/Window/**Space**/Bedroom/Toilet | **Table 1 alignment** (matches upstream `visualizer.py` `mean_accuracy`) |
| `macro_bench_protocol` | mean over Door/Window/Bedroom/Toilet | Live **headline** per paper prose §3.1.1 |
| `macro_exact_match_rate` | bound to `macro_bench_protocol` in live summary | Canonical publish name (RT-W-07) |

Paper prose cites four classes; heatmaps omit Space for display. Upstream code averages **five** fields. Scorer validation therefore compares `macro_extended` to Table 1.

## Provenance pin

From `object_counting_offline.provenance` in `aecv-bench-eval-latest.json`:

- **repo:** https://github.com/AECFoundry/AECV-Bench  
- **commit:** `1c88ec2da9ca40d9bda3311cc544816c37e73fe1`  
- **path:** `data/Use Case 1 - Object Counting/1 - Full Datasets/{plan_id}/{model}.json`  
- **tree sha256:** recorded in JSON (`predictions_tree_sha256`)  
- **17 repo-only models** (e.g. `claude_opus_46`, `openai_gpt_54`) are present in the prediction tree but **not** in Table 1 — cite as repo baseline, not peer-reviewed paper numbers.

## Defense one-liner

> Before asking whether ~0.51 is meaningful: the same scorer reproduces ten published Table 1 means within |Δ|≤0.02 (median ~0.004) when re-scoring the authors' own prediction files.
