# IFC release benchmark (2026-08)

**claim_level:** `fixture_only` / fixture-scoped
**customer_accuracy_not_established:** `true`
**accuracy_measured:** `false` (no adjudicated GT for these packs; issue_count is not accuracy)

Fixture-only schema suite over IFC2X3 / IFC4 / IFC4X3 wall Pset packs. Not a product accuracy claim. Real customer packages: **not run**.

Stability: shared DI container + suite prime; measured iterations=20, warmup=2. With n<20 nearest-rank p95 can equal max (historical IFC4 spike).

| Schema | Packs | bytes | entities | p50 ms | p95 ms | max ms | spike max/p50 | issues | reqs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| IFC2X3 | 1 | 975 | 12 | 30.809 | 31.925 | 32.024 | 1.039 | 5 | 3 |
| IFC4 | 1 | 997 | 12 | 30.199 | 31.28 | 33.422 | 1.107 | 4 | 3 |
| IFC4X3 | 1 | 1005 | 12 | 31.56 | 32.717 | 32.806 | 1.039 | 6 | 3 |

Policy: Schema suite reuses one DI container, primes once, warms per pack, gc.collect after warmup, and defaults to n=20 so nearest-rank p95 is not identical to a single OS/MEP spike (historical IFC4 n=5 max~568ms).

Generated at: `2026-08-15T08:37:15.775009+00:00`
JSON evidence: `audit/evidence/ifc-release-benchmark-2026-08.json`
