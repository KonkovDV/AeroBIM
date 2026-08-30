# IFC release benchmark (2026-08)

**claim_level:** `fixture_only` / fixture-scoped
**customer_accuracy_not_established:** `true`
**accuracy_measured:** `false` (no adjudicated GT for these packs; issue_count is not accuracy)

Fixture-only schema suite over IFC2X3 / IFC4 / IFC4X3 wall Pset packs. Not a product accuracy claim. Real customer packages: **not run**.

Stability: shared DI container + suite prime; measured iterations=20, warmup=2. With n<20 nearest-rank p95 can equal max (historical IFC4 spike).

| Schema | Packs | bytes | entities | p50 ms | p95 ms | max ms | spike max/p50 | issues | reqs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| IFC2X3 | 1 | 975 | 12 | 94.89 | 128.634 | 134.166 | 1.414 | 5 | 3 |
| IFC4 | 1 | 997 | 12 | 91.199 | 93.785 | 112.715 | 1.236 | 4 | 3 |
| IFC4X3 | 1 | 1005 | 12 | 59.801 | 172.088 | 269.41 | 4.505 | 6 | 3 |

Policy: Schema suite reuses one DI container, primes once, warms per pack, gc.collect after warmup, and defaults to n=20 so nearest-rank p95 is not identical to a single OS/MEP spike (historical IFC4 n=5 max~568ms).

Generated at: `2026-08-30T09:51:07.883147+00:00`
JSON evidence: `audit/evidence/ifc-release-benchmark-2026-08.json`
