---
title: "AeroBIM Execution Plan I8–I9 — Research-aligned advisory waves"
status: active
version: "1.0.0"
last_updated: "2026-07-17"
tags: [aerobim, roadmap, i8, i9, research, blueprint, ifcllm]
claim_boundary: >
  Planning only. Checkpoint remains NO_GO. No product VLM, GraphRAG, or accuracy claims.
  Literature map: RESEARCH_ALIGNMENT_AEC_AI_2025_2026_07.md
---

# Execution Plan — I8 / I9 (post–I7, research-aligned)

Parent: [`TARGET_HYBRID_ARCHITECTURE_TZ_2026.md`](TARGET_HYBRID_ARCHITECTURE_TZ_2026.md) · Research: [`RESEARCH_ALIGNMENT_AEC_AI_2025_2026_07.md`](RESEARCH_ALIGNMENT_AEC_AI_2025_2026_07.md) · Prior: I0–I7

## Objective

Translate 2025–2026 AEC AI practice (Blueprint region pipelines, hybrid ACC/RASE, IfcLLM GraphRAG) into **advisory** AeroBIM seams without flipping honesty gates or claiming GO.

## Priority order

| Order | Wave | Why |
|-------|------|-----|
| 0 | **RT-001/002/003** | Customer corpus / norms / MEP — blocks any GO discussion |
| 1 | **I8a** | Blueprint-style regions before whole-sheet VLM |
| 2 | **I8b** | RASE-ish provenance for ACC transparency |
| 3 | **I8c** | HITL escalate unmatched drawing regions |
| 4 | **I9** | IfcLLM-style knowledge graph query (advisory only) |

## I8a — Region detector behind MultimodalDrawingPipeline

- [x] Port/adapter: layout region detector feeding `DrawingRegionRef` (`DrawingRegionDetector` + `HeuristicLayoutRegionDetector`)
- [x] Region-restricted path: detector priors merge with OCR; full-page VLM still degrade
- [x] Honesty: `cv_human_level` stays **MISSING** (pipeline `degraded=True` + reason)
- [x] Tests: detector without raster → `detector_only`; DI token registered
- [ ] Future: YOLO/Blueprint weights behind same port (optional; still MISSING until corpus)

**Driver:** Blueprint (arXiv:2602.13345)

## I8b — RASE-style provenance on advisory findings

- [x] Optional R/A/S/E tags on advisory issues / IDS drafts (`rase_elements`, `rase_summary`)
- [x] Deep-link via existing `norm_clause` + pack fields; `issue_from_requirement` stamps RASE
- [x] Never write `summary.passed` from RASE/LLM path (tags are metadata only)
- [ ] Full RASE exception (E) NLP extraction — deferred

**Driver:** Hybrid ACC / LLM→IDS literature (re-verify before public cite)

## I8c — HITL escalate unmatched regions

- [x] Unmatched / low-confidence `DrawingRegionRef` → `hitl_required` + INFO issue
- [x] `ReviewEvent` type `drawing_region_escalated` persisted when store wired
- [x] Frontend types consume `hitl_required` / `hitl_reason`
- [x] FE triage queue UX (filter by hitl_required) — App checkbox + DrawingEvidencePanel list

**Driver:** Cross-document VLM escalate pattern + Blueprint HITL practice

## I9 — IfcKnowledgeGraphPort (**advisory scaffold**, not product capability)

- [x] Domain port + DI token + relational adapter (Atomic Delivery) — `RelationalIfcKnowledgeGraph`
- [x] Agent allowlist tool: `query_ifc_kg` → GUIDs
- [x] DeterminismGate mandatory; no capability OK for “IFC LLM understanding”
- [x] RU fixture CI harness `evaluate_ifc_qa` (fixture-only; not IfcLLM numbers)
- [x] `KNOWN_BUGS` — stub demoted to fallback; ODA stub tracked
- [ ] Multi-hop **GraphRAG** + customer IFC-QA (post RT-001) — **not shipped**

**Status label for prompts/presentations:** `ADVISORY SCAFFOLD` — never «I9 DONE» as a product feature.

**Also shipped with I9 wave (TZ TARGET aliases):**

- [x] `SystemClashPort` + `UnconfiguredSystemClash` + agent `detect_system_clash`
- [x] `RequirementInterpreterPort` / `CadEntityLoaderPort` / `DrawingAnalyzerPort` facades
- [x] `AgenticReviewOrchestrator` DI facade + CONTOUR_PORTS update

**Driver:** IfcLLM (arXiv:2605.13236)

## Explicit non-goals

- Claiming GO, >90%, MEP delivered, CDE-ready BCF, customer SLA
- Raising publishable κ gate to 0.80 without customer protocol (stretch SOP only)
- Whole-sheet GPT-4V as product CV
- Raw IFC dumped into LLM context

## Verification (when implementing)

```bash
cd backend
python -m pytest tests/test_architecture_seams.py tests/test_determinism_gate.py -q
# plus wave-specific tests
```

## Related SSOT

- Next work (all tracks): [`EXECUTION_PLAN_NEXT_2026_07.md`](EXECUTION_PLAN_NEXT_2026_07.md)
- Claims Lock: `audit/reports/CLAIMS_LOCK_2026_07_17.md`
- Drawing practice memo: `docs/evidence/DRAWING_AI_WORLD_PRACTICE_2026_07.md`
- Intake runbook: `docs/ops/intake-precision-runbook-2026.md`
