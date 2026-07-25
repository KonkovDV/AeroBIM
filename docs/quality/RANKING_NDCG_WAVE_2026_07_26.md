---
title: "Tie-aware nDCG ranking-quality harness"
status: done
version: "1.0.0"
last_updated: "2026-07-26"
claim_boundary: "nDCG на fixture-корпусе никогда не публикуется как качество ранжирования продукта (RT-001); nDCG не влияет на summary.passed. Checkpoint остаётся NO_GO."
---

# Wave N — Tie-aware nDCG ranking quality (2026-07-26)

## External anchors (Jul 2026)

| Domain | Anchor |
|---|---|
| Metric origin | Järvelin & Kekäläinen 2002 — DCG/nDCG, log2 discount |
| Theory | Wang et al. 2013 (COLT) — logarithmic discount yields consistent distinguishability between ranking functions |
| Ties | **McSherry & Najork 2008 (ECIR)** — expected metric value over within-tie permutations, closed form |
| Gain | Burges et al. 2005; MSLR/LETOR convention — exponential gain 2^rel − 1 for graded relevance |
| Metric choice | Fuhr 2018 (SIGIR Forum) — MRR/ERR violate basic metric requirements; Valcarce et al. — nDCG has the best discriminative power among common IR metrics |
| Uncertainty | Wave K cluster bootstrap (Efron & Tibshirani); Oosterhuis 2024 (KDD) — reliable CIs for IR metrics as current reporting norm |
| Pitfall | sklearn `ndcg_score` silently scores all-irrelevant lists as 0 — a known trap when averaging |

## Gap closed

TZ v2 §9.1 declares "nDCG (graded 0/1/2)" for ranking; harness runbook said
**planned — не реализован** (2026-07-24); Checkpoint #2 DoD item "nDCG —
если реализован или явно planned" was open. September pilot metrics include
«качество расстановки приоритетов» with no measuring instrument.

**Why tie-awareness is the design center:** `compute_issue_priority` returns
small deterministic integers — tied scores are the norm. A naive nDCG scores
whatever order the sort happened to emit, silently rewarding (or punishing)
arbitrary within-tie order; run-to-run "improvements" could be pure tie
shuffling. The expected-DCG closed form (mean tie-group gain × sum of the
group's position discounts) is permutation-invariant and deterministic.

## Delivered (code + test)

- `domain/ranking_quality.py` — `tie_aware_ndcg(items, k, gain)`:
  exponential (default, 2^rel−1) or linear gain; log2 discount; cutoff@k
  with correct handling of the tie group straddling the cutoff (expected
  gain per position unchanged; only discounts ≤ k counted); **fail-closed
  undefined case**: IDCG = 0 → `defined=False`, never a silent 0 or 1.
- `domain/eval_statistics.py` — `scalar_cluster_bootstrap_ci`: generic
  percentile cluster bootstrap for per-case scalar metrics (same method,
  stability floor and determinism as Wave K).
- `tools/evaluate_ranking_quality.py` — CLI: `ranking_quality_labels`
  artifact (per case: `finding_id`, `priority_score`, `relevance` 0/1/2) →
  per-case nDCG@5/@10/full + bootstrap CI of the mean over **defined** cases;
  undefined cases listed by id; duplicate case/finding ids and out-of-range
  grades rejected; non-adjudicated datasets carry the mandatory
  not-publishable warning (mirrors `evaluate_detection_precision`).
- `tests/test_ranking_quality.py` — 17 tests with hand-computed references:
  worst-order nDCG written out against explicit discounts; **closed form
  verified against full enumeration of tie permutations** (2-item tie: mean
  of DCG 3·1 and 3·d₃); cutoff-straddling tie gives exactly 0.5; input-order
  invariance under ties; undefined ≠ 0; degenerate CI; CLI shape/rejection/
  determinism/output-file cases.

## Statistical notes (for the record)

- The case (document/package ranking) is the exchangeable unit, consistent
  with Waves K–M; per-case nDCG values feed the generic scalar bootstrap.
- Excluding IDCG=0 cases from the mean (with explicit counting) follows the
  standard IR treatment of topics with no relevant documents; both fixed
  conventions (0 or 1) bias the mean in opposite directions.
- Comparing two rankers on the same labeled corpus should reuse Wave L/M
  machinery (paired permutation + Holm + TOST) over per-case nDCG — the
  values plug directly into `scalar` pairing; wiring that CLI is deferred
  until two real ranker variants exist.

## Explicitly NOT claimed

- No ranking-quality threshold: the TZ says «согласовать на пилоте» — the
  tool reports CIs, the threshold is a customer decision.
- Fixture nDCG never demonstrates customer ranking quality (RT-001).
- nDCG is advisory ordering measurement only; it never changes severity or
  `summary.passed` (same boundary as the priority score itself).

## Gate evidence (2026-07-26 local)

`ruff format/check` PASS · `mypy src` 197 files PASS · `pytest tests -q`
**1040 passed, 7 skipped**.
