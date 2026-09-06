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

### REAL-01 — IFC parsing on main thread → UI freeze on large files — CLOSED

| Field | Value |
|-------|-------|
| ID | `REAL-01` |
| Severity | **HIGH** (closed) |
| Symptom | `IfcAPI.OpenModel` + `StreamAllMeshes` ran synchronously on the browser main thread. Loading a large IFC file blocked rendering, froze pointer events, and made the entire UI unresponsive for several seconds — the most visible UX defect during a jury demo. |
| Root cause | `IfcSceneController` instantiated `IfcAPI` (WASM) directly on the main thread. |
| Fix | Three new files (PR #27, 2026-09-06): `ifc-worker-protocol.ts` (message types), `ifc-parser.worker.ts` (Vite module Worker: Init, OpenModel, StreamAllMeshes, spatial index, element-props cache), updated `ifc-scene.ts` (Worker integration, Transferable typed arrays, synchronous element-props cache via `elementPropsCache` Map). Public API of `IfcSceneController` is unchanged. |
| Files | `frontend/src/lib/ifc-worker-protocol.ts` (new), `frontend/src/workers/ifc-parser.worker.ts` (new), `frontend/src/lib/ifc-scene.ts` (modified) |
| Status | Closed 2026-09-06. PR #27. |

### BE-01 — `mark_failed()` not guarded against store exceptions — CLOSED

| Field | Value |
|-------|-------|
| ID | `BE-01` |
| Severity | **MEDIUM** (closed) |
| Symptom | If the DB/store raised an exception inside `AnalyzeProjectPackageJobRunner.run()` after a domain-level failure, the secondary `mark_failed()` call was unprotected. A DB write error there would propagate to FastAPI's `BackgroundTasks` runner, leaving the job permanently stuck in `RUNNING` until `reclaim_stale_running()` rescued it at the next submit. |
| Root cause | Missing `try/except` around `self._job_store.mark_failed(job_id, error_msg)` in the exception handler. |
| Fix | Wrapped `mark_failed` in its own `try/except Exception`; secondary store error is logged separately (with `job_id`, `request_id`, and detail) and does not re-raise, so the outer error path always completes. `reclaim_stale_running` is still the safety net. |
| File | `backend/src/aerobim/application/use_cases/analyze_project_package_jobs.py` |
| Status | Closed 2026-09-06. PR #27. |

### BE-02 — Idempotency-Key validated after expensive request build — CLOSED

| Field | Value |
|-------|-------|
| ID | `BE-02` |
| Severity | **LOW** (closed) |
| Symptom | In `submit_analyze_project_package`, the `Idempotency-Key` header normalization and `≤128 char` validation happened **after** `ctx.build_project_package_request()` — a potentially expensive call that resolves paths, checks IFC file sizes, and validates payload. A malformed key (e.g. 200-char garbage string) incurred the full request-build cost before returning 400. |
| Root cause | Ordering error in route handler. |
| Fix | Moved `idem = _normalize_idempotency_key(idempotency_key)` and the length guard `HTTPException(400)` to before the `try` block that calls `build_project_package_request`. |
| File | `backend/src/aerobim/presentation/http/routes/analyze.py` |
| Status | Closed 2026-09-06. PR #27. |

### BE-03 — sync `analyze_project_package` missing success log — CLOSED

| Field | Value |
|-------|-------|
| ID | `BE-03` |
| Severity | **LOW** (closed) |
| Symptom | The synchronous `/v1/analyze/project-package` route never emitted a success log line (e.g. `report_id`), unlike `/v1/validate/ifc` which logged `validate_ifc completed` with `report_id`, `passed`, and `issues`. Operational gaps: no latency-by-`report_id` tracing from logs, no easy success/error ratio baseline. |
| Fix | Added `logger.info("analyze_project_package completed", report_id=report.report_id)` before the `return` statement, consistent with `validate_ifc`. |
| File | `backend/src/aerobim/presentation/http/routes/analyze.py` |
| Status | Closed 2026-09-06. PR #27. |

### REAL-04 — `useCallback([cols])` anti-pattern in `ResizableWorkplace` — CLOSED

| Field | Value |
|-------|-------|
| ID | `REAL-04` |
| Severity | **LOW** (closed) |
| Symptom | `onResize` was memoised with `[cols]` in its dependency array. Because `cols` is React state that changes on every `setCols` call (i.e. every `pointermove` during a column drag), `useCallback` recreated the function reference on every drag frame. This is worse than not using `useCallback` at all: it adds memoisation overhead without ever producing a stable reference. Any `React.memo`-wrapped child receiving `onResize` as a prop would re-render on every drag event. |
| Root cause | `onResize` captured `cols` in its closure (to snapshot drag-start state) but that capture was expressed as a `useCallback` dep instead of a ref. |
| Fix | Added `const colsRef = useRef(cols); colsRef.current = cols;` (sync-in-render ref pattern) and changed `useCallback` deps to `[]`. `onResize` now reads `colsRef.current` at `pointerDown` time for the drag-start snapshot, staying stable for the entire component lifetime. |
| File | `frontend/src/features/workplace/ResizableWorkplace.tsx` |
| Status | Closed 2026-09-06. PR #27. |

### REAL-05 — `useAuthBff`: no retry on BFF unavailability — CLOSED

| Field | Value |
|-------|-------|
| ID | `REAL-05` |
| Severity | **LOW** (closed) |
| Symptom | `useAuthBff` fired a single `fetchAuthBff()` call inside a `void` async IIFE. If the BFF was transiently unavailable (container warm-up, network blip, reverse-proxy not ready), the thrown error was silently swallowed and the hook stayed in `DEFAULT_DISCOVERY` (`NOT_IMPLEMENTED / 501`) permanently for that page load. Auth-gated features appeared broken to the user with no log and no recovery path. |
| Root cause | No error handling and no retry in the `useEffect` async body. The `void` IIFE suppressed the unhandled-rejection warning as well. |
| Fix | Extracted `fetchBffWithRetry(signal: AbortSignal)`: 3 attempts with delays `[0, 1000, 3000]` ms. Abort signal checked before each retry so React StrictMode double-invoke and component unmount clean up correctly. On total failure: logs `console.warn` (operator-visible) and returns `DEFAULT_DISCOVERY` for graceful degradation. Replaced `boolean cancelled` flag with `AbortController` for future-proofing (signal-aware fetch helpers). |
| File | `frontend/src/hooks/useAuthBff.ts` |
| Status | Closed 2026-09-06. PR #27. |

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
