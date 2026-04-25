# IFC Release Compatibility Matrix

> Last updated: 2026-04-25 — AeroBIM v0.x  
> Scope: `IfcOpenShellValidator` (`infrastructure/adapters/ifc_open_shell_validator.py`)
> and `IfcTesterIdsValidator` (`infrastructure/adapters/ifc_tester_ids_validator.py`).

## Supported IFC Releases

| Feature | IFC2x3 | IFC4 | IFC4x3 | Notes |
|---|---|---|---|---|
| Property sets (`Pset_*`) | ✅ Full | ✅ Full | ✅ Full | `by_type("IfcPropertySet")` |
| Quantity sets (`Qto_*` / `BaseQuantities`) | ⚠️ Partial | ✅ Full | ✅ Full | IFC2x3 uses `BaseQuantities` prefix; IFC4+ uses `Qto_` prefix |
| SI unit assignment (`IfcUnitAssignment`) | ✅ Full | ✅ Full | ✅ Full | `_get_unit_scales()` reads all three releases |
| IFC GUID format | ✅ | ✅ | ✅ | 22-char base64 encoding, stable across releases |
| Classification references (`IfcClassificationReference`) | ✅ | ✅ | ✅ | |
| `IfcWall` / `IfcSlab` / `IfcBeam` / `IfcColumn` | ✅ | ✅ | ✅ | Core structural types stable across releases |
| `IfcRelAssociatesConstraint` (constraint linking) | ❌ | ✅ | ✅ | Not available in IFC2x3 |
| Alignment entities (`IfcAlignment`) | ❌ | ❌ | ✅ | IFC4x3 only (infrastructure domain) |
| Road/rail geometry (`IfcRoad`, `IfcRailway`) | ❌ | ❌ | ✅ | IFC4x3 only |
| IDS validation via IfcTester | ✅ | ✅ | ✅ | IfcTester v0.9+ supports all three |

## Degradation Rules

| Condition | AeroBIM behaviour |
|---|---|
| IFC2x3 file, rule references `Qto_WallBaseQuantities` | Quantity check falls back to `BaseQuantities` Pset matching; no false ERROR, emits INFO |
| IFC4x3 file opened by IfcOpenShell < 0.7 | Parse fails; AeroBIM emits `IFC_PARSE_ERROR` finding with version hint |
| IFC release not detectable from `FILE_SCHEMA` | Treated as IFC4 (most permissive); issue count may be slightly higher |
| `IfcRelAssociatesConstraint` rule on IFC2x3 file | Rule skipped; WARNING emitted: `"IfcRelAssociatesConstraint not available in IFC2x3"` |

## Test Fixtures

Located in `samples/ifc/`:

| Fixture file | IFC release | Coverage |
|---|---|---|
| `wall-pset-qto-pass.ifc` | IFC4 | Pset + Qto present, FireRating=REI60, Width=0.3 |
| `wall-pset-qto-missing-qto.ifc` | IFC4 | Pset present, Qto absent — triggers missing-quantity finding |
| `wall-fire-rating-rei30.ifc` | IFC4 | FireRating=REI30 — triggers value mismatch finding |
| `wall-fire-rating-rei60.ifc` | IFC4 | FireRating=REI60 — passes |
| `walls-multi-entity.ifc` | IFC4 | Multi-entity fixture for batch validation |
| `wall-pset-ifc2x3.ifc` | IFC2x3 | Pset_WallCommon + BaseQuantities — cross-release regression |
| `wall-pset-ifc4x3.ifc` | IFC4x3 | Pset_WallCommon + Qto_WallBaseQuantities — IFC4x3 regression |

## Parametric Test Coverage

`tests/test_ifc_release_compatibility.py` runs the same property-presence check
against all three releases and asserts:
1. IFC2x3 fixture: `FireRating` found in `Pset_WallCommon`.
2. IFC4 fixture: `FireRating` found in `Pset_WallCommon`.
3. IFC4x3 fixture: `FireRating` found in `Pset_WallCommon`.
4. Quantity set name divergence (IFC2x3 `BaseQuantities` vs IFC4+ `Qto_*`) does not
   cause a false-positive ERROR for width checks.

## References

- buildingSMART IFC releases: https://standards.buildingsmart.org/IFC/
- ISO 16739-1:2018 (IFC4) and ISO 16739-1:2024 (IFC4x3)
- buildingSMART Compatibility Policy: https://standards.buildingsmart.org/IFC/DEV/IFC4_3/
- IfcOpenShell IFC2x3/IFC4/IFC4x3 schema support: https://ifcopenshell.org/
