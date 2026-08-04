# ifcdiff → TZ row 28 (version / doc-type compare)

**Date:** 2026-08-04 (updated)  
**Status:** thin port landed — TZ product row still **not** closed as CDE compare  
**Matrix:** [`audit/reports/TZ_RUNTIME_MATRIX.md`](../../audit/reports/TZ_RUNTIME_MATRIX.md) row **28**

## Finding (unchanged product gap)

Tracker TZ requires «сравнение версий и типов документации» as multi-package CDE compare. Reserved kinds `STAGE_MISMATCH` / `VERSION_MISMATCH` alone do not satisfy that.

## Wheel reality

IfcOpenShell **documents** `ifcdiff` next to `ifctester` / `ifcclash`. On locked **0.8.5**, there is **no** importable `ifcdiff` module and no CLI on PATH. Upstream full `ifcdiff.py` pulls **deepdiff** — **not** added here.

## What landed (engineering)

| Piece | Path |
|---|---|
| Port | `backend/src/aerobim/domain/ifc_model_diff.py` (`IfcModelDiff`) |
| Adapter | `backend/src/aerobim/infrastructure/adapters/ifc_guid_attribute_diff.py` |
| DI | `Tokens.IFC_MODEL_DIFF` |
| Fixture | `samples/ifc/model-diff/revision-{a,b}.ifc` |
| Test | `backend/tests/test_ifc_model_diff.py` |

Scope: GlobalId **add/remove** + `Name` / `ObjectType` / `Tag` / `Description` changes. Severity map: removed→critical, added→warning, attribute→info.

## Honesty / Claims Lock

- Engineering signal only — not «документация одобрена».  
- Does **not** close RT-001.  
- Does **not** claim CDE version management.  
- Matrix row 28 stays **MISSING** (or PARTIAL only if explicitly reclassified) until package-vs-package doc-type/version compare ships.

## Estimate remaining

~0.5–1 d to map findings into analyze pipeline + optional PARTIAL matrix bump with fixture evidence; full CDE compare remains larger.
