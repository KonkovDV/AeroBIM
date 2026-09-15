<!-- claims-lint: allow-file reason="Honest deployment ranges from code; not a vendor quote; GO; customer_go false" -->
---
title: "Deployment sizing and cost 2026"
status: active
version: "1.0.0"
date: "2026-09-15"
last_updated: "2026-09-15"
claim_boundary: >
  Engineering ranges from Settings and the IFC LRU ceiling. Not a commercial
  quote, not customer SLA, not a 152-FZ opinion. Checkpoint GO; customer_go false.
---

# Deployment sizing and cost (honest ranges)

Not a price list. Not a VM SKU. Product Checkpoint **GO** (`regulatory_measurement_mvp`); `customer_go` **false**.

## What the code actually caps

| Surface | Default / formula | Source |
|---|---|---|
| IFC in-memory open | 256 MiB (`AEROBIM_MAX_IFC_BYTES`) | `Settings.max_ifc_bytes` |
| Process-local IFC LRU | 8 models × 256 MiB ≈ 2 GiB RAM ceiling | `ifc_file_open` / `export_ifc_cache_ram_ceiling` |
| Ingest envelope | 256 MiB default; customer-stated 1.5 GiB model / 500 MiB office under pilot when applied | `max_model_bytes` / `max_office_bytes` |
| Object store | `AEROBIM_STORAGE_DIR` (default `var/reports`) | Filesystem or S3 extra |
| Job runner | FastAPI `BackgroundTasks` in the API process | JOB-01; durable workers **not claimed** |
| IFC process isolate | Not claimed this pass | Honesty: in-process IfcOpenShell; child-process isolate is P1.7 residual |

Measured RSS delta for a federated pack is **null** until measured. Do not treat the 2 GiB LRU ceiling as a VM quote.

## People (not a Gantt)

Operator FTE for a fixture/pilot contour: **2 engineers + 0.5 HITL**. That is a staffing sketch, not a signed SOW.

Backlog lives in **GitHub Issues**, not a Gantt chart in this tree.

## Cost posture (build vs buy)

- Own code: MIT.
- Runtime: IfcOpenShell/IfcTester stay behind infrastructure/tools (LGPL).
- Optional `pdf-agpl` (PyMuPDF) is **not** in default extras or `requirements-lock.txt`.
- IDS profile of an appointing party is **data**, not a core fork.

No line here is a customer SLA of ≤30 minutes. Fixture `representative_scale` is an inventory flag on a public XSD-backed pack, not the appointing-party комплект.
