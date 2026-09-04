<!-- claims-lint: allow-file reason="Analyze SPF 256 MiB vs RocksDB 1.5 GB; bSI 256 MB; SPF RAM literature; NO_GO" -->
---
title: "IFC analyze cap vs ingest envelope"
date: "2026-08-30"
last_updated: "2026-09-04"
status: active
version: "1.1.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Four public numbers, four meanings. Default AEROBIM_MAX_IFC_BYTES stays
  256 MiB SPF in-memory. Files up to 1.5 GB (answers 1.1.4) open via
  IfcOpenShell RocksDB, not SPF RAM. WASM stays 256 MiB. Checkpoint GO; customer_go false.
---

# IFC: SPF 256 MiB; RocksDB до 1,5 ГБ

Machine: `python -c "from aerobim.domain.ifc_size_policy import size_policy_snapshot"`.
Probe: `python -m aerobim.tools.measure_ifc_open_rss --write-docs-evidence` (committed `samples/` only). The committed wall-pset fixture is 975 bytes; its RSS delta is **import noise**, not an SPF×10 measurement (`tiny_fixture_rss_delta_is_import_noise`).

Checkpoint **`GO`**; `customer_go` false. `raises_default_cap: false`. `rocksdb_backend: wired_over_spf_cap`.

## Four numbers

| Number | Bytes | Unit | What it governs | Source retrieved 2026-08-30 |
|---|---:|---|---|---|
| SPF in-memory | 268 435 456 | 256 **MiB** | `ifcopenshell.open(.ifc)` | `AEROBIM_MAX_IFC_BYTES` |
| bSI Validation Service | 256 000 000 | 256 **MB** | Public uncompressed `.ifc` upload | [User guide](https://buildingsmart.github.io/validate/user/index.html); UI «256mb max» |
| WASM viewer | 268 435 456 | 256 **MiB** | `web-ifc` `MEMORY_LIMIT` | `frontend/src/lib/ifc-scene.ts` |
| Disk analyze / ingest | 1 500 000 000 | 1,5 **GB** decimal | HTTP 413 over this; RocksDB convert then `open(rdb)` under `samolet_pilot`/`production` | Answers 1.1.4 (25.08) |

256 MiB − 256 MB = 12 435 456 bytes. A file can pass AeroBIM SPF analyze and fail bSI. Neither number is 1,5 ГБ.

The bSI **FAQ heading** on buildingsmart.org still says “250 MB limit”; the **user guide** (v0.8.4, retrieved 2026-08-30) is **256 MB** uncompressed `.ifc`. Classification in git uses the user-guide figure (`256_000_000`). The UI upload line is «256mb max». Do not treat FAQ 250, guide 256, and our 256 **MiB** as one number.

## Why the SPF default is not raised

IfcOpenShell #7116 (aothms, 2025-09-11, closed): SPF parse of a ~275–300 MB model is **roughly 10× disk in RAM**; the published 275 MB Riverside open was **2,19 GiB RSS** (~8×). Planning multiplier in git is **10**, labelled literature, not our measurement.

Secondary literature, same family: IfcOpenShell #2025 — even a **streaming** open of a ~245 MB file still held **~1.4 GB** in Python id/class/inverse maps. That is why 1,5 ГБ uses **RocksDB**, not `open(.ifc)`.

| File on disk | Literature SPF RSS (×10) |
|---|---|
| 256 MiB SPF cap | ~2,5 GiB |
| 1,5 GB if SPF-opened | ~15 GiB |
| LRU 8 × SPF cap (file-bytes ceiling 2 GiB) | ~20 GiB RSS literature |

`ifc_cache_ram_ceiling` remains **file bytes × 8 models = 2 GiB of 256 MiB slots**. That is not RSS and not 8 × 1.5 GB. `measured_rss_delta_bytes` stays null until OA-16 on a local over-SPF file.

Upstream RocksDB on the same ~275 MB file opened at **~11 MiB** vs **2,19 GiB** SPF ([PR 6203](https://github.com/IfcOpenShell/IfcOpenShell/pull/6203)). Status in git: `rocksdb_backend=wired_over_spf_cap`. Convert is streaming; there is no SPF fallback over the in-memory cap. Convert/open failure is HTTP **503** `IFC disk backend unavailable`.

## Where 1,5 ГБ likely comes from

Autodesk IFC exporter help (Revit 2024 toolkit): the third-party write toolkit has a **practical maximum around 1,5 GB**. That is an **authoring export** ceiling, not a promise that a checker can SPF-`open()` the file. Source: [Revit IFC Help](https://up.autodesk.com/2024/RVT/ADSKIFCExporterHelp_24_3_2.htm).

Industry rule of thumb (export guides): keep a single IFC near **~250 MB** or split by discipline/level. That is the same order as bSI and our SPF default.

## What the code does now

1. `classify_ifc_bytes` names the band: `analyze_ok` (SPF) / `analyze_disk` (RocksDB; alias `analyze_blocked_ingest_ok`) / `over_ingest`.
2. HTTP 413 over the **ingest** envelope is machine-readable: `reason_code=ifc_over_ingest_cap`, `required_profile=samolet_pilot`, `see` the path of this file. Message stays `IFC exceeds analyze size limit` (no byte oracle). RSS is **not** a measured figure (`rss_measured: false`).
3. `open_ifc_model` never SPF-opens over `AEROBIM_MAX_IFC_BYTES`. Over-SPF files convert to RocksDB then `open(rdb)`.
4. RSS probe opens under the ingest envelope (RocksDB when over SPF). Files over ingest are classified, not opened. `--write-docs-evidence` stays fixture-only.
5. WASM viewer and object-store `get_bytes` stay **256 MiB**. Do not buffer a 1.5 GB file for preview.
6. Development HTTP (`Settings.from_env` without Samolet caps) still has `max_model_bytes=256 MiB`. The Samolet 1.5 GB path is `samolet_pilot`/`production` (or an explicit `AEROBIM_MAX_MODEL_BYTES`).
7. UI 2026-09-04: `PackUploadPanel` / `AnalyzeRunPanel` state the split in Russian. Upload is one XHR with progress and cancel; resumable protocol is **not** implemented. WASM still 256 MiB.

Does not close RT-001/002b/003. Does not parse RVT/NWD/LIRA. Does not raise the SPF default cap. Does not claim a measured 1.5 GB RSS or customer SLA.
