---
title: "AeroBIM TZ Compliance Matrix 2026"
status: active
version: "1.1.2"
last_updated: "2026-07-11"
tags: [aerobim, tz, compliance, mvp]
---

# TZ Compliance Matrix — Expert Assistant MVP

SSOT mapping of the **intellectual expert-assistant TZ** / **TechLab Samolet Task 07** onto AeroBIM.
Companion: [`samolet-techlab-alignment-2026.md`](../samolet-techlab-alignment-2026.md) (R1–R15).
Task 07 readiness: [`../partners/TECHLAB_TASK_07_READINESS_2026.md`](../partners/TECHLAB_TASK_07_READINESS_2026.md).
Architecture TBD fill: [`TZ_ARCHITECTURE_REQUIREMENTS_2026.md`](TZ_ARCHITECTURE_REQUIREMENTS_2026.md).

**Status legend:** `done` | `partial` | `missing`  
**Phase legend:** `MVP` (sign-off deterministic) | `P0`–`P4` (implementation waves)

## 1. Terms (OCR / CV / NLP / BIM)

| Term | TZ meaning | AeroBIM mapping | Status | Phase |
|------|------------|-----------------|--------|-------|
| OCR | Image/PDF → editable text | `RasterDrawingAnalyzer` (PyMuPDF + RapidOCR) | partial | MVP baseline / P2 deepen |
| Computer Vision | Interpret drawings like a human | Not in sign-off; planned advisory layout CV | missing | P2 advisory |
| NLP | Understand / generate language | Regex + pipe extractors; LLM stub advisory only | partial | MVP deterministic / P3 advisory |
| BIM model | Geometry + attributes | IFC via IfcOpenShell + IDS | done | MVP |

## 2. Concept — expert assistant (not replacement)

| Requirement | Status | Module / evidence | Phase |
|-------------|--------|-------------------|-------|
| Analyze 2D drawings + BIM | partial | Structured/OCR drawings + IFC validators | MVP |
| Compare PD/RD vs calcs, TZ, sections, norms | partial | Cross-doc + JSON norm-pack loader + deterministic section-pair scaffold; customer pack/pair TBD | MVP / P1 |
| Detect clashes, calc errors, inconsistencies | partial | IfcClash + cross-doc + quantity compare | MVP |
| Highlight errors, severity, generate remarks | partial | `problem_zone`, severity, `TemplateRemarkGenerator` | MVP / P0 UI |
| Expert remains accountable | done | Claim boundary + HITL review-events | MVP |

## 3. Target tasks

### 3.1 Graphic analysis

| Requirement | Status | Module | Phase |
|-------------|--------|--------|-------|
| Vector 2D drawings | partial | Structured TXT/JSON; PDF text blocks — not CAD entities | P2 DWG/DXF |
| Scanned 2D drawings | partial | RapidOCR baseline | MVP / P2 |
| BIM geometry + attributes | done | IfcOpenShell, IDS, schema pre-gate | MVP |
| Extract objects | partial | IFC entities; no CV symbol detection | MVP / P2 |
| Extract dimensions | partial | IFC quantities + drawing annotations | MVP |
| Extract text annotations | partial | Structured / OCR regions | MVP |

### 3.2 Compliance analysis

| Requirement | Status | Module | Phase |
|-------------|--------|--------|-------|
| vs calculation results | partial | Cross-doc + OpenRebar provenance | MVP |
| vs design brief (TZ) | done | Narrative + structured requirements | MVP |
| sections vs sections | partial | `SectionDiffAnalyzer`: canonical PD↔RD pairing (RU/EN discipline + canonical-key registries, AR+KZH fixtures, SI tolerance, provenance, coverage in capability); customer pair/parser + canonical-key freeze TBD | P1 scaffold hardened 2026-07-11 |
| vs norms / design rules | partial | IDS + `NormRulePackLoader` + 20-rule synthetic AR template; manifest/env customer path (`AEROBIM_NORM_RULE_PACK`) with fail-closed capability + CI schema gate; approved customer pack still missing | MVP / P1 hardened 2026-07-11 |

### 3.3 Error detection

| Requirement | Status | Module | Phase |
|-------------|--------|--------|-------|
| MEP / system intersections | missing | Generic clash only; explicit gap [`MEP-CLASH-001`](../roadmap/MEP_SYSTEM_CLASH_GAP_2026_07.md) | P1 customer corpus / roadmap |
| Geometric BIM conflicts | partial | `IfcClashDetector` + `SPATIAL-*` | MVP |
| Calculation / load errors | partial | Cross-doc numeric; not full structural solver | MVP |
| Incorrect areas | partial | Space area rules + quantity algebra | MVP |
| Inefficient space use | missing | No utilization analytics | P4 (if metric agreed) |
| Section inconsistency | partial | Cross-doc + deterministic PD↔RD canonical section pairing (multi-discipline RU/EN, canonical keys, fail-closed on ambiguity) | MVP / P1 |
| Missing elements | partial | IDS `exists` / property checks | MVP |
| Dimension mismatches | done | Drawing↔IFC + property compare | MVP |

### 3.4 Expert support

| Requirement | Status | Module | Phase |
|-------------|--------|--------|-------|
| Highlight problem zones on drawing | done | `ProblemZone` + `DrawingEvidencePanel` | MVP |
| Generate remark text | done | RU/EN templates (`AEROBIM_REMARK_LOCALE`) | MVP / P0 |
| Edit comments | done | API + frontend remark editor → `edited_remark` | P0 |

## 4. Functionality

| Requirement | Status | Module | Phase |
|-------------|--------|--------|-------|
| Upload MS Office | partial | Optional Docling path; multipart upload for binaries | P0 done / Docling optional |
| Upload PDF | partial | Path-based + raster + `POST /v1/uploads` | P0 |
| Upload DWG | missing | — | P2 |
| Upload BIM (IFC) | done | Path-based + multipart upload | MVP / P0 |
| Auto analysis + report | done | `AnalyzeProjectPackageUseCase` + JSON/HTML/BCF | MVP |
| Version / doc-type compare | partial | ISO 19650-lite fields; no full version diff | P1 |
| CV for drawings | missing | Advisory roadmap | P2 |
| OCR for text | partial | Raster baseline | MVP |
| NLP for TZ / remarks / anomalies | partial | Regex NLP; LLM advisory stub; EN/RU templates | MVP / P3 |
| Clash / anomaly algorithms | partial | IfcClash deterministic | MVP |
| Web UI | done | `frontend/` review shell | MVP |
| Drawing overlay of errors | done | `DrawingEvidencePanel` | MVP |
| Remarks panel: list / filter / priority / edit | done | Severity filter + remark editor → review-events | P0 |

## 5. Data sources and constraints

| Item | Status | Notes |
|------|--------|-------|
| 2D drawings | partial | Fixtures + OCR; customer PDFs via intake |
| BIM models | done | IFC packs |
| TZ RU/EN | done | RU narrative + EN structured corpus |
| Company standards | partial | IDS / rule packs; customer corpus TBD |
| Scan vs vector quality | acknowledged | Capability status + claim boundary |
| Unstructured data | acknowledged | Deterministic extractors + HITL |
| Limited training data | acknowledged | No ML sign-off; F1 on fixtures |
| Style variation | acknowledged | IAA protocol + agreed packs |

## 6. Evaluation criteria (TZ)

| TZ criterion | Pilot / repo target | Status | Phase |
|--------------|---------------------|--------|-------|
| Clash accuracy >90% | Measured precision after labeled corpus; pilot TP ≥60% interim | partial (harness + protocol; not measured on customer corpus) | P1 harness done / P4 publish |
| Calc error detection | Cross-doc + OpenRebar on agreed pack | partial | MVP |
| Inconsistency accuracy >90% | Same adjudication path as clash | partial (harness + protocol; not measured on customer corpus) | P1 harness done / P4 publish |
| Remark quality RU/EN | RU templates live; EN P0; human edit HITL | partial | P0 |
| Model accuracy / stability | pytest + capabilities fail-closed | done | MVP |
| Scalability | Jobs + optional Redis/Postgres/S3 | partial | MVP foundation |
| UI usability | Review shell; remarks panel P0 | partial | P0 |
| Package ≤30 min | `measure_package_sla` on **agreed** pack | done (fixture); customer TBD | MVP |
| Cognitive load reduction | Priority profile + HITL KPI | partial | P0 |

**Honesty rule:** do not claim >90% in public materials until adjudication evidence exists. See [`../pilot-claim-boundary-2026.md`](../pilot-claim-boundary-2026.md) and Claims Lock.

## 7. Appendices (data)

| Appendix | Repo location | Status |
|----------|---------------|--------|
| 1 Project documentation | [`samples/tz-appendix/01-project-docs/`](../../samples/tz-appendix/01-project-docs/) | skeleton |
| 2 Working documentation | [`samples/tz-appendix/02-working-docs/`](../../samples/tz-appendix/02-working-docs/) | skeleton |
| 3 Standards | [`samples/tz-appendix/03-standards/`](../../samples/tz-appendix/03-standards/) + `samples/ids/` | partial |
| 4 Design brief | [`samples/tz-appendix/04-design-brief/`](../../samples/tz-appendix/04-design-brief/) + `samples/specifications/` | partial |
| 5 Typical errors | Catalog JSON ≥20 patterns + mapping tool; customer confirmation = 0 | partial (synthetic scaffold) |
| 6 Calculations | [`samples/tz-appendix/06-calculations/`](../../samples/tz-appendix/06-calculations/) + `samples/calculations/` | partial |

Manifest: [`samples/tz-appendix/MANIFEST.json`](../../samples/tz-appendix/MANIFEST.json).

## 8. Implementation wave summary

| Phase | Focus |
|-------|-------|
| **MVP** | Deterministic IFC/IDS/cross-doc/clash + OCR baseline + templates + browser review |
| **P0** | Multipart upload, remarks UI (list/filter/edit), EN remarks |
| **P1** | Norm packs, section pairing, detection precision harness — engineering scaffolds landed; customer pack/corpus still required |
| **P2** | DXF/DWG thin adapter, OCR deepen, CV advisory |
| **P3** | LLM remarks / IDS assist advisory + HITL |
| **P4** | Customer corpus → publish precision; optional space-efficiency |

## Drawing AI posture (retained local SSOT)

July 2026: [../evidence/DRAWING_AI_WORLD_PRACTICE_2026_07.md](../evidence/DRAWING_AI_WORLD_PRACTICE_2026_07.md).
