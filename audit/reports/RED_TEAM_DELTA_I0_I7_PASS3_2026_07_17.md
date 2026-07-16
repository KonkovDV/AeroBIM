---
title: "Red Team Pass 3 — post-dbc41bf"
status: active
generated_at: "2026-07-17"
author_relationship: self
claim_boundary: "Self-audit only. Checkpoint remains NO_GO."
---

# Red Team Pass 3

Hostile re-audit after PASS2 (`dbc41bf`). Prior CRITICAL remediations **not regressed**.

## Checkpoint

**`NO_GO`** — RT-001 ∧ RT-002 ∧ RT-003 remain open.

## Regression (prior closed)

| ID | Status |
|----|--------|
| RT-I7-001 / RT-SIGNOFF-001 / RT-CALC-001/002 / RT-AGENT-001 / RT-PATH-001 | **HOLD** |

## New findings this pass → remediated

| ID | Sev | Action |
|----|-----|--------|
| RT-SIGNOFF-002 | HIGH | `calculation_match=NOT_VERIFIED` now blocks `summary.passed` |
| RT-CALC-006 | HIGH | Tabular LOAD regex did not parse `expected\|unit\|observed` — rows never matched (FORMAT greenwash). **Fixed.** |
| RT-FE-001 | HIGH | Frontend `CapabilityState` + honesty/I7 report fields expanded |
| RT-PATH-002/003 | MEDIUM | CAD `source_id` basename; capabilities gate `source` repo-relative |
| RT-DOCS-002 | MEDIUM | Banner supersession on DELTA 8efbef8 + TZ matrix for MEP DI |

## Still open

RT-001/002/003 · RT-INTAKE-001 · RT-PREC-001 · RT-HONESTY-001 · RT-CLI-001 · RT-SERDE roundtrip tests · RT-CALC-004/005 (JSON non-dict skip / text shadows path)

## Positive controls

DeterminismGate · forbidden OK paths · intake all-false · Claims Lock · customer samples gitignored.
