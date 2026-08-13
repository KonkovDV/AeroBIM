# IFC release matrix (tracker 2.1)

**claim_level:** `fixture_only`
**customer_accuracy_not_established:** `True`

Fixture schema-suite kernel timing and finding counts. issue_count is not accuracy. Not customer packages. Not TZ >90%.

| Schema | entities | bytes | rules evaluated | findings emitted | p50 ms | p95 ms | max ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| IFC2X3 | 12 | 997 | 3 | 6 | 25.86 | 29.194 | 31.547 |
| IFC4 | 12 | 997 | 3 | 4 | 25.681 | 31.504 | 40.354 |
| IFC4X3 | 12 | 1005 | 3 | 4 | 27.881 | 41.388 | 45.576 |

Schema-suite packs are IFC+IDS wall Pset fixtures. Capability SKIPPED (clash/raster/MEP) is honesty, not a silent pass. DWG native remains FAILED.

Generated at: `2026-08-13T20:15:55.242372+00:00`
content_sha256: `c9c27ff556f47dab28c06a3299ca10098ae0bea9296b28053522c168d99ba7c3`
machine: `{"platform": "Windows-11-10.0.26200-SP0", "python": "3.13.7", "machine": "AMD64", "system": "Windows"}`
