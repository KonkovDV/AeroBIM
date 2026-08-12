# IFC release benchmark (2026-08)

**claim_level:** `fixture_only` / fixture-scoped
**customer_accuracy_not_established:** `true`
**accuracy_measured:** `false` (no adjudicated GT for these packs; issue_count is not accuracy)

Fixture-only schema suite over IFC2X3 / IFC4 / IFC4X3 wall Pset packs. Not a product accuracy claim. Real customer packages: **not run**.

Stability: shared DI container + suite prime; measured iterations=20, warmup=2. With n<20 nearest-rank p95 can equal max (historical IFC4 spike).

| Schema | Packs | bytes | entities | p50 ms | p95 ms | max ms | spike max/p50 | issues | reqs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| IFC2X3 | 1 | 997 | 12 | 29.663 | 30.992 | 32.498 | 1.096 | 6 | 3 |
| IFC4 | 1 | 997 | 12 | 28.255 | 30.206 | 31.962 | 1.131 | 4 | 3 |
| IFC4X3 | 1 | 1005 | 12 | 29.386 | 30.657 | 37.61 | 1.28 | 4 | 3 |

Policy: Schema suite reuses one DI container, primes once, warms per pack, gc.collect after warmup, and defaults to n=20 so nearest-rank p95 is not identical to a single OS/MEP spike (historical IFC4 n=5 max~568ms).

Generated at: `2026-08-10T22:04:04.561088+00:00`
JSON evidence: `C:/plans/AeroBIM/audit/evidence/ifc-release-benchmark-2026-08.json`
