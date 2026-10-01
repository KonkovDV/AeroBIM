# IFC-Bench v2 pins

See [`IMPORT_PINS.json`](IMPORT_PINS.json) for hashes, licenses, and GPLv3 exclusions.

| Item | Value |
|---|---|
| Measured v2 CSV SHA-256 (2026-08-04) | `e47ccd097306f5bca49b9c8ac0b4cd72f296df9f7ff7a02625b3f06c1691da9b` |
| HF card SHA (stale) | `8f08f5d0…` — do **not** treat as current pin |
| Measured QA rows | **1026** (card: 1027) |
| Checkout | `.local/ifc-bench-v2` (gitignored); env `AEROBIM_IFC_BENCH_ROOT` |
| Smoke | `python -m aerobim.tools.run_ifc_bench_smoke --version v2 --also-docs-evidence` |
| Evidence | [`docs/evidence/ifc-bench-v2-smoke-latest.json`](../../../docs/evidence/ifc-bench-v2-smoke-latest.json) — countable **27/1026** |

GitHub archive is **v1-only**. Do not vendor the full ~2 GB tree into `samples/` until selective non-GPL pull is approved.

Claim level: `open_bench_only`. Does **not** close RT-001.
