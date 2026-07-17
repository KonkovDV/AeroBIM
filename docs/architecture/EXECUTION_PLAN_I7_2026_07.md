---
title: "AeroBIM Execution Plan I7 — Post-I6 polish"
status: active
version: "1.0.0"
last_updated: "2026-07-17"
tags: [aerobim, roadmap, i7, polish]
claim_boundary: "Engineering polish only. Checkpoint remains NO_GO. No customer corpus, no GO claims."
---

# Execution Plan — I7 (Post-I6 polish)

Parent: [`TARGET_HYBRID_ARCHITECTURE_TZ_2026.md`](TARGET_HYBRID_ARCHITECTURE_TZ_2026.md) · Prior: I0–I6 · Next: [`EXECUTION_PLAN_I8_I9_2026_07.md`](EXECUTION_PLAN_I8_I9_2026_07.md)

## Objective

Close residual seams that discard useful advisory/audit artifacts without flipping honesty or intake gates.

## Work breakdown

- [x] I7a — Persist DeterminismGate `DivergenceRecord`s on ValidationReport
- [x] I7b — Keep advisory IDS draft on analyze report (+ promote path if thin)
- [x] I7c — Plumb `DrawingRegionRef` into report for UI highlight
- [x] I7d — Expand ComplianceAgent allowlist (quantities + clashes)
- [x] I7e — Track `@sota-stub` IdsAssist in KNOWN_BUGS + refresh TARGET §12

## Explicit non-goals

- Customer corpus / flipping intake gates
- Real VLM / ODA DWG / LLM sign-off
- Claiming GO or product accuracy

## Verification

```bash
cd backend
python -m pytest tests/test_determinism_gate.py tests/test_compliance_agent.py tests/test_ids_norm_assist.py tests/test_architecture_seams.py -q
```
