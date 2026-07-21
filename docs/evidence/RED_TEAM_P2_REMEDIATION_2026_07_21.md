# Red Team Remediation Evidence — P2/P2b (2026-07-21)

**Checkpoint after remediation:** still `NO_GO` (RT-001 / RT-002 / RT-003).  
**Scope:** hostile audit of P2/P2b engineering surfaces + executed fixes.

## Findings closed

| ID | Severity | Fix landed |
|---|---|---|
| RT-P2-001 | CRITICAL | `resolve_repo_relative_path` on federated IFC, matrix, bootstrap scope |
| RT-P2-002 | CRITICAL | Co-presence ≠ geometry; demote forbidden → WARNING |
| RT-P2-003 | HIGH | Template/synthetic → `AEROBIM-MEP-TEMPLATE` WARNING |
| RT-P2-004 | HIGH | BCF Comment + claim_boundary; Clash only for real ERROR |
| RT-P2-005 | HIGH | `VERIFIED` requires memo + expert_signoff; fixture=`ENG_FIXTURE` |
| RT-P2-006 | HIGH | `validate_invocation` before every agent handler |
| RT-P2-007 | HIGH | `ifc_guid=None`; `claimed_guid:` only |
| RT-P2-008 | HIGH | Missing matrix on ENG/VERIFIED → ERROR + FAILED |
| RT-P2-009 | MEDIUM | eng_fixture → `graph.synthetic=True` |
| RT-P2-010 | MEDIUM | audit reconstruct `authoritative` default **False** |
| RT-P2-011 | MEDIUM | Inverted BCF/matrix/annotation asserts |
| RT-P2-012 | MEDIUM | Backlog relabeled ENG_PARTIAL / ENG_DONE |

## Proof

- pytest: **795 passed**, 5 skipped (post-remediation run)
- ruff on remediations: PASS
- Negative tests: path jail absolute/`..`; template BCF ≠ Clash; annotation no invented guid

## Still open (customer)

RT-001 corpus, RT-002 signed norm pack, RT-003 customer federated IFC + geometry + signed matrix, customer SLA pack.
