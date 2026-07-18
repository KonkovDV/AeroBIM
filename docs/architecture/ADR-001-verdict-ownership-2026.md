---
title: "ADR-001 — Contour ownership of summary.passed"
status: accepted
date: 2026-07-18
---

# ADR-001: Contour ownership of `summary.passed`

## Context

Docs historically stated that only the **DETERMINISTIC_VALIDATION** contour may set `summary.passed`.  
Runtime writes the boolean in **EVIDENCE_REPORTING** (`EvidenceAssembler`) after applying `signoff_policy` to deterministic error counts + capability matrix.

## Decision

1. **Semantic owner of the verdict** = deterministic validation outputs (engine ERROR count + blocking capabilities).
2. **Physical writer** = EvidenceAssembler (reporting contour) — pure function of deterministic inputs + policy.
3. Advisory / AI never supplies inputs that alone can flip `passed` (`DeterminismGate` + advisory ON/OFF tests).
4. Public wording: “deterministic sign-off policy applied at evidence assembly” — not “AI contour sets pass”.

## Consequences

- Keep writing `passed` in EvidenceAssembler.
- Update architecture reference language to match this ADR.
- Do not move AI outputs into signoff inputs.
