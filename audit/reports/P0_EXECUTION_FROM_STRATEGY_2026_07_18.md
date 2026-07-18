---
title: "P0 Execution Plan from Strategic Assessment"
status: active
date: 2026-07-18
checkpoint: NO_GO
source: docs/partners/AEROBIM_STRATEGIC_ASSESSMENT_2026_07.md
---

# P0 plan → execution status

Derived from strategic assessment §7 / §9. Do **not** add GraphRAG / human CV / LLM into sign-off.

| # | P0 item | Status | Evidence |
|---|---------|--------|----------|
| 1 | False-pass paths (qty/load/MEP exception) | MITIGATED (prior + hyperdeep) | `test_red_team_signoff_remediation.py` |
| 2 | Required capability profiles | MITIGATED | `capability_policy.py`, `AEROBIM_SIGNOFF_PROFILE` |
| 3 | MEP NOT_VERIFIED blocks when required | MITIGATED | `test_rt_hyperdeep_hardening.py` |
| 4 | Audit JSONL integrity / fail-closed | MITIGATED | review event store + tests |
| 5 | Report commit marker / orphan record | MITIGATED (minimal) | FilesystemAuditStore |
| 6 | Upload magic-bytes + size for all types | MITIGATED | `upload_content.py`, upload API, tests |
| 7 | Cross-tenant API ACL gaps (review/KPI/BCF push/list) | MITIGATED | api.py + `test_api_object_acl.py` |
| 8 | HITL bbox + IoU honesty + deterministic events | MITIGATED | `drawing_region_hitl.py` |
| 9 | Full outbox/transaction + concurrent locks | PARTIAL — commit/orphan marker done; locks/cleanup CLI residual |
| 10 | Full advisory ON/OFF E2E beyond fixture | PARTIAL — DeterminismGate + UC injection tests added |
| 11 | Schema round-trip golden suite | MITIGATED — report provenance round-trip + schema_version |
| 12 | Quarantine / zip-bomb / per-tenant quotas | MITIGATED — quarantine, zip limits, daily tenant quotas |
| 13 | HITL lifecycle state machine | MITIGATED — `review_state_machine.py` + API previous_state |
| 14 | Orphan reconcile CLI | MITIGATED — `python -m aerobim.tools.reconcile_audit_orphans` |

## Positioning (canonical)

> Open-source openBIM validation kernel and expert review assistant for IFC, IDS and cross-document evidence.

Not: autonomous >90% / DWG / MEP / CDE-ready AI checker.

## Next slice after this P0 batch

```text
IFC + IDS + PDF + one cross-doc scenario
→ deterministic → provenance → HITL → BCF 2.1 → expert check
```

on **customer-agreed** corpus (closes engineering path toward RT-001 evidence; does not auto-close RT-001).

## Constraints

- PR #10 / #11 untouched
- No history rewrite / force-push / destructive git
- Checkpoint remains NO_GO
