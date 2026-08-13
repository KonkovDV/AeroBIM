# IFC release matrix (tracker 2.1)

**claim_level:** `fixture_only`
**customer_accuracy_not_established:** `True`

Fixture schema-suite kernel timing and finding counts. issue_count is not accuracy. Not customer packages. Not TZ >90%.

| Schema | entities | bytes | rules evaluated | findings emitted | p50 ms | p95 ms | max ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| IFC2X3 | 12 | 997 | 3 | 6 | 25.365 | 25.827 | 25.827 |
| IFC4 | 12 | 997 | 3 | 4 | 23.677 | 24.97 | 24.97 |
| IFC4X3 | 12 | 1005 | 3 | 6 | 25.806 | 31.758 | 31.758 |

Schema-suite packs are IFC+IDS wall Pset fixtures. Capability SKIPPED (clash/raster/MEP) is honesty, not a silent pass. DWG native remains FAILED.

Generated at: `2026-08-13T21:45:27.707830+00:00`
content_sha256: `3780a18ddba8f4ebac684b977f12ed4c66b71b0317ccf3b17f2803e27c45f5b6`
machine: `{"platform": "Windows-11-10.0.26200-SP0", "python": "3.13.7", "machine": "AMD64", "system": "Windows"}`
