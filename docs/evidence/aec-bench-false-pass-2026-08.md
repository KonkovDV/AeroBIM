<!-- claims-lint: allow-file reason="AEC-Bench false-pass SKIPPED; inventory is not product accuracy" -->
---
title: "AEC-Bench false-pass measurement — SKIPPED"
date: "2026-08-13"
claim_boundary: "SKIPPED. Inventory 196 is not a false-pass rate. Not RT-001. Not product accuracy."
---

# AEC-Bench false-pass — SKIPPED (honest)

**Status:** `SKIPPED`  
**claim_level:** `open_bench_only`  
**closes_rt001:** `false`

AEC-Bench ([arXiv:2603.29199](https://arxiv.org/abs/2603.29199), Apache 2.0) is inventoried: **196** tasks in [`aec-bench-smoke-latest.json`](aec-bench-smoke-latest.json). Harbor agent trial is `NOT_RUN` (no paid agent key / Docker trial). Mushkani et al. ([arXiv:2607.29058](https://arxiv.org/abs/2607.29058)) 160-task compliance subset is **not executed**.

## Why SKIPPED (not a hidden fail)

| Gate | Result |
| --- | --- |
| Inventory | 196 tasks, 9 families, 3 scopes — **done** 2026-08-03 |
| Prefetch sample | 3 sheets downloaded — **done** |
| Agent trial / 160-task slice | **NOT_RUN** |
| False-pass rate | **not measured** |
| Cluster bootstrap (project as unit) | **not measured** |
| Four-outcome table | **not measured** |

Publishing a percent here would be a fabricated metric. Calendar: full protocol is 17.08; if agent budget is still absent, keep SKIPPED.

## What we will measure when the run exists

1. **Observation unit = project**, not task (Mushkani: 29 projects). Cluster bootstrap CI.
2. **False pass first** (system says compliant, gold says violation). False fail is secondary.
3. Four outcomes: TP / FP / FN / TN — not binary accuracy.
4. Calibration + selective-risk curve if a confidence score exists; else say it does not.

Until that artifact has a hash, the only citeable sentence is: **false-pass rate not measured**.
