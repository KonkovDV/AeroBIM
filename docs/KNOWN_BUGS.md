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
| Effect | DWG ingest is not implemented; DXF via ezdxf is the combat path |
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
| JOB-01 | Production HTTP is producer-only; dedicated `aerobim.worker` reserves Redis JSON deliveries with `BLMOVE`, retains them until terminal ACK, and recovers expired leases. | Delivery is at-least-once, not physically exactly-once. Redis remains a single-node failure domain and the long-lived container is not a fresh per-job sandbox. |
| XML-POSTPARSE-01 | Element/depth/text caps run after defusedxml builds a tree. Byte cap (16 MiB) applies **before** parse. | Availability inside the cap, not XXE. |
| IFC-ISO-01 | Production async IfcOpenShell runs in a dedicated long-lived worker container (1.5 GB disk band); the synchronous API path is disabled by production compose. Pdfium crop and pdfminer drawing extract run in a child process with wall-clock kill. | Worker limits are not a fresh per-job sandbox. Crash/OOM ≠ silent `summary.passed=true`. Not MEP delivered. |
| UPLOAD-OS-01 | Upload object-store path uses `put_file` + `asyncio.to_thread`. RSS of this branch was not measured. | Not an OOM-closed claim. IFC caps unchanged. |
| CUST-REHEARSE-20260917 | Local customer-pack rehearsal 2026-09-17: upload → analyze → lab-reviewer HITL persist → structurally valid BCF. Verdict **PARTIAL**. | Not independent expert. Unsigned IDS ≠ signed profile. CDE import **NOT_VERIFIED**. Not a publishable accuracy pin. No customer hashes in git. |

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

### DOCKER-VOL-01 — first-boot named volume PermissionError — CLOSED

| Field | Value |
|-------|-------|
| ID | `DOCKER-VOL-01` |
| Adapter | `backend/Dockerfile` (`mkdir /data/reports` as aerobim) + `FilesystemAuditStore` |
| Severity | **MEDIUM** (closed engineering) |
| Effect | Image now owns `/data/reports` so a **new** named volume copies aerobim uid. Leftover root-owned volumes still need `docker compose down -v` or chown 999:999. |
| Honesty | Operational first-boot, not Shared-gate. Checkpoint **GO**; customer_go false. |
| Status | Closed 2026-09-17. |

### BCF-HITL-01 — TopicStatus Open and empty HITL Comment — CLOSED

| Field | Value |
|-------|-------|
| ID | `BCF-HITL-01` |
| Adapter | `bcf_report_exporter.py` / `bcf3_exporter.py` + `review_projection.bcf_hitl_overlay` |
| Severity | **MEDIUM** (closed engineering) |
| Effect | Accepted/waived findings export TopicStatus Closed, ModifiedAuthor = expert, Comment* with Date/Author/text. Rejected findings still omitted. CreationAuthor stays machine. |
| Honesty | Structural T1 only. CDE import T2 **NOT_VERIFIED**. Lab-reviewer is not an independent expert. |
| Status | Closed 2026-09-17. |

### VIEWER-DELETE-01 — `flatMesh.delete is not a function` — CLOSED

| Field | Value |
|-------|-------|
| ID | `VIEWER-DELETE-01` |
| Adapter | `frontend/src/lib/web-ifc-release.ts` |
| Severity | **MEDIUM** (closed engineering) |
| Effect | Viewer skips `delete()` when web-ifc handles omit it. Does not claim WASM memory is always released. |
| Honesty | Browser review shell only. Not a model-viewer product claim. |
| Status | Closed 2026-09-17. |

### IFC-TRUNC-01 — truncated STEP header accepted as IFC — CLOSED

| Field | Value |
|-------|-------|
| ID | `IFC-TRUNC-01` |
| Adapter | `core/security/upload_content.py` |
| Severity | **LOW** (closed engineering) |
| Effect | `.ifc` uploads require `FILE_SCHEMA` in the sniff window. Header-only sniff still detects STEP; completeness is validate-time. |
| Honesty | Not a schema validator. Truncation after FILE_SCHEMA can still upload. |
| Status | Closed 2026-09-17. |

- Cad / OCR multimodal / MEP unconfigured adapters are real fail-closed or degrade paths (not `@sota-stub`).
- `UnconfiguredSystemClash` / `UnconfiguredMepSystemGraphProvider` are honesty fail-closed (MEP-CLASH-001), not stubs.
- `HybridDrawingAnalyzer` ships detector **priors / future YOLO** only — no YOLO weights; not a stub, honesty degrade.
- `RelationalIfcKnowledgeGraph` is real I/O (ifcopenshell) — **advisory scaffold** only; not a stub, but **not** GraphRAG / IfcLLM product capability.
- F-15 / LIC: dependency license inventory + CI gate (`audit/dependency_license_inventory.json`, `backend/tests/test_dependency_license_gate.py`). LGPL IfcOpenShell / ifctester and optional AGPL PyMuPDF (`extra:pdf-agpl`) require legal review before redistribution / SaaS claims. Engineering inventory, not a legal opinion and not a runtime vuln. Not a customer-data finding.
