# AECV scorer validation (Task 0)

**Artifact:** [`aecv-scorer-validation-2026-08-04.json`](aecv-scorer-validation-2026-08-04.json)  
**Verdict:** `SCORER_REPRODUCES_TABLE1_WITHIN_TOLERANCE`  
**claim_level:** `open_bench_only` · **closes_rt001:** `false`

## What this proves

Offline re-score of the authors' per-plan prediction JSONs (120 plans, ten Table 1 models) reproduces published Table 1 means within the stated band:

| | |
|---|---:|
| max \|Δ\| | 0.0203 |
| median \|Δ\| | 0.0042 |
| gate tolerance | 0.025 (stated band 0.02) |

This is **agreement within tolerance**, not bit-identical tooling. Without this artifact, a live macro is just a number; with it, the number comes from a scorer shown to reproduce Table 1 on the authors' own predictions.

## Metric key (do not mix)

| Key | Definition | Use |
|---|---|---|
| **`macro_extended`** | mean over Door/Window/**Space**/Bedroom/Toilet | **Table 1 compare / live headline** (matches upstream `visualizer.py` `mean_accuracy`) |
| `macro_bench_protocol` | mean over Door/Window/Bedroom/Toilet | Reference only (paper prose §3.1.1 / heatmap display) |
| `macro_exact_match_rate` | bound to `macro_extended` in live summary | Canonical publish name |

Paper prose cites four classes; heatmaps omit Space for display. Upstream code averages **five** fields. Offline rescore of Table 1 aligns with five-field means and **diverges** from four-class means — therefore Table 1 values are five-field.

## Live hierarchy (corrected)

| Key | Live value | Role |
|---|---:|---|
| **`macro_extended`** | **0.4325** | Comparable to Table 1 |
| `macro_bench_protocol` | 0.5064 | Four-class reference — **do not** put against Table 1 |

If three vendor-rejected plans count as misses: five-field ≈ **0.422**.

## Provenance pin

From `object_counting_offline.provenance` in `aecv-bench-eval-latest.json`:

- **repo:** https://github.com/AECFoundry/AECV-Bench  
- **commit:** `1c88ec2da9ca40d9bda3311cc544816c37e73fe1`  
- **path:** `data/Use Case 1 - Object Counting/1 - Full Datasets/{plan_id}/{model}.json`  
- **tree sha256:** recorded in JSON (`predictions_tree_sha256`)  
- **17 repo-only models** — cite as repo baseline, not peer-reviewed Table 1.

## Defense one-liner

> Before asking whether the live macro is meaningful: the same scorer reproduces ten published Table 1 means within |Δ|≤0.02 (median ~0.004) when re-scoring the authors' own prediction files on the five-field metric (Space included).
