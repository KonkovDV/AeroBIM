# Open corpora measurability profiles (WP-06)

Reproducible profiles for engineering measurability on **open / fixture** data.

| Profile | Measures | Does **not** measure |
|---|---|---|
| `regression` | Binary IDS↔IFC pass/fail vs pinned expected outcomes (fixture n=7) | Product accuracy, expert TP/FP |
| `regression-bsi` | Unmodified buildingSMART IDS TestCases (CC BY-ND 4.0); **honest_case_count=290** | Product accuracy; not a marketing ≥250 claim if N drifts |
| `pilot-approx` | Package analyze wall-clock on public IFC + residential inventory | Customer SLA, precision |
| `load` | AR/KZH section-pairing + MEP federated timing | Verified geometric clash (RT-003 OPEN) |

## Honest inventory

| Corpus | Count | License |
|---|---|---|
| Fixture regression | **7** (`profiles/regression.json`) | repo fixtures |
| buildingSMART IDS TestCases | **290** (`profiles/regression-bsi.json`) | **CC BY-ND 4.0** unmodified (`samples/ids/buildingsmart-testcases/NOTICE`) |

Import / refresh BSI suite:

```bash
cd backend
python -m aerobim.tools.import_buildingsmart_ids_testcases --commit 016bbadce0d227d8eabbbc3e8b2b3788590b8a97
python -m aerobim.tools.export_samples_manifest --merge-missing
```

The commit is the upstream pin in `profiles/regression-bsi.json`. The import rewrites that profile and registers it in `manifest.json`; `--source-dir` reads a local clone of buildingSMART/IDS instead of downloading.

## Claim boundary (every artifact)

Open sets lack expert TP/FP labels → **regression and timing only**, never product accuracy, never «>90%».

**L1 open benches** (separate rail): IFC-Bench v1 deterministic smoke —

```bash
# once: git clone --depth 1 https://github.com/sylvainHellin/ifc-bench.git .local/ifc-bench
cd backend
python -m aerobim.tools.run_ifc_bench_smoke --also-docs-evidence
```

Data statement: [`docs/evidence/DATA_STATEMENT_2026_08.md`](../../../docs/evidence/DATA_STATEMENT_2026_08.md).

## Run

```bash
cd backend
python -m aerobim.tools.run_open_corpora_profiles
python -m aerobim.tools.run_open_corpora_profiles --mode smoke
```

## CI

CI wires `--mode smoke` (pin check). Full live analyze/IDS regression is **manual** — not customer evidence.
