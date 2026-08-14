<!-- claims-lint: allow-file reason="IFC schema-suite matrix; >90% only as non-claim boundary" -->
# IFC release matrix (tracker 2.1)

**claim_level:** `fixture_only`
**customer_accuracy_not_established:** `True`

Fixture schema-suite kernel timing and finding counts. issue_count is not accuracy. Not customer packages. Not TZ >90%.

| Schema | IfcProduct | entities | rules eval | rules fired | findings | p50 ms | p95 ms | max ms | refusals |
|---|---|---:|---:|---|---:|---:|---:|---:|---|
| IFC2X3 | IfcWall×1 | 12 | 3 | AEROBIM-CLASH-CAPABILITY×1, AEROBIM-QTY-MISSING×1, IDS-Wall Width Quantity×1, SAM-R-002×1, SAM-R-003×1 | 5 | 44.325 | 49.044 | 59.351 | shared honesty only |
| IFC4 | IfcWall×1 | 12 | 3 | AEROBIM-CLASH-CAPABILITY×1, AEROBIM-QTY-MISSING×1, SAM-R-002×1, SAM-R-003×1 | 4 | 38.135 | 47.209 | 48.448 | shared honesty only |
| IFC4X3 | IfcWall×1 | 12 | 3 | AEROBIM-CLASH-CAPABILITY×1, AEROBIM-IDS-IFC-VERSION×2, AEROBIM-QTY-MISSING×1, SAM-R-002×1, SAM-R-003×1 | 6 | 43.386 | 62.795 | 64.402 | ids=failed |

Schema-suite packs are IFC+IDS wall Pset fixtures. Capability SKIPPED (clash/raster/MEP) is honesty, not a silent pass. DWG native remains FAILED.

issue_count / rules fired are fixture findings, **not claimed** product accuracy.

Shared honesty refusals (all three packs, omitted from the refusals column): clash skipped, raster skipped, dwg_dxf missing, cv_human_level missing, mep_system_clash not_verified, calculation_correctness not_implemented, qualified_signature missing, unit_scale/ifc_schema not_verified. Native DWG is **not claimed** DWG-ready.

Generated at: `2026-08-14T13:15:46.359762+00:00`
content_sha256: `8d71e2ecc7e7ec8c7b0c704c0ffcd27ec8c71e99e6fe5b73f3495e8ea7aef85d`
machine: `{"platform": "Windows-11-10.0.26200-SP0", "python": "3.13.7", "machine": "AMD64", "system": "Windows"}`
