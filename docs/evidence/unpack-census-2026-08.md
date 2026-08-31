<!-- claims-lint: allow-file reason="Unpack suffix/magic census; not processed; no names/hashes; NO_GO" -->
---
title: "Local unpack census — suffix and magic (30.08.2026)"
date: "2026-08-30"
last_updated: "2026-08-30"
status: active
version: "1.1.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: coverage_map_only
detected_count: 0
claim_boundary: >
  Suffix and magic counts of a gitignored wrapper copy and its unpack tree.
  Evening recensus after deleting covered source archives. Not pack processed.
  Not product accuracy. Not native RVT/DWG/LIRA. Tracker «43 GB» is the
  assigned task title, not this measurement. Checkpoint NO_GO.
---

# Local unpack census (30.08.2026)

Machine pin: `python -c "from aerobim.domain.unpack_census import unpack_census_snapshot"`.  
JSON: [`unpack-census-latest.json`](unpack-census-latest.json). Live trees stay under `.local/`. Names and hashes are **not** in git.

Checkpoint **`NO_GO`**. `processed: false`. This is SIG-02 **inventory**, not SIG-01 findings and not «пакет обработан». The 27.08 public rehearsal pin (**2383** files on a partial wrapper) remains.

**Evening recensus.** Morning counts **2618 / 6467** included packed zip/7z shells. After member-level coverage the source archives were deleted locally; live trees are **2552 / 6408** with **0** zip/7z remaining. Deletion is a disk-hygiene step, not «processed».

Depth on carriers (exporters, FireRating scope, RVT years, LIRA fragment gaps): [`deep-study-carrier-facts-2026-08.md`](deep-study-carrier-facts-2026-08.md).

## Two trees (no folder labels)

| Tree | Files (evening) | Role |
|---|---:|---|
| Wrapper copy (`files/`, gitignored) | **2552** | As-received objects after covered archives removed |
| Unpack tree | **6408** | Members extracted; leftover shells also removed |

Unpack is **not** a union that replaces the wrapper. IFC for SIG-01 still lives primarily on the wrapper (**15** SPF files). The unpack tree holds **4** IFC (copies of wrapper files), plus PDF/DWG/RVT/LIRA that were only inside archives.

## Magic vs suffix (unpack tree unless noted)

| Carrier | Wrapper | Unpack | Magic check | Engine |
|---|---:|---:|---|---|
| IFC SPF | 15 | 4 | `ISO-10303-21`; **IFC2X3** only | Analyze under 256 MiB SPF; **1** file over cap on both trees; do not raise `AEROBIM_MAX_IFC_BYTES` |
| PDF | 1208 | 2046 | `%PDF-1.3…1.7` | Core PDF path; **1** wrapper / **2** unpack files named `.pdf` are PNG |
| DWG | 551 | 1877 | `AC1018`–`AC1032` (mostly AC1032) | `dwg_native=NOT_IMPLEMENTED` |
| DXF | 67 | 321 | ASCII `SECTION` | Optional `[cad]` ezdxf; not DWG |
| RVT | 27 | 75 | OLE CFB | Fail-closed (SIG-07) |
| NWD/NWC | 21 | 8 | `#LcUStream` | Fail-closed (SIG-07); Navis mostly stayed on the wrapper |
| `.lir` + tilde sidecars | 20+21 | 36+89 | LIRA-SAPR family | `native_lir=not_implemented` (SIG-06) |
| `.max` | 0 | 164 | OLE | Out of MVP; not a drawing reader |
| Zip/7z **shells** | **0** | **0** | — | Covered archives deleted after member check; not «still packed» |

OLE `.db` on both trees is **not** SQLite. Empty members: **30** in the unpack tree. One solver-binary member had a CRC defect on extract; it is not parsed.

## What this licenses

- Coverage map of **carriers** for SIG-02 (format / fail-closed natives / no remaining packed shells).
- IFC2X3-only pack: no IFC4 / IFC4x3 in this local copy.
- PDF volume for a future SIG-01 finding-count run **after** OA-9; that run is not this census.

## What this does not license

- Pack processed, «43 ГБ обработаны», product accuracy, customer SLA.
- Native DWG / RVT / NWD / LIRA / 3ds Max.
- Raising the 256 MiB SPF default because one IFC is over cap (OA-16 / RocksDB path).
- `customer_confirmed_patterns` or RT-001/002b/003 CLOSED.

Related: [`../quality/TRACKER_EIGHT_TASKS_SIGINEVICH_2026_08.md`](../quality/TRACKER_EIGHT_TASKS_SIGINEVICH_2026_08.md) · [`../quality/OWNER_AI_PLAN_EXECUTION_2026_08_27.md`](../quality/OWNER_AI_PLAN_EXECUTION_2026_08_27.md) · [`DATA_STATEMENT_2026_08.md`](DATA_STATEMENT_2026_08.md).
