# KNOWN_BUGS — AeroBIM tracked stubs & honesty debt

> Status: living register. Every `@sota-stub` adapter MUST have an entry here.
> Checkpoint remains **NO_GO** until RT-001/002/003 with customer evidence.

## Active stubs

### STUB-IDS-ASSIST-001

| Field | Value |
|-------|-------|
| Stub ID | `STUB-IDS-ASSIST-001` |
| Tag | `@sota-stub` |
| Adapter | `backend/src/aerobim/application/services/ids_assist_boundary.py` (`StubIdsAssistDraftAdapter`) |
| Port | `IdsAssistDraftPort` |
| Severity | **LOW** |
| Effect | Advisory IDS assist only; never writes `summary.passed` |
| Blockers | Real provider-agnostic LLM client + DeterminismGate already required for any promotion |
| Target | Post-customer-corpus advisory wave |
| Honesty | Does **not** flip intake gates |

### STUB-ODA-CAD-001

| Field | Value |
|-------|-------|
| Stub ID | `STUB-ODA-CAD-001` |
| Tag | `@sota-stub` |
| Adapter | `backend/src/aerobim/infrastructure/adapters/oda_cad_model_ingestor.py` |
| Port | `CadModelIngestor` (ODA path) / token `ODA_CAD_MODEL_INGESTOR` |
| Severity | **MEDIUM** |
| Effect | Native DWG remains unsupported; DXF via ezdxf is the combat path |
| Blockers | Legal review + licensed ODA/Teigha; flag `AEROBIM_ODA_CAD_ENABLED` |
| Target | After legal review; never claim DWG product readiness without customer DWG evidence |
| Honesty | `dwg_dxf` never OK |

### STUB-IFC-KG-001 (fallback only)

| Field | Value |
|-------|-------|
| Stub ID | `STUB-IFC-KG-001` |
| Tag | `@sota-stub` |
| Adapter | `stub_ifc_knowledge_graph.py` (fallback; default DI is `RelationalIfcKnowledgeGraph`) |
| Port | `IfcKnowledgeGraphPort` |
| Severity | **LOW** |
| Effect | Degraded empty GUIDs if explicitly constructed |
| Note | Default bootstrap uses relational ifcopenshell keyword route — still **advisory scaffold**, not IfcLLM/GraphRAG product |

## Closed / N/A

- Cad / OCR multimodal / MEP unconfigured adapters are real fail-closed or degrade paths (not `@sota-stub`).
- `UnconfiguredSystemClash` / `UnconfiguredMepSystemGraphProvider` are honesty fail-closed (MEP-CLASH-001), not stubs.
- `HybridDrawingAnalyzer` ships detector **priors / future YOLO** only — no YOLO weights; not a stub, honesty degrade.
- `RelationalIfcKnowledgeGraph` is real I/O (ifcopenshell) — **advisory scaffold** only; not a stub, but **not** GraphRAG / IfcLLM product capability.
