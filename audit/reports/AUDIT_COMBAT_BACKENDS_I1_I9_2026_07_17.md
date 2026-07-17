# Self-audit — Combat backends I1 / Hybrid CV / I9 relational / RT harness / MEP

**Date:** 2026-07-17  
**Checkpoint:** **NO_GO** (RT-001/002/003 **HOLD** — no customer evidence)  
**Literature (boundaries only):** AECV-Bench arXiv:2601.04819; IfcLLM arXiv:2605.13236 (do not cite 93–100% as AeroBIM); Blueprint arXiv:2602.13345; Solibri-class deterministic core; Iversen&Huang / multi-agent AiC tool-calling.

## Diff-plan executed (atomic)

### 1. CAD EntityGraph (I1)

| Layer | Path |
|-------|------|
| Domain | `domain/tz_architecture_ports.py` (`CadEntityLoaderPort`, `EntityGraph`) |
| Adapter | `infrastructure/adapters/ezdxf_cad_entity_loader.py` (objects/dimensions/text) |
| ODA stub | `oda_cad_model_ingestor.py` + `Tokens.ODA_CAD_MODEL_INGESTOR` |
| DI | `bootstrap.py` — `CAD_ENTITY_LOADER`, `ODA_CAD_MODEL_INGESTOR` |
| Settings | `AEROBIM_ODA_CAD_ENABLED` |
| Fixture | `samples/cad/minimal-entities.dxf` |
| Capability | no `[cad]` → SKIPPED; with ezdxf → NOT_VERIFIED; **never OK** |

### 2. HybridDrawingAnalyzer (CV advisory)

| Layer | Path |
|-------|------|
| Adapter | `hybrid_drawing_analyzer.py` |
| Extra | `pyproject.toml` `[vision]` = Pillow |
| DI | `DRAWING_ANALYZER_PORT` → Hybrid when `AEROBIM_HYBRID_DRAWING_ENABLED` |
| Honesty | `cv_human_level` stays MISSING; low_confidence → I8c HITL; docs = priors / future YOLO |
| Claim | Khan RCIM narrow-domain ≠ product; AECV-Bench counting 0.40–0.55 = unsolved |

### 3. I9 RelationalIfcKnowledgeGraph

| Layer | Path |
|-------|------|
| Adapter | `relational_ifc_knowledge_graph.py` (default DI) |
| Tool | `tools/evaluate_ifc_qa.py` + `samples/benchmarks/ifc-qa-ru/` |
| Agent | existing `query_ifc_kg` |
| Claim | Fixture accuracy only; **not** IfcLLM product numbers |

### 4. RT precision protocol (harness only)

| Change | Detail |
|--------|--------|
| `evaluate_detection_precision` | `per_discipline`, `clash_vs_nonclash` |
| Template | `labels-customer-protocol-template.json` |
| Gate | κ≥0.60 still required for publishable; **intake gates not flipped** |

### 5. SystemClash (MEP-CLASH-001)

| Adapter | Behavior |
|---------|----------|
| Default | `UnconfiguredSystemClash` |
| Opt-in | `IfcSystemAwareClash` + scope memo + IfcSystem |
| HOLD | MEP-CLASH-001 **remains open** until customer federated pack |

## HOLD vs lifted

| Item | Status |
|------|--------|
| RT-001 customer corpus | **HOLD** |
| RT-002 approved norms | **HOLD** |
| RT-003 federated MEP | **HOLD** (adapter scaffold only) |
| Engineering CAD DXF EntityGraph | **lifted** (combat path) |
| Hybrid CV wiring | **lifted** (advisory degrade) |
| I9 relational advisory | **lifted** (stub demoted to fallback) |
| Detection harness discipline/clash split | **lifted** |
| GO / >90% / DWG OK / CV OK / MEP delivered | **HOLD** |

## NFR notes

- Redis jobs: existing `AEROBIM_REDIS_URL`
- IFC cache dir setting: `AEROBIM_IFC_PARSE_CACHE_DIR` (wired in Settings; consumers may adopt)
- Drawing-CV remains parallel/advisory — not on IFC/IDS/BCF critical path for `summary.passed`
