---
title: "RT Hyperdeep Residual Slice — 2026-07-18"
checkpoint: NO_GO
baseline_tests: "572 passed, 4 skipped"
---

# Residual P0 slice (continued)

Closed in this continuation after strategic P0 batch:

| ID | Item | Status |
|----|------|--------|
| RT-HYPER-008 | ZIP bomb / member limits on upload | **MITIGATED** |
| RT-HYPER-009 | Quarantine-before-promote upload path | **MITIGATED** |
| RT-HYPER-010 | Report `schema_version` + provenance round-trip | **MITIGATED** |
| RT-HYPER-011 | HITL state machine (waived/superseded + actor rules) | **MITIGATED** |
| RT-HYPER-012 | Advisory ERROR cannot flip/clear deterministic pass | **MITIGATED** (gate + UC) |

## New / updated files

- `backend/src/aerobim/core/security/zip_limits.py`
- `backend/src/aerobim/domain/review_state_machine.py`
- `backend/tests/test_rt_hyperdeep_residuals.py`
- Upload API: quarantine → validate → zip inspect → promote
- `ValidationReport.schema_version`
- API `ReviewEventRequest.previous_state` + transition checks

## Still residual (next)

1. Full outbox / concurrent save locks  
2. Golden BCF/HTML export round-trip fixtures (beyond report JSON)  
3. Broader advisory ON/OFF across full demo path matrix  
4. Job lease/heartbeat after crash  
5. Customer corpus pilot slice (external RT-001/002/003)

## Latest continuation

- Quotas: `FilesystemUploadQuotaStore` + `429` on exceed  
- Orphans: `aerobim.tools.reconcile_audit_orphans` dry-run/`--apply`  
- Gates: **575 passed, 4 skipped**

## Constraints

- PR #10 / #11 untouched  
- No destructive git  
- Checkpoint **NO_GO** preserved  
- RT-001/002/003 remain EXTERNAL BLOCKER  
