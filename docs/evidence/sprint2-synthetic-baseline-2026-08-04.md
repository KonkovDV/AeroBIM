# Sprint 2 synthetic baseline

- generated_at: `2026-08-04T10:22:36.409313+00:00`
- claim_level: `synthetic_only`
- closes_rt001: `False`
- checkpoint: `NO_GO`

## Metrics

- TP/FP/FN: **6/2/0**
- precision: **0.75** (Wilson lower: 0.409275)
- recall: **1.0** (Wilson lower: 0.609666)
- time_per_case_p95_s: **1.904667**
- n_planted: 6 (below planner half-width 0.08 target)

## Limitations

- Synthetic planted defects only; unplanted TZ classes unmeasured
- Ground truth complete by construction for planted detectable set
- No real customer packages
- TZ 90% threshold NOT confirmed
- Does not close RT-001

JSON twin: `C:/plans/AeroBIM/docs/evidence/sprint2-synthetic-baseline-2026-08-04.json`
