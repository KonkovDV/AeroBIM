---
title: "ADR-001 — Contour ownership of summary.passed"
status: accepted
date: 2026-07-18
last_updated: "2026-08-13"
---

# ADR-001: Contour ownership of `summary.passed`

## Context

Docs historically stated that only the **DETERMINISTIC_VALIDATION** contour may set `summary.passed`.  
Runtime writes the boolean in **EVIDENCE_REPORTING** (`EvidenceAssembler`) after applying `signoff_policy` / `capability_policy` to deterministic error counts + capability matrix.

Jury-facing language must not say “no automatic verdict” without this distinction — there **is** an automatic technical status.

## Decision

1. **Semantic owner of the verdict** = deterministic validation outputs (engine ERROR count + blocking capabilities under the active sign-off profile).
2. **Physical writer** = EvidenceAssembler (reporting contour) — pure function of deterministic inputs + policy. Package-level `summary.outcome` uses this precedence (violation > missing data > uncertainty > compliance), matching Mushkani et al., [arXiv:2607.29058](https://arxiv.org/abs/2607.29058):
   1. confirmed finding failures / hard clashes → `FAILED`
   2. intake blocked or required capability not OK → `BLOCKED`
   3. HITL / missing source / low confidence → `REVIEW_REQUIRED`
   4. warnings only → `PASS_WITH_WARNINGS`
   5. else `PASS`  
   `REVIEW_REQUIRED` never rewrites a violation into a pass. Incomplete evidence never becomes `PASS`. `summary.passed` is true only for `PASS` and `PASS_WITH_WARNINGS`.
3. Advisory / AI / OCR never supplies inputs that alone can flip `passed` (`DeterminismGate` + advisory ON/OFF tests).
4. **ISO 19650 framing:** `summary.passed` is a **Shared-gate** technical pass under configured rules — **not** authorization to move Shared → Published and **not** contractual fitness for construction.
5. Human-in-the-loop confirms/rejects **findings** for handoff; HITL review events do not redefine the Shared-gate boolean by themselves.
6. Public wording: “deterministic Shared-gate applied at evidence assembly” — not “AI contour sets pass” and not “no automatic status”.

## Consequences

- Keep writing `passed` in EvidenceAssembler.
- Pilot/production sign-off profiles fail-closed on required clash / MEP / unit_scale / calc-qty SKIPPED.
- Jury memo (`docs/docs.md`) and Claims Lock must stay aligned with this ADR.
- Do not move AI outputs into signoff inputs.
