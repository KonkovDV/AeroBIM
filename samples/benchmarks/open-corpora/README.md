# Open corpora measurability profiles (WP-06)

Three reproducible profiles for engineering measurability on **open / fixture** data.

| Profile | Measures | Does **not** measure |
|---|---|---|
| `regression` | Binary IDS↔IFC pass/fail vs pinned expected outcomes | Product accuracy, expert TP/FP |
| `pilot-approx` | Package analyze wall-clock on public IFC + residential inventory | Customer SLA, precision |
| `load` | AR/KZH section-pairing + MEP federated timing | Verified geometric clash (RT-003 OPEN) |

## Honest inventory (regression)

The repo does **not** contain ≥250 official IDS/IFC pass-fail cases.  
Pinned binary cases today: **7** (see `profiles/regression.json` → `honest_case_count`).

External buildingSMART IDS test suites with hundreds of cases are **not vendored** here; expanding past 7 requires an explicit license-cleared import with SHA pins.

## Claim boundary (every artifact)

Open sets lack expert TP/FP labels → **regression and timing only**, never product accuracy, never «>90%».

## Run

```bash
cd backend
# Full three-profile run (writes artifacts/open-corpora/)
python -m aerobim.tools.run_open_corpora_profiles

# Cheap smoke: pin verification only (CI-friendly)
python -m aerobim.tools.run_open_corpora_profiles --mode smoke
```

## CI

CI wires `--mode smoke` (pin check). Full live analyze/IDS regression is **manual** or an optional local job — not claimed as customer evidence.
