---
title: "Red Team Re-Audit — post-ee622c8 (pass 2)"
status: active
generated_at: "2026-07-17"
author_relationship: self
head_sha: "post-ee622c8 remediation + pass-2 fixes"
claim_boundary: "Self-audit only. Checkpoint remains NO_GO."
---

# Red Team Re-Audit Pass 2 (hostile)

Follow-up to `RED_TEAM_DELTA_I0_I7_2026_07_17.md` after verifying remediations and hunting residuals.

## Checkpoint

**`NO_GO`** — RT-001 ∧ RT-002 ∧ RT-003 still open. Engineering honesty improved; product GO still forbidden.

## Prior I0–I7 findings (verification)

| ID | Status after pass 2 | Evidence |
|----|---------------------|----------|
| RT-I7-001 | **CLOSED** | `save(report)` before `get` |
| RT-SIGNOFF-001 | **CLOSED** | `calculation_match` + `dwg_dxf` in blocking set |
| RT-CALC-001 | **CLOSED** | LOAD-FORMAT → NOT_VERIFIED |
| RT-CALC-002 | **CLOSED** (this pass) | Empty / empty-loads / SCHEMA / ROW → NOT_VERIFIED; OK only after evaluated match rows |
| RT-AGENT-001 | **CLOSED** | quantity tool `skipped` without claims |
| RT-DOCS-001 | **MITIGATED** | TARGET §1/§2/§12 rebased; README.ru MEP DI wording fixed |
| RT-PATH-001 | **MITIGATED** | Agent norm evidence uses basename + `[unapproved/sample]` |
| RT-INTAKE-001 | **OPEN** | Weak evidence path acceptance |
| RT-PREC-001 | **OPEN** | Defaults / empty-class F1 / `--no-require-agreement` |
| RT-HONESTY-001 | **OPEN** | Runtime honesty assert still test-only |
| RT-SERDE-001/002 | **OPEN** | FE types + roundtrip tests |
| RT-CLI-001 | **OPEN** | Intake CLI output jail |
| RT-001/002/003 | **OPEN** | Customer / MEP delivery |

## Positive controls

DeterminismGate demotion · forbidden OK paths absent · intake gates false · capabilities `NO_GO` · Claims Lock · customer samples gitignored.

## Top remaining risks (ranked)

1. RT-001/002/003 customer evidence  
2. RT-PREC-001 / RT-INTAKE-001 process escapes  
3. RT-HONESTY-001 runtime assert  
4. Frontend honesty type drift  
5. Intake CLI path jail  

## Forbidden atoms (unchanged)

GO · >90% · MEP delivered · DWG product OK · calculation correctness · CDE-ready BCF · customer SLA proven · approved customer norm pack as fact.
