---
title: "ADR-001 — Contour ownership of summary.passed"
status: accepted
date: 2026-07-18
last_updated: "2026-07-19"
---

# ADR-001: Contour ownership of `summary.passed`

## Context

Docs historically stated that only the **DETERMINISTIC_VALIDATION** contour may set `summary.passed`.  
Runtime writes the boolean in **EVIDENCE_REPORTING** (`EvidenceAssembler`) after applying `signoff_policy` / `capability_policy` to deterministic error counts + capability matrix.

Jury-facing language must not say “no automatic verdict” without this distinction — there **is** an automatic technical status.

## Decision

1. **Semantic owner of the verdict** = deterministic validation outputs (engine ERROR count + blocking capabilities under the active sign-off profile).
2. **Physical writer** = EvidenceAssembler (reporting contour) — pure function of deterministic inputs + policy.
3. Advisory / AI / OCR never supplies inputs that alone can flip `passed` (`DeterminismGate` + advisory ON/OFF tests).
4. **ISO 19650 framing:** `summary.passed` is a **Shared-gate** technical pass under configured rules — **not** authorization to move Shared → Published and **not** contractual fitness for construction.
5. Human-in-the-loop confirms/rejects **findings** for handoff; HITL review events do not redefine the Shared-gate boolean by themselves.
6. Public wording: “deterministic Shared-gate applied at evidence assembly” — not “AI contour sets pass” and not “no automatic status”.

## Consequences

- Keep writing `passed` in EvidenceAssembler.
- Pilot/production sign-off profiles fail-closed on required clash / MEP / unit_scale / calc-qty SKIPPED.
- Jury memo (`docs/docs.md`) and Claims Lock must stay aligned with this ADR.
- Do not move AI outputs into signoff inputs.
