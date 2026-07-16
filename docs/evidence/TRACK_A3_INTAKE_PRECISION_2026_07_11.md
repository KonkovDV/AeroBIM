---
title: "Track A3 — Intake precision & adjudication readiness"
status: complete-engineering
delivered_at: "2026-07-11"
tags: [aerobim, p1, precision, intake, track-a]
---

# Track A3 — Intake precision & adjudication readiness (2026-07-11)

Goal: when the Samolet corpus arrives, the team runs precision + SLA **in a day**
instead of writing infrastructure. No customer labels are filled (no corpus yet);
`customer_confirmed` stays `0`.

## Было / стало

| Item | До A3 | После A3 |
|---|---|---|
| Adjudication worksheet | нет (только KPI weekly rollup) | finding-level 2-adjudicator CSV template linked to harness identity |
| Labels авторинг | вручную писать `labels.json` | thin compiler `aerobim-build-detection-labels` (CSV → schema-valid labels.json) |
| Consensus reconciliation | вручную | авто: agree-real→confirmed, agree-FP→excluded, disagree→unresolved |
| Publishable safety | только в evaluator | compiler **fail-closed** для `adjudicated` (≥2 adjudicators, 0 unresolved, scope, tz completed_at) |
| «Когда приедет корпус» | protocol doc (шаги вручную) | пошаговый ops runbook с точными командами (analyze→adjudicate→precision→SLA→redacted KPI) |
| Labels skeleton | нет | `labels-template.json` |

## Deliverables

1. **Adjudication templates** —
   `samples/benchmarks/detection-precision/adjudication-template.csv` (CSV,
   per-adjudicator: finding_id, case_id, finding_class, rule_id, target_ref/
   element_guid/match_key, adjudicator_id, verdict TP/FP/FN, notes, timestamp) +
   `labels-template.json` (blank harness skeleton).
2. **Runbook** — `docs/ops/intake-precision-runbook-2026.md` (NDA/storage → freeze
   → manifest/env pack → analyze → export detections → adjudicate → compile labels
   → evaluate → SLA → redacted KPI → go/no-go).
3. **Thin wrapper** — `aerobim.tools.build_detection_labels` (console script
   `aerobim-build-detection-labels`): reconciles the 2-adjudicator CSV into
   `labels.json` in the exact harness schema. No accuracy thresholds baked;
   thresholds stay in `evaluate_detection_precision` and gate **only** synthetic
   fixtures in CI.
4. Evidence: this note.
5. Claim-boundary / readiness synced; `customer_confirmed = 0` unchanged.

## Verification

- New `test_build_detection_labels.py` (11 tests): template compile, schema
  conformance, verdict reconciliation matrix, same-adjudicator conflict rejection,
  fail-closed adjudicated preconditions (2 adjudicators / unresolved / scope /
  tz-completed_at), malformed CSV (missing column / bad verdict / no ref), and an
  end-to-end test that compiled `adjudicated` labels pass the evaluator's
  `--require-publishable` gate (TP=1).
- Compiler output validated against `labels.schema.json` (no drift with the
  A2-style CI schema gate).
- Full backend suite green (see delivery report); A1 section pairing + A2 norm
  packs untouched.

## Claim boundary (unchanged)

Delivered: templates + thin compiler + runbook + tests. NOT delivered / NOT
claimed: any customer precision number, filled customer labels, published >90%.
The compiler cannot mint `adjudicated` labels without the two-adjudicator
preconditions, mirroring the evaluator's publishable gate.

## Customer blockers still open

1. Adjudicated customer corpus (2 independent adjudicators, 0 unresolved).
2. Baseline manual review hours for the −20% review-time KPI.
3. Signed scope memo + approved pack (shared with A2).
