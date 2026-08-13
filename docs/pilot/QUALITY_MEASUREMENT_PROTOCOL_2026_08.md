<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
---
title: "Quality measurement protocol — AeroBIM pilot (Aug 2026)"
status: active
version: "1.0.0"
last_updated: "2026-08-14"
claim_boundary: "Protocol only. Fixture/open corpora never publish product accuracy. Interim confirmed-finding target is 0.60 — not >90%."
---

# Quality measurement protocol (WP-07)

Executable companion: `python -m aerobim.tools.compute_quality_protocol_stats`  
Open-data rails (regression / timing only): [`samples/benchmarks/open-corpora/`](../../samples/benchmarks/open-corpora/README.md) · `run_open_corpora_profiles`  
Expert labeling instruction: [`EXPERT_LABELING_INSTRUCTION_2026.md`](EXPERT_LABELING_INSTRUCTION_2026.md)  
Harness runbook: [`HARNESS_AND_DEMO_RUNBOOK_2026.md`](HARNESS_AND_DEMO_RUNBOOK_2026.md)

## 1. Purpose and claim boundary

This protocol defines **how** pilot quality is measured once a customer corpus and dual-expert adjudication exist. It does **not** authorize publishing product accuracy from fixtures or open corpora.

| Allowed now | Forbidden without RT-001 adjudicated corpus |
|---|---|
| Pre-register schema, strata, n, Wilson CI plan | Product precision / recall as customer KPI |
| Fixture binary IDS regression (WP-06) | «>90% accuracy» |
| Timing on open packs (WP-06) | Customer SLA from fixture wall-clock |
| Interim target TP/(TP+FP) ≥ **0.60** (planning) | Treating κ≈0.8 on n≈30 as settled |

## 2. Stratification (discipline × criticality)

Sample **before** first look at detections. Minimum strata axes:

| Axis | Levels (start) | Why |
|---|---|---|
| Discipline | AR, KZH/KR, MEP, other-in-scope | Error rates differ by discipline |
| Criticality | Critical, Warning, Info | Critical drives Shared-gate; do not pool blindly |
| Finding class | clash, attribute, dimension, area, cross_document, missing_element, other | Aligns with expert instruction |
| Cognitive axis (report with class) | Recognition / Reasoning / Judging / Formal-check | MechVQA (arXiv:2605.30794) + BRAVO layers; do **not** publish only a macro % |
| Modality (optional) | IFC-native, PDF/scan, hybrid | OCR/VLM paths are advisory-only until grounded |

**Allocation:** proportional to expected finding mass per stratum, with a floor so each critical stratum has enough labeled items for a stratum-local Wilson interval (see §4). Pre-register the allocation table in the pilot kickoff memo; do not re-weight after seeing system outputs.

## 3. Pre-registered labeling schema

Freeze **before** adjudicators open the corpus (no peeking):

| Field | Allowed values | Notes |
|---|---|---|
| `match_key` | stable id | Finding id or FN candidate key |
| `adjudicator_id` | named expert | ≥2 independent |
| `verdict` | TP / FP / FN / excluded / unresolved | `unresolved` never publishes |
| `finding_class` | see §2 | One primary class |
| `severity_expert` | Critical / Warning / Info | May differ from system |
| `notes` | free text | Evidence pointer mandatory for TP |
| `adjudication_status` | pending / resolved | After disagreement meeting |

Templates: `samples/benchmarks/detection-precision/` (`adjudication-template.csv`, `labels-*.json`, `ranking-labels-template.json`).

## 4. Sample size guidance (Wilson)

Do **not** quote «κ > 0.8» without n. Use Wilson score intervals (Wilson 1927; Brown–Cai–DasGupta 2001 recommendation) for binomial rates.

```bash
cd backend
# Precision/recall Wilson from TP/FP/FN
python -m aerobim.tools.compute_quality_protocol_stats --tp 83 --fp 28 --fn 12

# Sample-size planner: expected p, half-width margin, confidence
python -m aerobim.tools.compute_quality_protocol_stats \
  --expected-p 0.75 --margin 0.08 --confidence 0.95
```

Default planning anchors (recompute if the customer changes assumptions):

| Goal | Default inputs | Planner output (indicative) |
|---|---|---|
| Demonstrate interim TP/(TP+FP) ≥ 0.60 with power | p0=0.60, p_true=0.75, α=0.05, power=0.8 | also via `plan_adjudication_corpus` (~62 for power; **111** when CI half-width ≤ 0.08 dominates) |
| Wilson half-width ≤ margin at expected_p | e.g. p=0.75, margin=0.08, conf=0.95 | `required_n` from this tool |

Exact binomial power is sawtoothed in n — nearby n are equivalent design points (`plan_adjudication_corpus`).

## 4.1. LLM reproducibility probes (P₁ / P₂) — sample-size planning

Vendor behaviour probes (deep analysis §2.1–2.2) split:

| Property | Meaning | Experiment |
|---|---|---|
| **P₁** | Intra-session determinism at fixed URI / prompt / `temperature=0` | `k` repeats per prompt; share of prompts with identical response hashes |
| **P₂** | Stability across time at same URI | Same prompts after Δ (e.g. 14 days); share matching original hashes |

Plan `n` (distinct fixture prompts) with the **existing** Wilson / adjudication planners — do not invent `n` ad hoc:

```bash
# Same tools as §4 — e.g. expected p≈0.9, half-width 0.08, conf=0.95
python -m aerobim.tools.compute_quality_protocol_stats \
  --expected-p 0.9 --margin 0.08 --confidence 0.95
# or plan_adjudication_corpus for power-aware nearby n
```

Publish the **lower Wilson bound**, not the point estimate. P₁/P₂ measure vendor behaviour; they are **not** a gate for report FAIR reproducibility (deterministic core + provenanced annotation — Claims Lock / `REPRODUCIBILITY-2026.md`).

## 5. Interim pilot confirmed-finding rate

**Target:** TP / (TP + FP) ≥ **0.60** on the held-out adjudicated slice (Samolet / MIK interim contract — not ТЗ aspirational >0.90).

Publish only when:

1. corpus_kind = customer (or explicitly scoped pilot pack),
2. ≥2 adjudicators, κ/α above the **task-justified** threshold (start κ ≥ 0.60; do not treat 0.8 as magic),
3. Wilson CI reported; prefer demonstrating the target via lower Wilson bound when claiming «threshold met».

Fixture / open-corpora binary match rates are **not** this metric.

## 6. Disagreement resolution

1. Dual-blind labeling (experts do not see each other’s marks or LLM «votes»).
2. Compute Cohen’s κ / Krippendorff’s α (`measure_adjudicator_agreement`).
3. If below agreed threshold → clarify class definitions; **do not** nudge labels toward the system.
4. Residual conflicts → adjudication meeting (third expert or customer sponsor); write `adjudication_status=resolved` + final verdict.
5. Items left `unresolved` are excluded from publishable precision.

### 6.1 LLM-as-a-judge (triage only)

AECV-Bench uses LLM-as-a-judge + human adjudication on edge cases. AeroBIM allows an LLM judge **only** as a queue/triage ranker to reduce expert load — **never** as publishable truth for RT-001 precision, and never as a substitute for κ/α. ChartMuseum (Tang et al. 2026) shows judges can mask perceptual errors; disputed and critical strata stay human-only (see also VLM protocol).

## 7. Ranking quality (nDCG)

After graded labels (relevance 0/1/2) are adjudicated:

```bash
python -m aerobim.tools.evaluate_ranking_quality \
  --labels ../samples/benchmarks/detection-precision/<ranking-labels>.json \
  --output ../artifacts/pilot-evidence/<run-id>/ranking-report.json
```

Method (implemented): tie-aware expected nDCG@5/10/full (McSherry–Najork 2008), exponential gain, cluster-bootstrap CI. nDCG never flips `summary.passed`. Fixture nDCG is not customer ranking quality (RT-001).

`compute_quality_protocol_stats` references this tool; it does not recompute nDCG.

## 8. Relation to WP-06 open corpora

| Profile | Role in this protocol |
|---|---|
| regression | Engine binary pass/fail fidelity on pinned IDS/IFC (honest count documented; not ≥250 today) |
| pilot-approx | Package analyze timing on public IFC + residential inventory |
| load | AR/KZH cross-doc + MEP federated path timing |

Every open-corpora artifact carries: *open sets lack expert TP/FP → regression/timing only, NOT product accuracy*.

L1 public benches (IFC-Bench smoke, AECV live counting, AEC-Bench inventory) are separate: see [`../quality/OPEN_BENCH_VS_RT001_DECISION_2026_08_04.md`](../quality/OPEN_BENCH_VS_RT001_DECISION_2026_08_04.md) and [`../quality/RED_TEAM_AECV_LIVE_YANDEX_2026_08_04.md`](../quality/RED_TEAM_AECV_LIVE_YANDEX_2026_08_04.md).

## 9. Acceptance checklist (protocol ready for customer negotiation)

- [x] Stratification axes written (§2)
- [x] Pre-registered schema (§3)
- [x] Sample-size + Wilson tool executable (§4)
- [x] Disagreement order written (§6)
- [x] Interim confirmed-finding target = 0.60 (§5)
- [x] nDCG path referenced to `evaluate_ranking_quality` (§7)
- [ ] Customer sign-off on strata allocation + n + κ threshold (external)

## 10. Task-07 acceptance additions (18.08.2026)

These constraints are mandatory when Samolet labels exist. They do **not** authorize publishing product accuracy from fixtures, AEC-Bench inventory, or MOEXP engine coverage.

| Rule | Why |
| --- | --- |
| **Observation unit = project** (or signed package), not finding/task | Tasks in one drawing are correlated. Mushkani et al. [arXiv:2607.29058](https://arxiv.org/abs/2607.29058) report 29 projects / 160 tasks. Cluster bootstrap, not iid binomial on tasks. |
| **False pass first** | System says compliant, gold says violation. This is the dangerous error for expertise. Report FP (false pass) separately from FN. |
| **Four outcomes, not binary accuracy** | TP / FP / FN / TN aligned with `PackageOutcome` (FAILED / BLOCKED / REVIEW_REQUIRED / PASS*). Do not collapse to «% correct». |
| **Selective-risk curve** | If a confidence score exists, publish risk vs coverage (abstain allowed). If it does not exist, say so — do not invent calibration. |
| **Solihin split** | Report class 1 / 2 / 3 separately. Class 4 (performance / proof-of-solution) is **not claimed**. Inventory: [`../evidence/solihin-rule-classes-2026-08.md`](../evidence/solihin-rule-classes-2026-08.md). |
| **AEC-Bench ≠ RT-001** | External document bench. Harbor drawing-reading false-pass is **NOT_MEASURED**. Gold-only `null_always_clean` floor is in [`../evidence/aec-bench-false-pass-2026-08.md`](../evidence/aec-bench-false-pass-2026-08.md) (task unit, not project cluster). |

Wilson intervals (§4) remain the planner for a **project-level** rate after clustering, not a substitute for the cluster bootstrap.

## 11. Reference implementation (already in this repo)

| Protocol need | Command / module |
| --- | --- |
| Extraction quality on fixtures | `python -m aerobim.tools.evaluate_extraction` |
| Detection precision + FN | `python -m aerobim.tools.evaluate_detection_precision` |
| Ablation | `python -m aerobim.tools.run_ablation_study` |
| SLA honesty (p95, pack hash, machine) | `python -m aerobim.tools.measure_package_sla` |
| Evidence bundle | `python -m aerobim.tools.export_evidence_bundle` |
| Cluster bootstrap / κ / α | `aerobim.domain.eval_statistics` · `measure_adjudicator_agreement` |
| False-pass on AEC-Bench | Harbor **NOT_RUN**; gold-only `null_always_clean` in `aec-bench-false-pass-2026-08` |

Do not publish a product accuracy number from any of these without a Samolet (or RF-expertise) corpus.
