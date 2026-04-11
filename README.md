# Samolet

`Samolet` is an isolated nested repository for an openBIM and construction-document quality platform.

The project takes the architectural discipline of MicroPhoenix as its baseline, but deliberately extracts only the subset that is useful for a BIM / IFC / document QA product:

- layered architecture with strict boundaries
- explicit DI container and token registry
- bootstrap chain and composition root
- domain ports with infrastructure adapters
- request-scoped traceability and config isolation
- phase-driven delivery and verification

## Product Thesis

Construction and BIM teams need one workflow that can:

1. ingest technical specifications, calculations, drawings, and structured IDS packages;
2. compare 2D drawing evidence, narrative requirements, and IFC/BIM deliverables in one analysis path;
3. emit machine-readable findings and reviewer-friendly remarks with explicit provenance;
4. sync findings back into BIM tooling and issue-management loops.

`Samolet` is positioned as an open, composable quality kernel rather than another monolithic BIM desktop tool.

## What Was Extracted From MicroPhoenix

### Kept

- `core -> domain -> application -> infrastructure -> presentation`
- token-based DI instead of magic reflection
- explicit module bootstrap
- use-case orchestration instead of controller-heavy logic
- clear port/adapter seams for external libraries

### Deferred

- multi-agent orchestration
- full event sourcing / outbox
- MCP server estate
- plugin marketplace
- vector-memory and knowledge-graph subsystems

Those capabilities are valuable in MicroPhoenix, but they are not required for the first useful `Samolet` release.

## Documentation Entry Points

- `docs/README.md` — documentation router and reading order
- `docs/06-architecture-reference.md` — canonical architecture reference
- `docs/08-microphoenix-adoption-matrix.md` — exact extraction decisions from MicroPhoenix
- `docs/09-implementation-and-verification-rails.md` — how new work should be delivered and verified

## Selected External Stack

- IFC / openBIM: buildingSMART IFC, IDS, BCF
- IFC tooling: IfcOpenShell, IfcTester
- document parsing: Docling
- AI/CV-ready seams: local rule-synthesis and drawing-analysis baselines with future LLM/VLM adapters
- browser viewer surface: web-ifc and APS Viewer patterns
- authoring-side workflow: thin Revit add-in / BIM plugin surface

## Repository Layout

```text
samolet/
├── backend/                 # Python backend with extracted MicroPhoenix patterns
├── clients/revit-plugin/    # Thin authoring-side client boundary
├── docs/                    # Plan, extraction dossier, research landscape, atomic backlog
├── ops/                     # Environment and runtime notes
├── samples/                 # IFC, IDS, drawing, spec, and calculation fixtures
└── frontend/                # Planned review UI and browser viewer surface
```

## Current Deliverables

- isolated nested Git repository
- deep plan and atomic backlog
- MicroPhoenix extraction dossier
- MicroPhoenix adoption matrix and delivery rails
- openBIM / OSS / competitor research package
- backend multimodal MVP scaffold with tests
- project-package analysis flow for narrative rules, drawing annotations, IFC checks, and generated remarks

## Near-Term Delivery Sequence

1. harden the multimodal backend kernel around richer fixtures, persistence, and IDS/clash adapters;
2. add report export surfaces (`json`, `html`, `bcf`);
3. add browser review experience with 2D overlays and BIM highlighting;
4. add Revit-side issue roundtrip;
5. add CDE / BCF / openCDE interoperability.
