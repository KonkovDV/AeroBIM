---
title: "AeroBIM Execution Plan I0–I2 (TZ Hybrid Architecture)"
status: active
version: "1.0.0"
last_updated: "2026-07-17"
tags: [aerobim, roadmap, tz, execution]
claim_boundary: "Implementation plan. Checkpoint remains NO_GO until RT-001/002/003."
---

# Execution Plan — I0 / I1 / I2a (post target-architecture)

Parent design: [`TARGET_HYBRID_ARCHITECTURE_TZ_2026.md`](TARGET_HYBRID_ARCHITECTURE_TZ_2026.md).

## Objective

Close the highest-leverage architectural gaps without claiming TZ GO:

1. **I0 — DeterminismGate** (application): engine ≻ advisory; persist divergence warnings.
2. **I2a — MEP DI wiring**: `MepSystemGraphProvider` token + bootstrap (fail-closed Unconfigured*).
3. **I1 — Ingest ports**: `CadModelIngestor` (ezdxf DXF) + `OfficeDocumentIngestor` (Docling/text).

Deferred to later PRs: MultimodalDrawingPipeline, RAG, ComplianceAgent, Quantity/Load/Logic engines, ODA DWG.

## Success criteria (this wave)

| ID | Criterion | Evidence |
|----|-----------|----------|
| S1 | DeterminismGate unit tests: engine wins; advisory-only → non-blocking | pytest |
| S2 | `Tokens.MEP_SYSTEM_GRAPH_PROVIDER` registered; contour updated | bootstrap + arch test |
| S3 | DXF ingest via ezdxf optional extra; DWG without ODA → FAILED; honesty forbids OK | pytest + capabilities |
| S4 | Office ingest port returns `RequirementSource`; degrade without Docling | pytest |
| S5 | `dwg_dxf` may be `NOT_VERIFIED` (DXF partial) but never `OK` | honesty guard |
| S6 | Checkpoint / Claims Lock wording unchanged (NO_GO) | docs spot-check |

## Work breakdown

### I0 DeterminismGate
- [x] `domain` / application: `DivergenceRecord` + `DeterminismGate`
- [x] Wire into `AnalyzeProjectPackageUseCase` (advisory list empty until LLM)
- [x] Tests: reconcile matrix

### I2a MEP DI
- [x] `Tokens.MEP_SYSTEM_GRAPH_PROVIDER`
- [x] bootstrap → `UnconfiguredMepSystemGraphProvider`
- [x] `CONTOUR_PORTS` + analyze probe capability reason update
- [x] Extend `test_mep_system_graph_contract.py`

### I1 Cad + Office
- [x] Ports in `domain/ports.py` + `CadIngestResult`
- [x] `EzdxfCadModelIngestor` + optional `[cad]` extra
- [x] `DoclingOfficeDocumentIngestor` / text fallback
- [x] DI tokens + analyze integration for `.dxf`/`.dwg` drawing sources
- [x] Honesty: allow `NOT_VERIFIED` for `dwg_dxf`; never `OK`

## Out of scope (do not ship in this wave)

- Claiming BCF CDE-ready, >90% accuracy, MEP clash verified, calculation correctness
- New `@sota-stub` multimodal/LLM adapters without KNOWN_BUGS entries
- Force-push / history rewrite

## Verification commands

```bash
cd backend
python -m pytest tests/test_determinism_gate.py tests/test_mep_system_graph_contract.py tests/test_cad_office_ingest.py tests/test_architecture_seams.py -q
ruff check src tests
ruff format --check src tests
```

## Iteration after this wave

- [x] **I2b** Quantity / Load / Logic ports + adapters + analyze wire
- [x] **I3** MultimodalDrawingPipeline (OCR degrade only; cv_human_level stays MISSING)
- [x] **I4** Deterministic RequirementToIdsCompiler + FilesystemNormCorpusRetriever (advisory; no LLM)
- [x] **I5** ComplianceAgentOrchestrator (deterministic ReAct tool allowlist → DeterminismGate)
- [x] **I6** Customer metrics readiness — see [`EXECUTION_PLAN_I6_2026_07.md`](EXECUTION_PLAN_I6_2026_07.md)
- [x] **I7** Post-I6 polish — see [`EXECUTION_PLAN_I7_2026_07.md`](EXECUTION_PLAN_I7_2026_07.md)
- Next: **RT-001/002/003** (customer) · research waves [`EXECUTION_PLAN_I8_I9_2026_07.md`](EXECUTION_PLAN_I8_I9_2026_07.md) · [`RESEARCH_ALIGNMENT_AEC_AI_2025_2026_07.md`](RESEARCH_ALIGNMENT_AEC_AI_2025_2026_07.md)
