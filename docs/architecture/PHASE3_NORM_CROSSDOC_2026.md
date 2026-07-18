---
title: "Norm pack lifecycle and unresolved cross-doc alignment (Phase 3)"
status: active
date: 2026-07-18
---

# Phase 3 — NormPack + cross-document honesty

## NormPack activation (already fail-closed + defense-in-depth)

| Gate | Behavior |
|------|----------|
| `JsonNormRulePackLoader` | `customer_approved`/`approved` require full `approval` + `scope_reference` |
| Schema `norm-rule-pack.schema.json` | same |
| `ApplyNormRuleHitlEventUseCase` | rejects empty `approval_ref` for customer_approved |
| `ObjectStoreNormRulePackVersionStore.save_version` | **NEW** rejects `customer_approved`/`approved` without `approval_ref` |

Synthetic/draft packs remain loadable as advisory — never claim customer approval without `approval_ref`.

## Cross-document unresolved → HITL (no silent agreement)

| Case | Behavior |
|------|----------|
| Same entity+property, **divergent Psets** across sources | `CROSS-DOC-AMBIGUOUS-*` **ERROR** + `AMBIGUOUS_MAPPING` |
| Non-numeric string value conflicts (same key) | `AMBIGUOUS_MAPPING` (not fake SI hard conflict) |
| PD/RD section key outside canonical registry | `SECTION-PAIR-…-UNRECOGNIZED-…` **ERROR** + HITL text |
| Any unrecognized PD keys in pairing | `section_pairing` capability **FAILED** |

Deterministic SI/ε equivalence and registered RU/EN aliases remain agreement paths.

## Verification

```bash
cd backend
pytest tests/test_cross_document_detection.py \
       tests/test_section_diff_analyzer.py \
       tests/test_apply_norm_rule_hitl_event.py \
       tests/test_p1_norm_section_integration.py -q
```

Checkpoint remains **NO_GO** until RT-001/002/003 customer evidence.
