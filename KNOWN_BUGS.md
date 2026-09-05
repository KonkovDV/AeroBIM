# KNOWN_BUGS — AeroBIM tracked stubs & honesty debt

> Status: living register. Every `@sota-stub` adapter MUST have an entry here.
> Product Checkpoint is **GO** (`regulatory_measurement_mvp`). `customer_go` stays
> **false** until residual RT-001b/c, RT-002c, RT-003c, federated IFC, and CDE T2.
> Do not read that as product `NO_GO`. Undifferentiated `closes_rt001/002/003` stay false.

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
| Honesty | `dwg_dxf` never OK; flag=true without SDK → distinct `NATIVE_DWG_ODA_ENABLED_NO_SDK_REASON` (2026-08-11); analyze uses `EzdxfCadModelIngestor` only |

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

### STUB-MEP-GRAPH-001 (unit tests only)

| Field | Value |
|-------|-------|
| Stub ID | `STUB-MEP-GRAPH-001` |
| Tag | `@sota-stub` |
| Adapter | `backend/src/aerobim/domain/mep.py` (`SyntheticMepSystemGraphProvider`) |
| Port | `MepSystemGraphProvider` |
| Severity | **MEDIUM** |
| Effect | Fixed multi-system synthetic graph for unit/integration tests; analyze probe stays `NOT_VERIFIED` |
| Blockers | Customer federated IFC + signed scope memo + clearance matrix (RT-003) |
| Target | Replace with real IFC system-assignment provider after RT-003 evidence |
| Honesty | Never DI default; never `mep_system_clash=OK`; template JSON stays template |

## Tracked residuals (not stubs)

| ID | Kind | Honesty |
|----|------|---------|
| JOB-01 | Analyze **runner** is in-process FastAPI `BackgroundTasks`. Redis stores job **records**, not execution. | Not a Shared-gate writer. Do not claim durable workers. |
| XML-POSTPARSE-01 | Element/depth/text caps run after defusedxml builds a tree. Byte cap (16 MiB) applies **before** parse. | Availability inside the cap, not XXE. |
| IFC-ISO-01 | IfcOpenShell opens in the API process (1.5 GB disk band). Pdfium stays isolated. | Crash/OOM ≠ silent `summary.passed=true`. Not MEP delivered. |

S3 presign cap, S3 dial pin, Windows pdfium Job Object, BFF token-exchange body cap,
and path-jail percent-decode-to-fixpoint are closed below / in tests. Checkpoint
**GO**; customer_go false.

## Closed / N/A

### HD19-S3-01 — presigned GET bypasses stream cap — CLOSED

| Field | Value |
|-------|-------|
| ID | `HD19-S3-01` |
| Adapter | `backend/src/aerobim/infrastructure/adapters/s3_object_store.py` (`presign_get`) |
| Severity | **INFO** (closed) |
| Effect | `head_object` runs before `generate_presigned_url`. Missing object → `None`. `ContentLength > max_get_bytes` → `ObjectTooLargeError` (parity with `LocalObjectStore`). Direct `get_bytes` remains stream-capped. |
| Honesty | **No `.presign_get(` callers in `backend/src`**. Does not sit on the `summary.passed` path. Checkpoint **GO**; customer_go false. |
| Status | Closed 2026-09-05. |

### HD19-S3-02 — S3 boto3 dials hostname after DNS pin — CLOSED

| Field | Value |
|-------|-------|
| ID | `HD19-S3-02` |
| Adapter | `backend/src/aerobim/infrastructure/adapters/s3_object_store.py` (`_build_client`) + `core/security/outbound_url.py` (`pin_s3_outbound_dials`) |
| Severity | **LOW** (closed) |
| Effect | Custom `endpoint_url` is resolved with `resolve_and_pin_outbound_url`. TCP is pinned via `socket.create_connection` to the validated IP; hostname stays on the URL for Host/SNI. Virtual-hosted `{bucket}.{host}` is pinned to the same IP. Default AWS regional endpoints (no custom URL) are unchanged. |
| Honesty | Does not sit on the `summary.passed` path. Checkpoint **GO**; customer_go false. |
| Status | Closed 2026-09-05. |

### PROC-01 — Windows pdfium isolate has no RLIMIT_AS / RLIMIT_CPU — CLOSED

| Field | Value |
|-------|-------|
| ID | `PROC-01` |
| Adapter | `backend/src/aerobim/infrastructure/adapters/pdfium_isolate/process_isolate.py` |
| Severity | **LOW** (closed) |
| Effect | POSIX child still applies `RLIMIT_AS` (1 GiB) and `RLIMIT_CPU` (30s) via `preexec_fn`. Windows creates a Job Object with `JOB_OBJECT_LIMIT_PROCESS_MEMORY` (1 GiB) and `JOB_OBJECT_LIMIT_PROCESS_TIME` (30s). If `CreateJobObjectW` / `AssignProcessToJobObject` fails (nested job), the isolate falls back to subprocess timeout only. |
| Honesty | Does not sit on the `summary.passed` path. Checkpoint **GO**; customer_go false. |
| Status | Closed 2026-09-05. |

- Cad / OCR multimodal / MEP unconfigured adapters are real fail-closed or degrade paths (not `@sota-stub`).
- `UnconfiguredSystemClash` / `UnconfiguredMepSystemGraphProvider` are honesty fail-closed (MEP-CLASH-001), not stubs.
- `HybridDrawingAnalyzer` ships detector **priors / future YOLO** only — no YOLO weights; not a stub, honesty degrade.
- `RelationalIfcKnowledgeGraph` is real I/O (ifcopenshell) — **advisory scaffold** only; not a stub, but **not** GraphRAG / IfcLLM product capability.
- F-15 / LIC: dependency license inventory + CI gate (`audit/dependency_license_inventory.json`, `backend/tests/test_dependency_license_gate.py`). LGPL IfcOpenShell / ifctester and optional AGPL PyMuPDF (`extra:pdf-agpl`) require legal review before redistribution / SaaS claims. Engineering inventory, not a legal opinion and not a runtime vuln. Not a customer-data finding.
