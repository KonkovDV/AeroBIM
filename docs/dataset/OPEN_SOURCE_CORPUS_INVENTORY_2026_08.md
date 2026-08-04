# Open-source corpus inventory (Sprint 2)

**Date:** 2026-08-04 (updated after search pass)  
**claim_level:** inventory only — not product accuracy; Checkpoint **NO_GO**

Rule: same as BSI — verbatim NOTICE + pin, or link-only until license GO. No derivatives without explicit license.

**Decision update:** do **not** draw synthetic geometry from scratch. Prefer real IFC → BatchPlan/ResBIM plans → planted defects. Detail: [`OPEN_SOURCE_SEARCH_RESULTS_2026_08_04.md`](OPEN_SOURCE_SEARCH_RESULTS_2026_08_04.md).

| Source | In repo? | License | Storage | Status | Notes |
|---|---|---|---|---|---|
| buildingSMART IDS TestCases | Yes | CC BY-ND 4.0 | Vendored + NOTICE + pins | **READY** | 290 regression pairs |
| buildingSMART BCF/IDS XSD | Yes | CC BY-ND 4.0 | Vendored + NOTICE | **READY** | RT-W-01 |
| AeroBIM fixtures / Level-B | Yes | Fixture / MIT | In-tree | **READY** | Synthetic floor for Sprint 2 PDF |
| **IFC-Bench v2** | Pin only | QA **CC BY 4.0**; models per-file (exclude GPLv3 from MIT tree) | `.local/ifc-bench-v2` + [`ifc-bench-v2/IMPORT_PINS.json`](../../samples/benchmarks/ifc-bench-v2/IMPORT_PINS.json) | **PINNED** | Measured 1026 QA rows; smoke 7/1026 scored @ 1.0 (`docs/evidence/ifc-bench-v2-smoke-latest.json`) |
| KAAN residential IFC+plans | No | **No open primary** — [`KAAN_LICENSE_HONESTY_2026_08_04.md`](KAAN_LICENSE_HONESTY_2026_08_04.md) | pin_or_link_only | **PARTIAL** | Do not vendor |
| OSArch open data directory | No | varies | link_only | **PARTIAL** | MEP rehearsal; ≠ RT-003 close |
| BatchPlan / ResBIM | No | BatchPlan **MIT** + pythonocc — [`BATCHPLAN_PROBE_2026_08_04.md`](BATCHPLAN_PROBE_2026_08_04.md) | tool pin | **PARTIAL** | Preferred synthetic pipeline; not wired |
| ArchCAD-400K / FloorPlanCAD | No | check upstream | EXTERNAL | **PARTIAL** | Symbol vision (AECV weak spot) |
| CODE-ACCORD | No | check HF | EXTERNAL | **PARTIAL** | WP-04 / RT-002 later |
| Минстрой / Renga | No | TBD | pin_or_link_only | **INVENTORY** | No vendor without GO |
| CubiCasa5K / CVC-FP | No | via AECV | EXTERNAL_PIN | **INTERNAL_ONLY_LICENSE_REVIEW** | Do not copy to samples |

## ifcdiff / TZ row 28

See [`IFCDIFF_TZ_GAP_NOTE_2026_08_04.md`](IFCDIFF_TZ_GAP_NOTE_2026_08_04.md). Thin GUID/attribute adapter + fixture landed (`Tokens.IFC_MODEL_DIFF`); matrix row 28 stays **MISSING** until package-vs-package CDE compare. No `deepdiff` / wheel `ifcdiff` CLI.

## Manifest sync

- Root `DATASET_MANIFEST.json`: `review_pending=0`  
- Sprint provenance: CC BY-ND aligned  
- IFC-Bench v2: pins JSON only (no 2 GB vendoring this commit)
