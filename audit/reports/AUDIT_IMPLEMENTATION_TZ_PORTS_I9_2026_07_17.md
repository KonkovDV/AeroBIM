# Audit — Planned vs Implemented (TZ hybrid + I8/I9)

**Date:** 2026-07-17  
**Checkpoint:** **NO_GO** (RT-001/002/003 unchanged)  
**Scope:** Close engineering gaps from `TARGET_HYBRID_ARCHITECTURE_TZ_2026.md` §12 / `EXECUTION_PLAN_I8_I9_2026_07.md` without flipping honesty gates.

## Verdict

| Wave | Status | Evidence |
|------|--------|----------|
| I8a Region detector | **DONE** (prior) | `DrawingRegionDetector` + heuristic adapter |
| I8b RASE tags | **DONE** (prior) | `rase_elements` on issues / IDS drafts |
| I8c HITL escalate | **DONE** + FE filter | Backend prior; FE `HITL regions only` + panel list |
| **I9** IfcKnowledgeGraphPort | **DONE (stub)** | `StubIfcKnowledgeGraph` + DI + agent `query_ifc_kg` + `STUB-IFC-KG-001` |
| SystemClashPort | **DONE (fail-closed)** | `UnconfiguredSystemClash` + agent `detect_system_clash` |
| DrawingAnalyzerPort | **DONE (facade)** | `MultimodalDrawingAnalyzerPort` over OCR multimodal |
| RequirementInterpreterPort | **DONE** | `DeterministicRequirementInterpreter` |
| CadEntityLoaderPort | **DONE** | `EzdxfCadEntityLoader` → `EntityGraph` |
| AgenticReviewOrchestrator | **DONE** | Facade + contour registration |
| RT-001/002/003 | **OPEN** | Customer corpus / norms / MEP — blocks GO |

## Atomic delivery checklist (this ship)

| Port | Adapter | Token | DI | Test | Docs |
|------|---------|-------|----|------|------|
| `IfcKnowledgeGraphPort` | `StubIfcKnowledgeGraph` | `IFC_KNOWLEDGE_GRAPH` | yes | `test_tz_architecture_ports` | KNOWN_BUGS + plans |
| `SystemClashPort` | `UnconfiguredSystemClash` | `SYSTEM_CLASH` | yes | same | TARGET / I8–I9 |
| `RequirementInterpreterPort` | `DeterministicRequirementInterpreter` | `REQUIREMENT_INTERPRETER` | yes | same | TARGET |
| `CadEntityLoaderPort` | `EzdxfCadEntityLoader` | `CAD_ENTITY_LOADER` | yes | same | TARGET |
| `DrawingAnalyzerPort` | `MultimodalDrawingAnalyzerPort` | `DRAWING_ANALYZER_PORT` | yes | same | TARGET |
| `AgenticReviewOrchestrator` | facade | `AGENTIC_REVIEW_ORCHESTRATOR` | yes | same | CONTOUR_PORTS |

## Explicit non-claims

- No GO, no >90% accuracy, no MEP delivered, no CDE-ready BCF
- No product VLM / YOLO weights; `cv_human_level` remains MISSING
- IFC KG stub returns empty GUIDs; DeterminismGate still owns sign-off
- Native DWG / `dwg_dxf` never OK

## Residual backlog (not this ship)

1. Customer RT-001/002/003 evidence packs  
2. Real IfcLLM relational/graph backend (replace STUB-IFC-KG-001)  
3. Federated MEP + clearance matrix → real `SystemClashPort`  
4. Optional YOLO behind `DrawingRegionDetector` (still MISSING until corpus)  
5. Full RASE exception (E) NLP  

## Related

- Claims Lock: `audit/reports/CLAIMS_LOCK_2026_07_17.md`
- Prior I8c audit: `audit/reports/AUDIT_I8C_TZ_V2_RESEARCH_2026_07_17.md`
