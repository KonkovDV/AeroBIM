# Sprint 2 — detection metrics method

**Date:** 2026-08-04  
**claim_level:** `synthetic_only` for this baseline · **closes_rt001:** `false`  
**Checkpoint:** NO_GO

## Definitions

| Quantity | Definition |
|---|---|
| TP | System finding matches a planted (or adjudicated) error in the ground-truth set |
| FN | Ground-truth error with no matching system finding |
| FP | System finding with no matching ground-truth error |
| Recall | TP / (TP + FN) |
| Precision | TP / (TP + FP) |
| Time | Wall-clock from package load start to report ready |

## Match rule

A system finding matches a ground-truth item when **both** hold:

1. **Class / rule identity:** `finding_class` compatible **and** `match_key` equals expected `rule_id` / `match_key` (exact string).  
2. **Locus:** `element_guid` exact match when both sides have a GUID; otherwise `locus` / `target_ref` / case_id exact match.

**Tolerance justification:** Synthetic Level-B cases are deterministic single-locus injections. Fuzzy geometric IoU is not used — it would invent agreement on fixtures that have no spatial GT. When customer bbox labels exist, tolerance must be re-specified with units (mm / IoU) and signed off.

Implementation: [`FindingKey`](../../backend/src/aerobim/tools/evaluate_detection_precision.py) (`case_id` + `finding_class` + `match_key`). Sprint 2 synthetic runner uses `defect_id` as `case_id` and Level-B `match_key` as above.

## FP semantics (do not conflate)

| Corpus | Meaning of FP |
|---|---|
| **Synthetic** (this sprint) | False positive — ground truth is complete **by construction** for planted detectable defects |
| **Real customer** | May be true defect missed by the expert register — **not** published as system error without customer adjudication |

## Confidence intervals

Report Wilson score interval (α=0.05) via [`wilson_interval`](../../backend/src/aerobim/domain/study_design.py). Publish the **lower bound** alongside the point estimate.

If `n` is below the planner target for half-width ≤0.08 ([`plan_adjudication_corpus.py`](../../backend/src/aerobim/tools/plan_adjudication_corpus.py)), state that explicitly — do not widen definitions to hide small-n.

## Time metric

Publish **p95** wall-clock (same gate as SLA fixture), not the mean. Measure AI overlay **on** and **off** separately when both runs exist.

## Forbidden claims

- Threshold «90%» from TZ — **not confirmed**  
- Synthetic recall/precision as product accuracy or RT-001 close  
- AECV open-bench 0.43 as product accuracy  
