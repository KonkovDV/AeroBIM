---
title: "AeroBIM Fact-Check And Corrected Architecture Audit"
status: active
version: "0.5.0"
last_updated: "2026-04-12"
tags: [aerobim, audit, evidence, architecture]
---

# AeroBIM Fact-Check And Corrected Architecture Audit

Date: 2026-04-12

Evidence sources: direct repository inspection of `README.md`, `docs/**`, backend composition root, HTTP API, domain contracts, use cases, tests, fixture packs, and ops surfaces, plus official buildingSMART IDS and BCF pages, the W3C SHACL Recommendation, and the IfcOpenShell project site.

## 1. Standards Verdicts

### IFC / IfcOpenShell

**Verdict: CONFIRMED.**
IfcOpenShell continues to present itself as the open-source IFC toolkit and geometry engine. `AeroBIM` is correctly built around IFC as the canonical model substrate rather than around a vendor viewer.

### IDS

**Verdict: CONFIRMED.**
buildingSMART continues to position IDS as the machine-readable contract and validation surface for model-based exchange requirements. `AeroBIM` is correct to keep IDS as the primary portable requirement language.

### BCF

**Verdict: CONFIRMED.**
buildingSMART continues to position BCF as the issue transport surface for model-based topics, with both file-based and REST-style exchange modes. `AeroBIM` is correct to treat BCF as the coordination/export layer.

### SHACL

**Verdict: CONFIRMED WITH A BOUNDARY.**
SHACL remains a W3C Recommendation for RDF graph validation. It is suitable as a future semantic overlay or graph-validation layer, but it is not a reason to displace IFC + IDS in the current kernel.

## 2. Repository-State Verdicts

### Nested Product Boundary

**Verdict: CONFIRMED.**
`c:\plans\samolet` is the product boundary being audited here and should be treated independently from the parent workspace.

### Five-Layer Backend

**Verdict: CONFIRMED.**
The Python backend still follows the extracted five-layer split:

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
Domain contracts remain independent of infrastructure imports, and boundary rules are covered by layer tests.

### Composition Root

**Verdict: CONFIRMED.**
`bootstrap_container()` remains the single explicit wiring point for settings, adapters, and use cases.

### HTTP And Persistence Slice

**Verdict: CONFIRMED.**
The live backend exposes:

- `/health`
- `/v1/validate/ifc`
- `/v1/analyze/project-package`
- `/v1/reports`
- `/v1/reports/{report_id}/source/ifc`
- report export to `json`, `html`, and `bcf`

Filesystem-backed report persistence is the live default rather than a test-only placeholder.

### Frontend Status

**Verdict: ACTIVE INITIAL SPATIAL RUNTIME.**
The frontend is no longer docs-first only. It is now a real React/Vite review shell for:

- report listing;
- issue detail inspection;
- report-scoped IFC loading;
- issue-to-element and clash-pair highlight / isolate flow in the browser viewer;
- persisted drawing preview browsing with 2D problem-zone overlays;
- provenance inspection;
- HTML / JSON / BCF export actions.

What it still is not:

- a full persisted-report smoke harness for the full browser workflow;
- a full authoring-side coordination surface.

### Ops Status

**Verdict: ACTIVE.**
`ops/` now contains standalone bootstrap, environment, storage, and smoke guidance instead of placeholder-only notes.

### Revit Plugin Status

**Verdict: DOCS-FIRST.**
The authoring-side boundary remains intentionally thin and not yet implemented as an active runtime.

## 3. Capability Verdicts

| Capability | Current verdict | Notes |
|---|---|---|
| IFC property and quantity validation | ✅ LIVE | Backed by `IfcOpenShellValidator` and fixture-driven tests |
| IDS validation | ✅ LIVE | Backed by `IfcTesterIdsValidator` and end-to-end samples |
| Narrative rule synthesis | ✅ LIVE BASELINE | Deterministic regex-backed baseline, not LLM-first |
| Structured drawing annotation validation | ✅ LIVE | Active through drawing contracts |
| Deterministic PDF / OCR drawing extraction | ✅ LIVE BASELINE | PyMuPDF + RapidOCR path exists behind `VisionDrawingAnalyzer` |
| Geometry clash detection | ✅ LIVE WITH OPTIONAL EXTRA | Real IfcClash path requires `.[clash]`; graceful empty fallback without the extra remains an intentional limitation |
| JSON / HTML / BCF export | ✅ LIVE | Export endpoints and tests exist |
| Browser review shell | ✅ LIVE + INITIAL 3D/2D REVIEW | Report shell plus browser IFC selection and persisted drawing-evidence overlays |
| Thin Revit roundtrip | ❌ NOT YET | Boundary only |

## 4. Corrected Findings Versus Prior Documentation Drift

The previous active docs had drifted in three meaningful ways:

1. They understated the frontend and ops surfaces by describing them as placeholder-only.
2. They overstated a few runtime capabilities by not making optional-extras gating visible enough.
3. They still described the next milestone as if IDS, clash, and persistence were not already live.

This rebaseline corrects those mismatches.

## 5. Confirmed Risk Notes

### Optional Capability Gating Is Real

**Verdict: CONFIRMED.**
`.[vision]` is part of the common development lane, but `.[clash]` and `.[docling]` remain explicit extras. Active docs must say so clearly, otherwise runtime expectations become misleading.

### Clash Temp-Directory Cleanup Defect

**Verdict: FIXED IN THIS TRANCHE.**
During this rebaseline a real infrastructure defect was confirmed in `IfcClashDetector`: each run created a temporary output directory without cleanup. The adapter now uses `TemporaryDirectory()` and a regression test covers cleanup behavior.

## 6. Current Open Gaps

The remaining meaningful gaps are now product gaps, not architecture-foundation gaps:

- no real integration test that exercises `ifcclash` against fixture geometry with the optional extra installed;
- no benchmark/throughput rail or async job execution for larger models;
- no project-level metadata or tenant-aware report indexing;
- no active authoring-side roundtrip.

## 7. Interpretation

The correct academic reading of the repository is now:

`AeroBIM` is a deterministic multimodal BIM QA kernel with a live backend, a live persisted-report/export path, a report-scoped drawing preview contract, and initial browser 3D/2D spatial-review rails. It is not yet a full coordination ecosystem.