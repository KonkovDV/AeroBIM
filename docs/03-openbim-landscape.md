---
title: "OpenBIM Landscape, Algorithms, Protocols, And Competitive Frame"
status: active
version: "0.2.0"
last_updated: "2026-04-08"
tags: [samolet, landscape, reference, openbim]
---

# OpenBIM Landscape, Algorithms, Protocols, And Competitive Frame

## Standards Baseline

## IFC

IFC is the canonical vendor-neutral data model for the built environment and remains the core exchange format for `Samolet`.

Key implications for the product:

- the product must reason over entities, properties, relationships, and GUIDs;
- validation cannot be limited to geometry only;
- archive and exchange scenarios matter as much as point-in-time checking.

## IDS

IDS is the most important requirement-expression standard for the first `Samolet` release.

Why it matters:

- it expresses machine-checkable requirements for IFC data delivery;
- it is explicitly designed for automated compliance checking;
- it gives the product a portable contract surface instead of locking the rule model into an internal format.

Product implication:

`Samolet` should treat IDS as a first-class input, not a later add-on.

## bSDD

bSDD is the shared terminology and classification service in the buildingSMART stack.

Why it matters:

- it provides interoperable dictionaries and controlled vocabularies;
- it helps align terms across IFC, IDS, and discipline-specific taxonomies;
- it can enrich requirement normalization with canonical identifiers.

Product implication:

`Samolet` should treat bSDD as a terminology and enrichment adapter, not as the primary rule language.

## BCF

BCF is the issue and collaboration transport layer.

Why it matters:

- it carries issue context, screenshots, viewpoints, and IFC GUID references;
- it exists both as file exchange (`.bcfzip`) and as a REST-style API pattern;
- it is the shortest path from validation findings to coordination workflow.

Product implication:

`Samolet` findings should be mappable to BCF topics, even before full BCF API support lands.

## SHACL

SHACL is a W3C Recommendation for validating RDF graphs against shapes.

Why it matters:

- it is relevant if `Samolet` later materializes requirements, classifications, or graph-shaped provenance into RDF;
- it can express graph constraints and validation reports in semantic-data workflows;
- it is useful for a semantic overlay, not for native IFC/IDS execution.

Product implication:

`Samolet` should not treat SHACL as the primary MVP validation language. For the first release, IFC plus IDS stay primary; SHACL remains an optional semantic extension surface.

## OpenCDE / buildingSMART APIs

The buildingSMART technical surface explicitly links BCF to the Foundation API and Documents API.

Why it matters:

- issue exchange without CDE interoperability caps product reach;
- long-term integration should align with standard issue, document, and identity flows rather than custom one-off connectors.

Product implication:

`Samolet` should keep interop surfaces adapter-driven from day one.

## External OSS Stack

## IfcOpenShell

IfcOpenShell is the foundational open-source IFC runtime.

What it provides:

- IFC parsing and model access;
- Python and C++ surfaces;
- surrounding utilities for BCF, diffing, clash, testing, FM, and more.

Why it fits `Samolet`:

- it is the deepest open-source IFC substrate available;
- it keeps the core validation kernel out of proprietary runtime lock-in.

## IfcTester

IfcTester is the shortest route from IDS to actual model validation.

What it provides:

- author/read IDS files;
- validate IFC against IDS;
- output reports to console, JSON, HTML, ODS, and BCF.

Why it fits `Samolet`:

- it can serve as the standards-aligned validation engine while the broader product workflow remains product-specific.

## xBIM

xBIM is the strongest .NET-native openBIM toolkit in the current evidence package.

What it provides:

- IFC model access for .NET runtimes;
- support for IFC2x3, IFC4, and IFC4x3 in xBimEssentials;
- an IDS validation library through `Xbim.IDS.Validator`.

Why it fits `Samolet`:

- it is the natural .NET-side counterpart for thin authoring-tool integrations;
- it can support plugin-side read, lookup, and issue-context workflows without moving core validation into Revit.

Constraint to remember:

- the IDS validator is AGPL-licensed, so it must remain an explicit licensing decision, not an accidental dependency.

## BIMserver

BIMserver is the mature open-source server-side reference for IFC storage, versioning, and object-level model management.

What it provides:

- IFC object storage instead of plain file storage;
- model query, merge, filtering, and versioning workflows;
- a server-centric integration surface for openBIM collaboration.

Why it matters:

- it is useful as a benchmark and potential interop/storage adapter;
- it shows what a model-centric IFC backend can look like if `Samolet` later grows beyond report-centric persistence.

Constraint to remember:

- BIMserver is AGPL-licensed and is far broader than the MVP kernel, so it should remain optional.

## Docling

Docling is the document-to-structured-representation engine.

What it provides:

- multi-format document parsing;
- advanced PDF understanding;
- structured export formats;
- local execution path for sensitive environments.

Why it fits `Samolet`:

- narrative requirement packs and annexes often arrive as PDFs, DOCX, and mixed office documents;
- `Samolet` needs a deterministic preprocessing step before rule normalization.

## web-ifc

web-ifc is the browser-side IFC engine.

What it provides:

- high-speed IFC reading in browser/Node;
- WASM-based runtime;
- direct geometry and property access.

Why it fits `Samolet`:

- it enables a browser review surface without requiring a heavyweight proprietary viewer;
- it is a strong default for issue lookup and object navigation in the review UI.

## xeokit

xeokit is the high-performance browser viewer reference point for large BIM and AEC scenes.

What it provides:

- production-proven WebGL toolkit for federated BIM viewing;
- BCF viewpoint save/load support;
- double-precision rendering and optimized XKT pipeline for large models.

Why it matters:

- it is a serious alternative to building the full viewer stack around raw `web-ifc` primitives;
- it is especially relevant if `Samolet` needs large-model performance, federated scenes, and rich viewer plugins.

Constraint to remember:

- xeokit open-source use is AGPL-3.0, with proprietary licensing available separately.

## APS Viewer And Model Derivative

APS defines the enterprise-grade viewer and translation reference point.

What it provides:

- hosted SDK for multi-format design viewing;
- property querying, extension framework, aggregated views, and enterprise translation paths through Model Derivative.

Why it matters even if not used first:

- it is a strong benchmark for viewer UX expectations;
- it may become necessary in mixed-format enterprise deployments;
- Autodesk confirms active Revit translation support for current major versions in Model Derivative, and composite RVT translation requires ZIP packaging plus `compressedUrn` and `rootFilename` rather than direct RVT reference linking.

## Revit-Side Boundary

The Revit-side surface should stay intentionally thin.

Why:

- viewer, translation, and validation gravity should remain server-side and web-side;
- plugin logic should focus on authentication, issue pull, object focus, and status pushback;
- exact deep Revit API claims remain a research thread until they are verified from stable Autodesk documentation.

## Protocol And Dataflow Stack

The target protocol chain is:

1. `document / ids input`
2. `requirement normalization`
3. `IFC validation`
4. `finding persistence`
5. `BCF / JSON / HTML output`
6. `review UI`
7. `authoring-side roundtrip`
8. `openCDE integration`

This chain should stay modular. No layer should need to know every transport or every file format.

## Core Algorithms And Work Units

## A. Requirement Normalization

Input sources:

- IDS XML;
- narrative specification text;
- later PDF / DOCX packages.

Atomic steps:

1. parse source;
2. segment into candidate obligations;
3. map to entity / property / value / cardinality form;
4. assign stable rule identifiers;
5. preserve provenance.

## B. IFC Evaluation

Atomic steps:

1. load IFC model;
2. resolve applicable entity sets;
3. inspect property sets and properties;
4. compare actual vs expected values;
5. produce issue objects with evidence.

## C. IDS Evaluation

Atomic steps:

1. load IDS package;
2. run standards-aligned validation path;
3. normalize engine output into domain findings;
4. preserve rule identifiers and provenance;
5. merge results with report summary semantics.

## D. Issue Materialization

Atomic steps:

1. classify severity;
2. attach entity GUID and requirement ID;
3. group repeated failures;
4. generate reviewer-ready messages;
5. emit export formats.

## E. Coordination Loop

Atomic steps:

1. convert issue to BCF-ready topic;
2. surface it in browser review;
3. sync into authoring tool;
4. collect comments / statuses;
5. re-run validation and close the loop.

Complexity note:

`Samolet` should avoid hard asymptotic performance claims in its architecture package until they are backed by benchmark packs on representative IFC and IDS datasets.

## Competitive Landscape

## Solibri

Market position:

- model-checking leader;
- deep ruleset and QA/checking maturity;
- strong support for IDS, COBie, code compliance, and domain-heavy QA use cases.

Takeaway:

This is the benchmark for rule depth and trust.

## Navisworks

Market position:

- model federation, clash detection, 4D/5D workflows, preconstruction coordination;
- strong Autodesk ecosystem gravity;
- ACC-linked issue workflow.

Takeaway:

This is the benchmark for coordination and construction-facing workflow integration.

## BIMcollab

Market position:

- issue lifecycle and BCF collaboration hub;
- plugin presence inside Revit, Navisworks, and other tools;
- strong bridge between issue data and authoring context.

Takeaway:

This is the benchmark for issue roundtrip and authoring-side usability.

## Samolet Positioning

`Samolet` should not try to out-Solibri Solibri or out-Navisworks Navisworks.

The differentiated position is:

- open and composable core;
- standards-first validation (`IFC + IDS + BCF`);
- stronger extraction and normalization of requirement documents;
- architecture that supports automation and selective productization rather than a closed desktop suite.

## Publications And Reference Material

The current evidence base already points to a concrete reading stack:

1. `IFC / ISO 16739-1:2024` for canonical model semantics.
2. `IDS 1.0` buildingSMART final standard materials and implementer docs.
3. `BCF XML / BCF API` repositories and technical guidance.
4. `Docling` documentation and paper trail (`arXiv:2408.09869`).
5. `SmolDocling` and the DocTags representation work (`arXiv:2503.11576`).
6. `IfcOpenShell / IfcTester` implementation documentation.
7. `xBIM`, `BIMserver`, `web-ifc`, `xeokit`, and APS official surfaces.

## Research Backlog Still Worth Closing

The current project package is already deep enough to start building, but the following research threads should be expanded next:

- regulatory automated code-checking literature;
- graph-based rule dependency models for BIM validation;
- issue deduplication and conflict clustering for multi-discipline models;
- Revit add-in UX patterns for issue triage at scale;
- openCDE implementation details beyond BCF-only workflows.

## What Should Not Be Overclaimed Yet

- Russian regulatory mapping should not be embedded into the canonical architecture until official sources are pinned and reviewed;
- exact Revit API rendering and graphics-mechanics claims should stay out of SSOT until verified from Autodesk references;
- benchmark or complexity claims should remain provisional until the project has sample packs and repeatable measurements.

## Immediate Product Conclusions

1. IDS must be a primary interface, not an afterthought.
2. IfcOpenShell + IfcTester is the shortest credible open validation path.
3. bSDD is a terminology-enrichment surface, not the main rule engine.
4. SHACL is an optional semantic-validation layer, not the MVP constraint language.
5. Docling should feed rule normalization, not directly decide compliance.
6. BCF is the operational issue-transport layer.
7. `web-ifc` is the right default browser-side parsing substrate; `xeokit` is the serious high-performance viewer alternative.
8. proprietary viewers and enterprise APIs remain optional adapters, not core truth.
