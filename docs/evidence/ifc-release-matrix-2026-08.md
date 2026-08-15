<!-- claims-lint: allow-file reason="IFC schema-suite matrix; >90% only as non-claim boundary" -->
# IFC release matrix (tracker 2.1)

**claim_level:** `fixture_only`
**customer_accuracy_not_established:** `True`

Fixture schema-suite kernel timing and finding counts. issue_count is not accuracy. Not customer packages. Not TZ >90%.

**suite:** n=20 warmup=2 python=`3.12.10`. Shared-gate `summary.passed` is not Checkpoint GO.

| Schema | IfcProduct | entities | rules eval | rules fired | findings | passed | p50 ms | p95 ms | max ms | refusals |
|---|---|---:|---:|---|---:|---|---:|---:|---:|---|
| IFC2X3 | IfcWall×1 | 12 | 3 | AEROBIM-CLASH-CAPABILITY×1, AEROBIM-QTY-MISSING×1, IDS-Wall Width Quantity×1, SAM-R-002×1, SAM-R-003×1 | 5 | false | 28.012 | 36.717 | 45.385 | clash=skipped |
| IFC4 | IfcWall×1 | 12 | 3 | AEROBIM-CLASH-CAPABILITY×1, AEROBIM-QTY-MISSING×1, SAM-R-002×1, SAM-R-003×1 | 4 | false | 28.187 | 32.266 | 154.031 | clash=skipped |
| IFC4X3 | IfcWall×1 | 12 | 3 | AEROBIM-CLASH-CAPABILITY×1, AEROBIM-IDS-IFC-VERSION×2, AEROBIM-QTY-MISSING×1, SAM-R-002×1, SAM-R-003×1 | 6 | false | 35.621 | 56.957 | 60.829 | clash=skipped, ids=failed |

Schema-suite packs are IFC+IDS wall Pset fixtures. Clash SKIPPED/FAILED and raster/MEP SKIPPED/NOT_VERIFIED are honesty, not a silent pass. DWG native remains FAILED.

issue_count / rules fired are fixture findings, **not claimed** product accuracy.

Shared honesty refusals (all three packs, omitted from the refusals column): raster skipped, dwg_dxf missing, cv_human_level missing, mep_system_clash not_verified, calculation_correctness not_implemented, qualified_signature missing, unit_scale/ifc_schema not_verified. Clash skipped/failed is listed in the refusals column. Tiny wall fixtures default to clash=skipped via AEROBIM_CLASH_SKIP_TINY (all-skipped still fail-closed); geom-init FAILED remains honesty, not a silent pass. Native DWG is **not claimed** DWG-ready.

## Tracker paste (Dmitry 14.08 #2)

**suite:** n=20 warmup=2 python=`3.12.10`. Shared-gate `summary.passed` is not Checkpoint GO.

| Schema | Elements | Rules fired | Findings | passed | p50 ms | p95 ms | Refusals |
|---|---|---|---:|---|---:|---:|---|
| IFC2X3 | IfcWall×1 | AEROBIM-CLASH-CAPABILITY×1, AEROBIM-QTY-MISSING×1, IDS-Wall Width Quantity×1, SAM-R-002×1, SAM-R-003×1 | 5 | false | 28.012 | 36.717 | clash=skipped |
| IFC4 | IfcWall×1 | AEROBIM-CLASH-CAPABILITY×1, AEROBIM-QTY-MISSING×1, SAM-R-002×1, SAM-R-003×1 | 4 | false | 28.187 | 32.266 | clash=skipped |
| IFC4X3 | IfcWall×1 | AEROBIM-CLASH-CAPABILITY×1, AEROBIM-IDS-IFC-VERSION×2, AEROBIM-QTY-MISSING×1, SAM-R-002×1, SAM-R-003×1 | 6 | false | 35.621 | 56.957 | clash=skipped, ids=failed |

Paste-ready. Fixture kernel only. IFC4X3 `ids=failed` is fail-closed `ifcVersion` (BSI 0101), not a product defect. Not customer accuracy.

Generated at: `2026-08-15T17:22:49.426402+00:00`
content_sha256: `559dcd91f3bde3a485a6d5d8d77679586a1e13de079975e0cb36e010a6346391`
machine: `{"platform": "Windows-11-10.0.26200-SP0", "python": "3.12.10", "machine": "AMD64", "system": "Windows"}`
