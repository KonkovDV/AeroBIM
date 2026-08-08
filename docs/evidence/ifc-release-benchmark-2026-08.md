# IFC release benchmark (2026-08)

**claim_level:** `fixture_only` / fixture-scoped
**customer_accuracy_not_established:** `true`
**accuracy_measured:** `false` (no adjudicated GT for these packs; issue_count is not accuracy)

Fixture-only schema suite over IFC2X3 / IFC4 / IFC4X3 wall Pset packs. Not a product accuracy claim. Real customer packages: **not run**.

Stability: shared DI container + suite prime; measured iterations=20, warmup=2. With n<20 nearest-rank p95 can equal max (historical IFC4 spike).

| Schema | Packs | bytes | entities | p50 ms | p95 ms | max ms | spike max/p50 | issues | reqs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| IFC2X3 | 1 | 997 | 12 | 23.882 | 24.617 | 24.728 | 1.035 | 6 | 3 |
| IFC4 | 1 | 997 | 12 | 23.379 | 24.203 | 24.976 | 1.068 | 4 | 3 |
| IFC4X3 | 1 | 1005 | 12 | 23.384 | 24.535 | 24.823 | 1.062 | 4 | 3 |

Policy: Schema suite reuses one DI container, primes once, warms per pack, gc.collect after warmup, and defaults to n=20 so nearest-rank p95 is not identical to a single OS/MEP spike (historical IFC4 n=5 max≈568ms).

Generated at: `2026-08-08T07:37:03.643318+00:00`
JSON evidence: `C:/plans/AeroBIM/audit/evidence/ifc-release-benchmark-2026-08.json`
