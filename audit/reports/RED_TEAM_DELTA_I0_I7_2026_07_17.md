---
title: "Red Team Delta — I0–I7 Architecture Wave Re-Audit"
status: active
generated_at: "2026-07-17"
author_relationship: self
scope_sha_range: "c8f9fd6..HEAD"
claim_boundary: "Self-audit only. Checkpoint remains NO_GO. Does not supersede CLAIMS_LOCK."
---

# Red Team Delta — I0–I7 (2026-07-17)

Hostile re-verification of architecture waves I0–I7 (~4.3k LOC delta) against Claims Lock, industry AECO QA honesty norms, and Clean Architecture seams.

**Does not supersede** `RED_TEAM_FULL_REPORT.md` / prior `RED_TEAM_DELTA_2026_07_17.md`.  
**Operational SSOT:** `CLAIMS_LOCK_2026_07_17.md` + this delta for I0–I7-specific IDs.

## Measurement freeze

| Probe | Result |
|-------|--------|
| Scope | `c8f9fd6..HEAD` (I0–I7 + CI follow-ups) |
| Customer corpus | **false** (`customer-intake-gate.json` all gates false) |
| Author relationship | **self** |
| Checkpoint | **`NO_GO`** |

## Checkpoint verdict

**`NO_GO`**

Rationale: RT-001 ∧ RT-002 ∧ RT-003 remain open (customer / MEP delivery). I0–I7 improve *engineering honesty surfaces* and close several false-pass vectors, but they do **not** convert the checkpoint to GO. Vocabulary “readiness” ≠ product GO.

## Findings opened / closed this wave

| ID | Sev | Status | Summary |
|----|-----|--------|---------|
| RT-I7-001 | CRITICAL | **CLOSED** (this remediation) | Analyze accidentally dropped `audit_report_store.save()` under “persist” commit — restored |
| RT-SIGNOFF-001 | CRITICAL | **CLOSED** (this remediation) | `calculation_match` + `dwg_dxf` FAILED now block `summary.passed` |
| RT-CALC-001 | HIGH | **CLOSED** (this remediation) | Empty LOAD parse no longer yields `calculation_match=OK` → `NOT_VERIFIED` |
| RT-DOCS-001 | HIGH | **MITIGATED** | TARGET §2/§12 rebased to as-built I0–I7; keep NO_GO |
| RT-INTAKE-001 | HIGH | **OPEN** | Gate validator accepts weak evidence paths once status ≠ BLOCKED |
| RT-PREC-001 | HIGH | **OPEN** (process) | Defaults `require_publishable=False`; empty-class F1=1.0; `--no-require-agreement` escape |
| RT-AGENT-001 | MEDIUM | **MITIGATED** | Quantity tool now `skipped` without claims (was false `ok`) |
| RT-HONESTY-001 | MEDIUM | **OPEN** | Runtime analyze does not call honesty assert (tests only) |
| RT-SERDE-001 | MEDIUM | **OPEN** | Frontend types omit I7 report fields |
| RT-CLI-001 | MEDIUM | **OPEN** | Intake CLI output path not storage-jailed |
| RT-NORM-001 | MEDIUM | **OPEN** (messaging) | Sample corpus hits can be misread as approved norms |

## Positive controls (verified)

1. DeterminismGate demotes advisory ERROR→INFO; cannot alone flip pass via ERROR count.
2. Forbidden capabilities (`dwg_dxf`, `cv_human_level`, `mep_system_clash`, `calculation_correctness`) have no analyze path to OK.
3. Intake gates all false; capabilities API hardcodes checkpoint `NO_GO`.
4. PrecisionClaim base gate: customer + ≥2 adjudicators; agreement required when publishable enforced.
5. IDS compiler / agent drafts marked advisory; Claims Lock / EXECUTION plans refuse GO / >90%.
6. `samples/customer/**` gitignored; `@sota-stub` IdsAssist tracked in `KNOWN_BUGS.md`.

## Forbidden claim atoms (unchanged)

GO · CDE-ready BCF · customer SLA proven · product accuracy >90% · MEP delivered · calculation *correctness* · DWG as product OK · `cv_human_level` delivered · customer-approved norm pack as fact.

## Follow-ups

1. Typed intake evidence digests (RT-INTAKE-001).
2. CI always `--require-publishable` for customer packs (RT-PREC-001).
3. Frontend types for `divergences` / `drawing_regions` / `advisory_ids_draft`.
4. Call `assert_honesty_capabilities_not_silently_ok` on analyze/save.
5. Customer RT-001/002/003 when data arrives — only then reopen GO discussion.
