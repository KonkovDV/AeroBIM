<!-- claims-lint: allow-file reason="IFC streaming/disk R-tree design; RocksDB over SPF cap; WASM 256 MiB; NO_GO" -->
---
title: "IFC streaming and disk R-tree design"
date: "2026-08-27"
last_updated: "2026-08-30"
status: active
version: "1.3.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Design note. Streaming parser and disk R-tree are not implemented.
  Default AEROBIM_MAX_IFC_BYTES stays 256 MiB SPF. Files up to 1.5 GB
  use IfcOpenShell RocksDB. WASM stays 256 MiB. In-memory IfcSpatialIndex
  is not a disk R-tree. Checkpoint GO; customer_go false.
---

# IFC streaming / disk R-tree (design)

Machine: `python -c "from aerobim.domain.ifc_streaming_design import streaming_design_snapshot"`.

Checkpoint **`GO`**; `customer_go` false. `raises_default_cap: false`. `rocksdb_backend: wired_over_spf_cap`.

## Today

- **SPF** (`analyze_ok`): `ifcopenshell.open(.ifc)` + dense in-memory `IfcSpatialIndex` (`IfcRoot`). Cap: **256 MiB**.
- **RocksDB** (`analyze_disk`): streaming `convert_path_to_rocksdb`, then `open(rdb)`. Sparse index (`IfcProduct` + storey/grid). Cap: **1.5 GB** under Samolet ingest.
- Optional JSON sidecar is a dump of that index (`spatial_index_json_sidecar=dump_only`). It is **not** a disk R-tree and is **not** a streaming parser. WASM stays **256 MiB**.

## Intended next slice (not shipped)

1. Persist an AABB R-tree on disk keyed by GUID (broadphase only).
2. Stream STEP entities instead of retaining the whole graph for every query (`stream2` is not the analyze path).
3. OA-16 RSS on a local over-SPF file via RocksDB (owner-local; do not raise the SPF default).
4. Owner override of the SPF cap remains an explicit flag, never a silent raise.

## Forbidden speech

| Attack | Brake |
|---|---|
| Design doc = streaming shipped | `streaming_parser=designed_not_implemented` |
| In-memory index / JSON sidecar = disk R-tree | `disk_r_tree=designed_not_implemented`; sidecar `dump_only` |
| 1.5 GB = SPF `open(.ifc)` / WASM | `raises_default_cap=false`; WASM 256 MiB; RocksDB is the 1.5 GB path |

Does not close RT-001/002b/003. Does not parse RVT/NWD/LIRA.
