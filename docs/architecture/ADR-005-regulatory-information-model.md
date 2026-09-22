# ADR-005: Regulatory Information Model

**Status:** Accepted  
**Date:** 2026-09-22  
**Deciders:** AeroBIM Principal Engineering  
**Replaces:** Informal norm-pack JSON without interpretation chain

---

## Context

AeroBIM's P0 norm packs contained flat rule definitions with a `norm_ref`
string but no formal traceability between:
- the normative document clause,
- the human interpretation of that clause,
- the automated rule that implements it,
- the review and approval status.

This created a verification gap:
> *Why does AeroBIM evaluate this rule? Who approved this interpretation?
What exact clause does it implement?*

Modern ACC research (BRISE-Vienna 2026, ePlanCheck, Euclid project) shows
that regulatory traceability is part of the compliance pipeline itself,
not separate documentation.

ISO 19650 and buildingSMART IDS 1.0 both assume that information requirements
have a traceable normative basis. AeroBIM needed to align.

---

## Decision

Implement a **Regulatory Information Model** as a first-class domain module
(`backend/src/aerobim/domain/regulation_model.py`) with the following chain:

```
norm_pack → norm_document → clause → interpretation
  → requirement → rule → execution → evidence → result
```

Key design decisions:

### 1. Interpretation as explicit artefact

`RuleInterpretation` is a named, versioned, reviewable artefact.
It carries four independent review statuses:
- `interpretation_status` — technical correctness of the mapping
- `legal_review_status` — legal team sign-off
- `technical_review_status` — domain expert sign-off
- `approval_status` — final publication gate

A rule cannot enter production unless **all four** are `APPROVED`.
This prevents "rules from nowhere".

### 2. Immutable rule versions

`ComplianceRule.stable_version` is immutable after `approval_status=APPROVED`.
Any change to rule content, logic, parameters, or severity creates a **new
version**. The old version remains in the record to maintain
reproducibility of past results.

`rule_hash` is computed from content fields. A change in hash = a change
in version. This is enforced at the application layer.

### 3. Immutable norm packs

`NormPack.finalise()` seals `pack_hash` over all rule hashes.
Once sealed:
- The pack cannot be modified.
- Each execution record stores `pack_hash + rule_hash + engine_version +
  configuration_hash + result_hash`.
- Old results **never** adopt the semantics of a new norm pack version.

### 4. Evidence requirements on every rule

Each rule declares `evidence_requirements: list[EvidenceRequirement]`
specifying what must be found to evaluate the rule.

**If required evidence is absent: result is `NOT_VERIFIED`, not `PASS`.**

This enforces `unknown != pass` at the rule definition level.

### 5. ExecutionMode separates AI from deterministic

```python
class ExecutionMode(str, Enum):
    DETERMINISTIC = "deterministic"  # Must pass DeterminismGate
    ADVISORY = "advisory"            # AI contribution; human must confirm
    SKIPPED = "skipped"              # Not applicable
```

AI cannot change a `DETERMINISTIC` rule's result.
The `DeterministicVerdict(AI_ON) == DeterministicVerdict(AI_OFF)` invariant
is testable and tested (see `test_p0_p1_upgrade.py::TestDeterminismInvariant`).

### 6. BRISE-Vienna parallel

The model is structurally aligned with the BRISE-Vienna 2026
Regulation Information Matrix:
```
legal interpretation → implementation → testing → validation → acceptance
```

This enables future interoperability with European ACC toolchains.

---

## Consequences

### Positive
- Every finding has a traceable normative basis.
- Unapproved interpretations cannot reach production.
- Past results are reproducible by content hash.
- `unknown != pass` is enforced structurally, not just by convention.
- Enables meaningful benchmark tracking: rule version is explicit.

### Negative / mitigations
- Existing norm packs must be migrated to the new schema.
  Mitigation: migration script in `tools/migrate_norm_packs.py` (P1-B task).
- Review workflow requires domain expert time.
  Mitigation: pending interpretations are `PENDING`, not `REJECTED`;
  system degrades gracefully (fewer production rules, not broken rules).

### Neutral
- Does not introduce new runtime dependencies.
- Does not change IFC or IDS parsing.
- Does not affect existing BCF export.

---

## Alternatives considered

| Alternative | Rejected because |
|---|---|
| Keep flat JSON norm packs | No traceability; "rules from nowhere" risk |
| Full OWL ontology | Over-engineered for current scale; adds runtime dependency |
| External regulation DB (3rd party) | Vendor dependency; no Russian norm coverage |
| Store interpretation as free text in README | Not machine-readable; not versionable |

---

## References

- BRISE-Vienna 2026: Regulation Information Matrix methodology
- buildingSMART IDS 1.0: Information Delivery Specification
- NIST AI RMF 1.0: AI Risk Management Framework
- ISO/IEC 42001:2023: AI Management Systems
- `backend/src/aerobim/domain/regulation_model.py`
- `backend/tests/test_p0_p1_upgrade.py::TestRegulationModel`
