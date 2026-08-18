<!-- claims-lint: allow-file reason="Open IFC stress; GNI student models are not product accuracy" -->
---
title: "Open IFC header stress"
date: 2026-08-13
claim_level: open_ifc_stress
claim_boundary: >-
  Header-level open/parse timing on IFC files present on disk. Not GNI 223 unless AEROBIM_GNI_BIM_ROOT is set. Student GNI models are not product accuracy. GPLv3 IFC-Bench models are not scanned from this tree. IfcOpenShell entity counts are optional and skip oversized files.
---

# Open IFC header stress

- fixture files: **15** open_ok **15**
- schemas: `{"IFC2X3": 1, "IFC4": 13, "IFC4X3": 1}`
- GNI: **RUN** files **224** open_ok **224** fail **0**
- GNI schemas: `{"IFC2X3": 29, "IFC4": 195}`
- GNI subsets: `{"fundamentals_2025": 208, "projects_2026": 16, "other": 0}`
- GNI bytes_total: **3304206027**
- AR+STR pairs complete: **7** / 9 stems (upstream: 7 of 9 teams)
- largest file: `{"path": "2026_BIMprojects/2026_BIMprojects/model_6_arc.ifc", "bytes": 561838129}` (upstream could not load ~536 MB architecture; header-only still opens)
- IfcOpenShell: `{"ok": 223, "skipped_oversize": 1}`
- extra roots: `[{"dir": ".local/bim-whale-ifc-samples", "status": "RUN", "file_count": 6, "open_ok": 6, "schema_counts": {"IFC2X3": 6}, "ifc_open_counts": {"ok": 6}}]`
- DOI: [10.5281/zenodo.19722012](https://doi.org/10.5281/zenodo.19722012)
- content_sha256: `1682899c2eed89810708cd0999d5a98b5b4a7ecfaaf46c3f241fabafc2c5c746`

## Paired architectural + structural stems

| stem | paired | schema_match | arc_products | structure_products |
| --- | --- | --- | --- | --- |
| `model_0` | True | True | 2150 | 152 |
| `model_1` | True | True | 34268 | 328 |
| `model_2` | False | None | 589 | None |
| `model_3` | True | True | 1735 | 201 |
| `model_4` | True | True | 1419 | 107 |
| `model_5` | True | True | 3142 | 1111 |
| `model_6` | False | None | None | None |
| `model_7` | True | True | 1243 | 876 |
| `model_8` | True | True | 702 | 206 |

Student GNI models are **not** product accuracy. Checkpoint stays NO_GO.

```bash
cd backend
python -m aerobim.tools.run_open_ifc_stress --gni-root ../.local/gni-bim --open-model
```
