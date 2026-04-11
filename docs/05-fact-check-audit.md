---
title: "AeroBIM Fact-Check And Corrected Architecture Audit"
status: active
version: "0.3.0"
last_updated: "2026-04-10"
tags: [aerobim, audit, evidence, architecture]
---

# AeroBIM Fact-Check And Corrected Architecture Audit

Date: 2026-04-10

Evidence sources: ISO publication metadata, buildingSMART standards and services pages, W3C SHACL Recommendation, official GitHub repositories and websites for IfcOpenShell, xBIM, BIMserver, web-ifc, xeokit, Docling, APS community blog posts, Solibri, Navisworks, BIMcollab, plus direct repository inspection.

Scope of this audit state:

- refresh the architecture evidence base;
- correct stale audit findings against current repository state;
- document the transition from docs-first skeleton to the current validated runtime slice.

---

## 1. Standards And Protocol Verdicts

### IFC / ISO 16739-1:2024

**Verdict: CONFIRMED.**
IFC remains the canonical vendor-neutral data model. The current anchor is ISO 16739-1:2024.

### IDS 1.0

**Verdict: CONFIRMED.**
buildingSMART publishes IDS 1.0 as a final standard, making it the correct primary rule-expression surface for IFC delivery requirements.

### BCF

**Verdict: CONFIRMED.**
BCF exists both as file exchange and as a REST-style API family, which makes it the correct issue-transport surface for findings and viewpoints.

### bSDD

**Verdict: CONFIRMED.**
bSDD is a terminology and dictionary service. It is useful for enrichment, mappings, and canonical identifiers, but it is not the main validation language.

### SHACL

**Verdict: CONFIRMED WITH A BOUNDARY.**
SHACL is a W3C Recommendation for RDF graph validation. It is valuable for semantic overlays or knowledge-graph validation, but it is not an IFC-native replacement for IDS in the MVP.

### OpenCDE / buildingSMART APIs

**Verdict: CONFIRMED.**
The buildingSMART stack clearly exposes BCF, Foundation, Documents, and bSDD APIs as interoperable surfaces.

---

## 2. Tooling And Licensing Verdicts

### IfcOpenShell

**Verdict: CONFIRMED.**
IfcOpenShell is the foundational open-source IFC runtime in the evidence package, with adjacent utilities for BCF, IDS auditing, diffing, and conversion.

### IfcTester

**Verdict: CONFIRMED.**
IfcTester remains the shortest standards-aligned path from IDS packages to executable IFC validation.

### xBIM

**Verdict: CONFIRMED.**
xBimEssentials is the strongest .NET-native openBIM toolkit in the current research set. `Xbim.IDS.Validator` provides IDS support, but carries AGPL-3.0 licensing constraints.

### BIMserver

**Verdict: CONFIRMED.**
BIMserver is an active open-source IFC server platform with object storage, versioning, merging, and model-query capabilities. It is strategically relevant as an optional interop/storage adapter, not as the MVP core.

### Docling

**Verdict: CONFIRMED.**
Docling is a credible document-conversion and extraction component. `arXiv:2408.09869` is the correct technical report reference.

### SmolDocling / DocTags

**Verdict: CONFIRMED, WITH TERMINOLOGY CORRECTION.**
`arXiv:2503.11576` should be cited as `SmolDocling`, which introduces DocTags as the markup representation. Referring to the paper as `DocTags` alone is imprecise.

### web-ifc

**Verdict: CONFIRMED.**
`web-ifc` is an actively maintained browser and Node IFC runtime, published on npm, built around a WASM core, and currently licensed under MPL-2.0.

### xeokit

**Verdict: CONFIRMED WITH LICENSE GATE.**
xeokit is a serious high-performance BIM/AEC viewer SDK with BCF viewpoint support, federated-scene strengths, and XKT-based large-model workflows. The open-source route is AGPL-3.0, with proprietary licensing offered separately.

### APS Viewer And Model Derivative

**Verdict: CONFIRMED.**
APS is the relevant enterprise benchmark for translation and mixed-format viewing. Autodesk confirms that current major Revit support in Model Derivative tracks Revit 2023 through Revit 2026, while older versions stay in maintenance mode.

### Composite Revit Translation Claim

**Verdict: CONFIRMED.**
Composite RVT translation in APS Model Derivative requires packaging the host and linked RVT files into ZIP and using `compressedUrn` plus `rootFilename`. Autodesk explicitly states that the generic references endpoint does not support RVT in this scenario.

---

## 3. Competitor Benchmark Verdicts

### Solibri

**Verdict: CONFIRMED.**
Solibri remains the benchmark for deep rule-based QA, IDS and COBie checking, and high-trust model auditing.

### Navisworks

**Verdict: CONFIRMED.**
Navisworks remains the benchmark for federation, clash detection, 4D/5D coordination, and Autodesk-linked project delivery workflows.

### BIMcollab

**Verdict: CONFIRMED.**
BIMcollab remains the benchmark for BCF-centric issue lifecycle, open collaboration hub behavior, and authoring-tool roundtrip usability.

---

## 4. Repository Architecture Verification

### Nested Repository Boundary

**Verdict: CONFIRMED.**
`c:\plans\aerobim` is an isolated nested Git repository and should be treated as its own product boundary.

### Backend Layering

**Verdict: CONFIRMED.**
The current backend structure matches the intended five-layer split:

```text
backend/src/aerobim/
  core/
  domain/
  application/
  infrastructure/
  presentation/
```

### Domain Purity

**Verdict: CONFIRMED.**
The domain layer remains free of infrastructure imports.

### DI And Composition Root

**Verdict: CONFIRMED.**
The container, token registry, and bootstrap composition root are present and structurally consistent with the intended extraction strategy.

### Thin Entry Chain

**Verdict: CONFIRMED.**
The current startup path uses a single bootstrap container shared by app creation and runtime startup.

### Frontend And Plugin Status

**Verdict: DOCS-FIRST, NOT IMPLEMENTED.**
Frontend and Revit-plugin surfaces remain boundary definitions rather than active runtimes, which is consistent with the current delivery phase.

---

## 5. Corrected Findings Versus The Prior Audit

The earlier audit content in this repository had drifted behind the codebase. After direct file inspection:

### Path Traversal Finding

**Current verdict: NO LONGER REPRODUCES.**
`presentation/http/api.py` now resolves paths and rejects storage-boundary escapes with `is_relative_to()`.

### Double Bootstrap Finding

**Current verdict: NO LONGER REPRODUCES.**
`main.py` now uses a single module-level container for both app creation and runtime settings lookup.

### DI Unit-Test Presence

**Current verdict: PRESENT.**
`backend/tests/` contains unit tests for the container, extractor behavior, and the validation use case scaffold.

### Remaining Low-Signal Gaps

These remain real, but are not blockers for the current runtime phase:

- filesystem persistence is live, while `InMemoryAuditStore` remains a test-only fast path;
- the IDS path is live, wired, and now covered by a real sample-backed IFC+IDS end-to-end regression path;
- real drawing CV/PDF/DWG ingestion is still deferred behind the drawing port.

---

## 6. Corrected Architectural Conclusions

1. The canonical validation core should stay `IFC + IDS + report/export`, not `viewer + plugin` first.
2. Python remains the correct backend choice because the strongest IFC and document-processing tooling is Python-first.
3. The browser review surface should stay TypeScript-first, with `web-ifc` as the default parsing substrate.
4. xeokit is a valid performance-oriented viewer option, but its AGPL/commercial split makes it a deliberate licensing decision.
5. APS should remain an optional enterprise adapter for mixed-format viewing and Revit translation, not the core truth model.
6. The Revit surface should stay thin and orchestration-oriented.
7. SHACL and bSDD are important, but neither should displace IDS as the MVP rule language.
8. BIMserver and xBIM are strategically relevant adjacent tools, not required MVP foundations.

---

## 7. Current Skeleton Status

The repository is no longer docs-only. It now contains a small but live runtime slice, while most non-backend surfaces remain boundary-first.

### Existing Runtime Skeleton

- backend code scaffold already exists;
- frontend and plugin boundary surfaces remain docs-first.

### Active Placeholder And Boundary Surfaces

- `frontend/src/`
- `frontend/public/`
- `clients/revit-plugin/src/`
- `clients/revit-plugin/docs/`
- `clients/revit-plugin/resources/`
- `samples/ifc/`
- `samples/ids/`
- `samples/requirements/`
- `ops/`

Most of these remain placeholders. The backend runtime already contains the first multimodal analysis slice.

---

## 8. Evidence Gaps Kept Out Of SSOT

### Russian Regulatory Claims

**Status: NOT YET CANONICAL.**
Official Russian regulatory sources were not reliably retrievable in this environment during this pass. Therefore Russian TIM/BIM compliance claims must stay out of the canonical architecture docs until they are pinned to stable official sources.

### Deep Revit API Claims

**Status: PARTIAL.**
APS-side Revit translation evidence is strong. Deep desktop Revit API UI/graphics claims are still under-verified and should remain outside SSOT for now.

### Complexity And Performance Claims

**Status: DEFERRED.**
No exact complexity or throughput claims should be treated as canonical until sample packs and benchmark rails exist.

---

## 9. Second-Pass Audit (2026-04-09)

### Code vs Docs Alignment

All structural claims verified by direct file inspection.

| Claim | Verdict |
|---|---|
| Layer purity: domain imports only stdlib and domain models | ✅ CONFIRMED |
| DI container: 9 tokens, Container class, single composition root | ✅ CONFIRMED |
| Entry chain: `main.py → bootstrap_container() → create_http_app()` | ✅ CONFIRMED |
| Path traversal protection: `_resolve_safe_path` with `is_relative_to()` | ✅ CONFIRMED |
| Backend verification baseline | ✅ CONFIRMED — targeted backend suite currently passes (53 tests across 12 files) |
| Multimodal use case: narrative + drawing + IFC + remarks | ✅ CONFIRMED |
| Filesystem persistence | ✅ CONFIRMED — `FilesystemAuditStore` is the live bootstrap default; `InMemoryAuditStore` is kept for fast tests |
| IDS validation path | ✅ CONFIRMED — live `IfcTesterIdsValidator` exists and is wired through bootstrap |
| Real PDF/DWG CV analysis | ❌ NOT YET — current drawing path is structured text/JSON baseline |
| Clash detection | ✅ PORT + ADAPTER — `ClashDetector` port + `IfcClashDetector` adapter wired via DI; graceful fallback when `ifcclash` not installed |
| BCF export | ✅ CONFIRMED — `export_bcf()` produces valid BCF 2.1 ZIP archives; endpoint at `/v1/reports/{id}/export/bcf` |

### Naming Adjustment

The runtime now exposes `StructuredRequirementExtractor` as the canonical class and preserves `DoclingRequirementExtractor` as a compatibility alias. This resolves the earlier naming drift without breaking imports.

### Coverage Gap

Coverage now includes narrative synthesis, drawing annotation parsing, container behavior, IDS result mapping, real IDS+IFC end-to-end regression (property + quantity + multi-entity), filesystem persistence, report-listing API behavior, path traversal API protection, project-package use case, HTML export, BCF export, malformed-input rejection, calculation source flow, and clash detection port wiring. Missing: malformed drawing JSON, live PDF/DWG CV ingestion, and IfcClash integration-level testing with real geometry clashes.

### Scope Gap vs Task Requirements

The competition task (2026-04-09 brief) requires capabilities beyond the current IFC/IDS property-checking kernel:

- 2D drawing analysis (PDF/DWG ingestion and geometric extraction);
- cross-document comparison (project docs vs working docs vs TZ vs calculations);
- dimension and area verification;
- collision detection in BIM models;
- problem zone highlighting with spatial context;
- structured remark generation for designers.

These capabilities now exist as explicit domain models, ports, adapters, and one live project-package analysis use case, but the current baseline is still intentionally limited:

- narrative requirements use regex-backed synthesis rather than an external LLM;
- drawing analysis consumes structured annotations rather than live PDF/DWG CV;
- remark generation is template-based rather than model-authored;
- clash detection remains an upcoming adapter.

## 10. Recommended Next Moves

1. Add a small license matrix for `IfcOpenShell`, `IfcTester`, `xBIM IDS`, `BIMserver`, `web-ifc`, and `xeokit`.
2. Define the canonical requirement DSL and its provenance fields before implementing richer extraction.
3. Add sample packs under `samples/requirements`, `samples/ids`, and `samples/ifc` before making any performance claims.
4. Decide whether the first viewer rail is `web-ifc` only or `web-ifc + xeokit` adapter-ready.
5. Keep Russian regulatory mapping as a separate research track until official citations are stable.
6. ~~Extend the new real IFC + IDS regression pack with quantity, multi-entity, and mixed-discipline variants.~~ ✅ DONE
7. ~~Add an HTML export surface and matching report-export tests, then extend the same report model into BCF mapping.~~ ✅ DONE (HTML + BCF)
8. Add a PDF/DWG drawing-analysis adapter behind the existing drawing port.
9. ~~Add clash detection behind a dedicated infrastructure adapter.~~ ✅ DONE (port + adapter + DI + graceful fallback)
10. Decide whether the filesystem store remains sufficient for the next phase or should be followed by tenant-aware database persistence.
11. Add real IfcClash integration tests once `ifcclash` geometry pipeline is available.
12. Add a 3D viewer rail (web-ifc + Three.js preferred over xeokit for licensing — see `08-license-matrix.md`).
