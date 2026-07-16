---
title: "AeroBIM TZ Architecture Requirements 2026"
status: active
version: "1.0.0"
last_updated: "2026-07-10"
tags: [aerobim, tz, architecture]
---

# TZ Architecture Requirements

Fills **«Требования к архитектуре решения = TBD»** for the expert-assistant TZ.
Canonical product architecture: [`../06-architecture-reference.md`](../06-architecture-reference.md).

## 1. Product posture

AeroBIM is an **open, multimodal acceptance-criteria engine** and **expert co-pilot**:

- validates IFC against IDS and cross-checks specs, calculations, and drawings;
- surfaces clashes and inconsistencies with provenance;
- exports BCF for coordination;
- **does not** replace the licensed engineer or Solibri’s full geometric rule depth.

## 2. Layered architecture (mandatory)

```text
presentation/   FastAPI + React review shell
application/    Use cases (AnalyzeProjectPackage, jobs, BCF push)
domain/         Models, Protocol ports, quantity algebra
infrastructure/ Adapters (IFC, IDS, stores, OCR, clash, …)
core/           DI container, settings, path jail
```

**Rules:**

1. Domain → Core only. Application → Domain + Core. No Infrastructure imports in Domain/Application.
2. Constructor injection only via `container.resolve(TOKEN)` in [`bootstrap_container()`](../../backend/src/aerobim/infrastructure/di/bootstrap.py).
3. **Atomic Delivery:** every new port ships with adapter + DI token + wiring + test.

## 3. Validation pipeline (sign-off path)

```text
IFC / package
  ├─① Schema / SPF pre-gate          (IfcSchemaValidator, optional bSI cert)
  ├─② IDS document audit             (IdsDocumentAuditor)
  ├─③ IDS + IFC property validation  (IfcTester, IfcOpenShell)
  ├─④ Multimodal cross-doc + drawings
  ├─⑤ Clash / spatial predicates     (optional capability)
  ├─⑥ Drawing structured / OCR       (capability-gated)
  └─⑦ Remarks + report + BCF export
```

Every optional capability must emit `capabilities.* ∈ {ok, skipped, failed}` so silent degradation cannot look like PASS.

## 4. Sign-off path vs advisory AI path

| Path | Allowed technologies | Affects `summary.passed`? |
|------|----------------------|---------------------------|
| **Sign-off** | Deterministic extractors, IDS, IFC, IfcClash, template remarks, OCR+regex baseline | Yes |
| **Advisory** | CV layout models, LLM remark/IDS drafting, speculative NLP | **Never** without HITL accept |

Advisory outputs must be tagged and stored separately (or as review events), never as sole gate for pilot sign-off.

## 5. Domain ports (current + TZ-driven)

### Current (live)

`RequirementExtractor`, `NarrativeRuleSynthesizer`, `DrawingAnalyzer`, `RasterDrawingAnalyzer`, `IfcValidator`, `IdsValidator`, `IfcSchemaValidator`, `IdsDocumentAuditor`, `NormRulePackLoader`, `SectionDiffAnalyzer`, `ClashDetector`, `RemarkGenerator`, `AuditReportStore`, `ReviewEventStore`, `ObjectStore`, `AnalyzeProjectPackageJobStore`, `ExternalEvidenceVerifier`, `BcfApiClient`, `BsiValidationService`.

### Required for TZ waves (add atomically)

| Port | Purpose | Phase |
|------|---------|-------|
| `DocumentUploadStore` | Multipart ingest → object keys + safe paths | P0 done (`POST /v1/uploads`) |
| `RemarkEditor` / HITL | Persist edited remark text (via ReviewEventStore) | P0 done |
| `CadDrawingAnalyzer` | DXF/DWG text/dimension extract | P2 |
| Detection label store (optional) | Persist adjudicated labels beyond file harness | P4 optional |

P1 ports already live: `NormRulePackLoader`, `SectionDiffAnalyzer`, and file-based
`evaluate_detection_precision` harness (no separate store required for pilot protocol).

## 6. Security and deployment integrity

- Fail-closed auth outside `development`/`dev`/`test` (`AEROBIM_API_BEARER_TOKEN` and/or OIDC).
- Storage path jail: reject symlinks outside `AEROBIM_STORAGE_DIR`.
- IFC size limit (default 256 MiB).
- No second HTTP entrypoint; single app factory from DI.

## 7. Persistence

| Concern | Default | Enterprise |
|---------|---------|------------|
| Report payloads | Filesystem under `storage_dir` | + S3/MinIO `ObjectStore` |
| Report index | Filesystem list | Postgres filtered `list_reports` |
| Async jobs | In-memory snapshot | Redis when `AEROBIM_REDIS_URL` set |
| Review telemetry | Filesystem JSONL | same store contract |

## 8. Frontend bounded context

The React shell is a **review surface**, not domain truth:

- loads reports from API;
- focuses IFC GUIDs and drawing `problem_zone` overlays;
- edits remarks via HITL APIs (P0);
- never re-implements validation logic.

## 9. Non-goals (architecture)

- Full CDE product
- Revit-centered runtime
- Autonomous regulatory certification
- Training ML models inside the sign-off path

## Drawing AI posture (retained local SSOT)

July 2026: [../evidence/DRAWING_AI_WORLD_PRACTICE_2026_07.md](../evidence/DRAWING_AI_WORLD_PRACTICE_2026_07.md).
