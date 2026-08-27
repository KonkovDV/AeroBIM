<!-- claims-lint: allow-file reason="IFC streaming/disk R-tree design; 1.5GB ingest ≠ analyze cap; NO_GO" -->
---
title: "IFC streaming and disk R-tree design"
date: "2026-08-27"
last_updated: "2026-08-27"
status: active
version: "1.0.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Design note only. Streaming parser and disk R-tree are not implemented.
  Default AEROBIM_MAX_IFC_BYTES stays 256 MiB. Stated 1.5 GB is ingest.
  In-memory IfcSpatialIndex is not a disk R-tree. Checkpoint NO_GO.
---

# IFC streaming / disk R-tree (design)

Machine: `python -c "from aerobim.domain.ifc_streaming_design import streaming_design_snapshot"`.

Checkpoint **`NO_GO`**. `raises_default_cap: false`.

## Today (do not re-sell as streaming)

Analyze opens the IFC with `ifcopenshell.open` and builds an in-memory `IfcSpatialIndex` (GUID, storey containment, `IfcGridAxis.AxisTag`). Process-local LRU cache is still full models. Default **`AEROBIM_MAX_IFC_BYTES` = 256 MiB**. Samolet-stated **1.5 GB** is the **ingest** envelope for model files, not analyze and not the WASM viewer.

## Intended next slice (not shipped)

1. Stream STEP entities instead of retaining the whole graph for every query.
2. Persist an AABB R-tree on disk keyed by GUID (broadphase only).
3. Measure RSS on a representative file **before** any default-cap change.
4. Owner override of the cap remains an explicit flag, never a silent raise.

## Forbidden speech

| Attack | Brake |
|---|---|
| Design doc = streaming shipped | `streaming_parser=designed_not_implemented` |
| In-memory index = disk R-tree | `disk_r_tree=designed_not_implemented` |
| 1.5 GB ingest = analyze default | `raises_default_cap=false` |

Does not close RT-001/002b/003. Does not parse RVT/NWD/LIRA.
