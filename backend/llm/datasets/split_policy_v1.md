# AeroBIM FT Split Policy v1

## Scope

Deterministic split policy for AER-201 scaffold smoke.

## Split Rules

1. `train` contains supervised extraction examples.
2. `val` contains validation examples for bounded quality checks.
3. `holdout` is never used during training.
4. Reused IDs across splits are forbidden.
5. Split edits require manifest version bump.

## Determinism

- Seed: `42`
- Manifest of record: `llm/datasets/manifest_v1.json`
