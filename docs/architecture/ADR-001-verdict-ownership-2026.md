<!-- claims-lint: allow-file reason="ADR-001 verdict ownership; Iversen/Fuchs contrast as non-claim; NO_GO" -->
---
title: "ADR-001 — Contour ownership of summary.passed"
status: accepted
date: 2026-07-18
last_updated: "2026-09-02"
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

## Product split vs 2026 ACC literature

Iversen & Huang (AuC 182, 2026) put the LLM on the check route: interpret a clause, select a tool, execute, report. Fuchs, Hellin & Borrmann (EC3, 2026) generate reusable checking functions from IDS-validated requirements and run them. Those papers close **encoding a clause into an executable check**. They do not close **who is allowed to say pass**.

AeroBIM’s product choice for Samolet / expertise is the opposite of that route:

1. **Drafts yes.** The model may compose a remark, an IDS fragment, or a candidate function.
2. **Shared-gate no.** `call_tool` and `change_verdict` are forbidden provider actions. Generated checkers do not enter sign-off until a human-approved hashed pack with `approval_ref`.
3. **Hybrid, not “more accurate”.** Do not say «мы лучше Iversen». Their F1 stays theirs. Jury line: they close digitising a norm with a model; we close who may emit `summary.passed`.

Runtime pins: `FORBIDDEN_LLM_ACTIONS`, `LLM_SELECTS_CHECK_ON_VERDICT_PATH=False`, `LLM_GENERATED_FUNCTION_WRITES_SUMMARY_PASSED=False`, `DeterminismGate`, `IdsAssistDraftPort` unwired from Analyze.

## Consequences

- Keep writing `passed` in EvidenceAssembler.
- Pilot/production sign-off profiles fail-closed on required clash / MEP / unit_scale / calc-qty SKIPPED.
- Jury memo (`docs/docs.md`) and Claims Lock must stay aligned with this ADR.
- Do not move AI outputs into signoff inputs.
- Do not wire generated IDS/functions onto the verdict path without journal + pack hash.
