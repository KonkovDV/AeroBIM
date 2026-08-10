# Red Team — VLM rename (kimi→vlm) + Yandex path

**Date:** 2026-08-10  
**Scope:** uncommitted advisory VLM rename + mentor/Yandex wiring  
**claim_level:** code_review + focused tests (not customer corpus)

## Summary

Production/DI contour remains sound after rename. Two Medium findings on CLI smoke
paths were **fixed in the same change set** before push.

## Findings

| ID | Severity | Status | Finding |
|---|---|---|---|
| RT-VLM-01 | Medium | **Fixed** | Mentor/region smoke bypassed `vlm_advisory_ready` / pilot-production signoff |
| RT-VLM-02 | Medium | **Fixed** | `vlm_advisory_smoke` whole-sheet egress without stamp/PII guard |
| RT-VLM-03 | Info | Open (accepted) | Yandex uses `json_object` + prompt schema sketch (post-hoc grounding fail-closed) |
| RT-VLM-04 | Info | Open (accepted) | Historical `docs/architecture/KIMI_*` keep old names (evidence only) |

### RT-VLM-01 fix

`smoke_signoff_blocks_external()` in `vlm_smoke_gate.py` — blocks
`samolet_pilot` / `production` before client construction in:

- `run_mentor_vlm_demo.py`
- `vlm_region_smoke.py`
- `vlm_advisory_smoke.py`

### RT-VLM-02 fix

Whole-sheet advisory smoke requires explicit `--allow-whole-sheet`; default
points operators to `vlm_region_smoke` (region-restricted + PII plan).

## Checklist (DI / product)

| Check | Result |
|---|---|
| SSRF host allowlist on VLM URL | Pass |
| Secrets not in `repr` / mentor errors | Pass |
| `AEROBIM_KIMI_*` aliases do not bypass DI signoff | Pass |
| `vlm_advisory_ready` fail-closed on pilot/production | Pass |
| Region-only product path + stamp exclusion | Pass |
| `summary.passed` OFF==ON | Pass (existing tests) |
| Yandex `Api-Key` + `x-folder-id` + think-off | Pass |

## Verification

```text
120+ focused VLM tests passed (prior suite)
+ smoke gate tests for signoff / whole-sheet opt-in
```

## Claim boundary

Rename does **not** claim product CV, >90% accuracy, native DWG, or VLM verdicts.
Live provider remains advisory-only (Yandex Qwen when configured).
