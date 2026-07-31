# Sprint 2.1 benchmark corpus

**Claim level:** `engineering_baseline_only`  
**Customer evidence:** `false`  
**Checkpoint impact:** does **not** close RT-001 / RT-002 / RT-003.

## What this is

Minimal, hash-locked package for Sprint 2.1:

- reuses existing **fixture / synthetic** assets under `samples/` (see `DATASET_MANIFEST.json`);
- adds a Sprint 2.1 **manifest** + **mutation SSOT** + expected-finding labels;
- does **not** download large third-party IFC dumps into git without license clearance.

## What this is not

- not a Samolet customer corpus;
- not product accuracy;
- not customer SLA ≤30 min.

## Layout

| Path | Role |
|------|------|
| `manifest.json` | Asset inventory + hashes |
| `source-provenance.json` | License / redistribution status |
| `package-baseline-*.json` | Packs for open/synthetic baseline |
| `baseline-package.json` | Entry pack for CLI |
| `mutations/mutation-manifest.json` | SSOT for synthetic defects |
| `expected/` | Expected finding ids for TP/FP/FN |
| `labels/` | Detection-precision style labels |

## Reproduce

```bash
cd backend
python -m aerobim.tools.run_sprint_2_1_baseline \
  --pack ../samples/benchmarks/sprint-2-1/baseline-package.json \
  --iterations 1 \
  --output ../artifacts/sprint-2-1/baseline.json \
  --report ../artifacts/sprint-2-1/baseline.md
```
