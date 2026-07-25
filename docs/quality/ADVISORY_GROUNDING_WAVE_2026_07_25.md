---
title: "Advisory evidence grounding (DeterminismGate)"
status: done
version: "1.0.0"
last_updated: "2026-07-25"
claim_boundary: "Grounding stamps are advisory-contour metadata: never raise severity, never write summary.passed, never drop findings. Checkpoint stays NO_GO."
---

# Wave J — Advisory evidence grounding (2026-07-25)

## External anchors (Jul 2026)

| Domain | Anchor |
|---|---|
| Atomic claim verification | TACO, EACL 2026 (2026.eacl-long.252) — self-verified atomic confidence; claims must bind to evidence |
| Verification prompting | Chain-of-Verification — plan checks, verify, revise |
| Grounded fact-checking | FinGround (arXiv 2604.23588) — decompose answers into atomic claims verified against evidence |
| Internal SSOT | ADR-001 / DeterminismGate — engine owns summary.passed; advisory is never authoritative |

## Gap closed

DeterminismGate demoted advisory-only findings to INFO but performed **no
grounding**: an advisory issue referencing a hallucinated element GUID or
target (never seen by the deterministic engine) flowed into review/provenance
indistinguishable from a well-grounded observation.

## Delivered (code + test)

- `determinism_gate.py`:
  - `build_evidence_universe(...)` — deterministic token set: engine issue
    GUIDs/target_refs, requirement rule_ids/target_refs/ifc_entities, clash
    pair GUIDs, drawing annotation target_refs;
  - `reconcile(..., evidence_universe=None)` — advisory-only findings are
    classified per references: `grounding:verified_reference` /
    `grounding:unverified_reference` (+ `[ungrounded]` message with the
    unknown tokens, divergence verdict prefixed `ungrounded:`) /
    `grounding:no_verifiable_reference`; findings are never dropped and stay
    INFO; `None` universe → exact legacy behavior (backward compatible).
- `AdvisoryOrchestrator.run(request, deterministic, ingested)` builds the
  universe from the deterministic bundle + ingestion bundle; both `execute`
  paths (with/without trace collector) wired.
- `tests/test_advisory_grounding.py` — 6 tests: universe collection, verified/
  ungrounded/no-reference stamps, never-raise/never-drop invariant, legacy
  behavior without a universe.

## Explicitly NOT claimed

- Not semantic entailment/NLI — grounding checks reference existence only
  (deterministic, no model); message-level truth still requires HITL.
- No change to Shared-gate, DivergenceRecord schema, or advisory OFF==ON seam
  invariants (verified by existing seam tests staying green).

## Gate evidence (2026-07-25 local)

`ruff format/check` PASS · `mypy src` 193 files PASS · `pytest tests -q`
**982 passed, 7 skipped**.
