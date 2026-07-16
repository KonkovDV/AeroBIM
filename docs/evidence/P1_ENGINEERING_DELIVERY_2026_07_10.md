---
title: P1 engineering delivery
status: complete-engineering
delivered_at: "2026-07-10"
---

# P1 engineering delivery — 2026-07-10

## Closed engineering scope

| P1 item | Status | Evidence |
|---|---|---|
| Norm / rule packs | Engineering done | `JsonNormRulePackLoader`, 20-rule residential AR synthetic template, schema, docs |
| PD↔RD section pairing | Scaffold done | `JsonSectionDiffAnalyzer`, AR fixtures, SI tolerance, provenance |
| Detection precision harness | Done | `evaluate_detection_precision`, synthetic contract, CI smoke, adjudication protocol |
| Typical-errors ≥20 | Scaffold done | catalog 20 patterns + mapping tool; customer_confirmed=0 |
| MEP system clash | Honest gap | `MEP-CLASH-001` + matrix `missing` |
| Docs / claim-boundary sync | Done | TZ matrix, claim-boundary, readiness, architecture, README |

## Customer blockers remaining

1. Approved residential pack (not `synthetic-template`).
2. Real PD↔RD pair + canonical keys.
3. Adjudicated customer corpus for publishable precision.
4. Federated MEP IFC + system rules for MEP-CLASH-001.

## Verification

- Focused P1 tests: loader / section / integration / precision / mapping.
- Full backend `pytest` after delivery.
- Synthetic precision contract: `4 TP / 2 FP / 2 FN` (harness only).
- Layer boundaries: no Domain/Application → Infrastructure imports.

## Claim boundary

May claim: harness, loaders, scaffolds, capabilities honesty.  
Must not claim: customer accuracy >90%, full SP/GOST, Solibri replacement, synthetic scores as product quality.
