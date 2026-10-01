<!-- claims-lint: allow-file reason="VLM confidence is an uncalibrated abstention threshold; not product accuracy; NO_GO" -->
---
title: "VLM confidence — tuning protocol, not a calibrated score"
status: active
version: "1.0.0"
last_updated: "2026-09-02"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Default thresholds are abstention knobs on fixture VLM reads.
  Not product accuracy. Not the MIK interim TP/(TP+FP) ≥ 0.60.
  Not a published calibration. Checkpoint GO; customer_go false.
---

# VLM confidence — tuning protocol

Re-Audit #8 observation: verbalized VLM confidence is **uncalibrated**.
The numbers below are **abstention floors**, not measured precision.

This is **not** the quality-protocol interim 0.60 (TP/(TP+FP) on adjudicated
findings). Same numeral, different contract.

## Defaults in code (02.09.2026)

| Knob | Value | Where |
|---|---|---|
| Drawing-read min confidence | **0.60** | `vlm_grounding._DEFAULT_MIN_CONFIDENCE` |
| Layout-detector HITL floor | **0.45** | `heuristic_layout_region_detector._HITL_CONFIDENCE` |
| Region-observation HITL | below min **or** `confidence_calibrated=False` | `ground_vlm_region_observations` |

Uncalibrated path: every region-observation is `hitl_required` unless a caller
explicitly sets `confidence_calibrated=True`. High self-reported confidence
must not silently clear expert review.

Schema deviation on `ground_vlm_drawing_response`: **whole response**
`parse_ok=False` (siblings discarded). Invalid observations on
`ground_vlm_region_observations`: drop that observation, keep the rest.

## AB on fixture (not RT-001)

1. Fix prompt, crop policy (stamp/PII clip), schema, model id, `normalizer_version`.
2. Run the same open fixture at two floors (e.g. 0.45 vs 0.60).
3. Record: `hitl_count`, `parse_ok`, schema-fail share, expert time on HITL
   regions. `t_manual_s` stays empty until a rater logs it.
4. Do not publish the floor as product accuracy. `claim_level=fixture_only`.

Existing stamp comparison remains `comparison_not_run`:
[`vlm-comparison-2026-08.md`](vlm-comparison-2026-08.md).
