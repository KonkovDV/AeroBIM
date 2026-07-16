---
title: "AeroBIM Execution Plan I6 — Customer Metrics Readiness"
status: active
version: "1.0.0"
last_updated: "2026-07-17"
tags: [aerobim, roadmap, i6, precision, sla, intake]
claim_boundary: "Engineering readiness only. Checkpoint remains NO_GO until RT-001/002/003 with real customer evidence."
---

# Execution Plan — I6 (Customer metrics readiness)

Parent: [`TARGET_HYBRID_ARCHITECTURE_TZ_2026.md`](TARGET_HYBRID_ARCHITECTURE_TZ_2026.md) · Prior waves: [`EXECUTION_PLAN_I0_I2_2026_07.md`](EXECUTION_PLAN_I0_I2_2026_07.md)

## Objective

Make the **publishable PrecisionClaim path operationally complete** without flipping any intake gate or claiming GO / >90% / customer SLA.

## Success criteria

| ID | Criterion | Evidence |
|----|-----------|----------|
| S1 | Krippendorff α (nominal) implemented + tested; κ retained | `measure_adjudicator_agreement` schema 1.1.0 |
| S2 | `validate_customer_intake_gate` fails if gates true without evidence; default all-false passes | CLI + pytest |
| S3 | `evaluate_detection_precision` can require `--agreement-json`; publishable ∧ agreement thresholds | pytest |
| S4 | `samples/customer/` gitignored + README placeholder | `.gitignore` |
| S5 | Capabilities API surfaces intake gate snapshot (BLOCKED) | GET `/v1/system/capabilities` |
| S6 | Console scripts for κ/α + intake gate; SLA customer wording unchanged | `pyproject.toml` |
| S7 | Checkpoint / Claims Lock remain **NO_GO** | docs spot-check |

## Work breakdown

- [x] Plan doc (this file)
- [x] I6a — κ/α + intake gate validator
- [x] I6b — PrecisionClaim ↔ agreement wiring
- [x] I6c — path hygiene + capabilities + scripts
- [x] I6d — tests, runbook polish, commit

## Explicit non-goals

- Flipping any `customer-intake-gate.json` gate to `true`
- Minting customer adjudicated corpus without data
- Claiming GO, product accuracy >90%, or customer SLA pass
- Treating fixture SLA as customer SLA

## Verification

```bash
cd backend
python -m pytest tests/test_measure_adjudicator_agreement.py tests/test_i6_precision_intake.py tests/test_evaluate_detection_precision.py tests/test_architecture_seams.py -q
ruff check src/aerobim/tools/measure_adjudicator_agreement.py src/aerobim/tools/validate_customer_intake_gate.py src/aerobim/tools/evaluate_detection_precision.py
```
