<!-- claims-lint: allow-file reason="P0 env inventory; scanner defect not product accuracy; NO_GO" -->
---
title: "P0 — bidirectional AEROBIM_* inventory (scanner vs no-op)"
date: "2026-08-27"
status: active
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Inventory of how Settings reads env names. Does not close RT.
  Does not publish a new runtime-baseline pin (attested_by=ci only).
  Checkpoint NO_GO.
---

# P0: documented_env_vars absent from code_env_vars

**Question.** CI pin `docs/evidence/runtime-baseline-latest.json` (`commit_sha` `c081cfc87619042a73b64960b0cb61aeb2220baa`, `generated_at` `2026-08-26T16:03:50.067817+00:00`, `attested_by=ci`, run `32986441455`) lists documented knobs that `code_env_vars` does not. Are those flags no-ops?

**Method.** Diff the pin sets, then read `backend/src/aerobim/core/config/settings.py`. The scanner in `export_runtime_baseline._code_env_names` matched only `os.getenv` / `os.environ.get` / `os.environ[]`.

**Verdict.** **Scanner defect, not no-op.** Every name below is read by `Settings.from_env` via `_read_int` / `_read_bool` / `_read_float` / `_read_optional_int` / `_optional_bool` / `_env_prefer` / `_read_optional_int_prefer`, except `AEROBIM_GATES_ATTESTED` which is read by the baseline exporter itself (`os.environ.get` in `export_runtime_baseline.py`, not `settings.py`). CI previously enforced **code ⊆ docs**, not **docs ⊆ code**.

Publishable numbers stay the pin: backend 2663 collected / 2644 passed / 19 skipped / 0 failed; frontend 57; src 83887 LOC; tests 54607 LOC; `extraction_macro_f1=0.86` on the **fixture** corpus; 48 ports / 72 adapters / 63 DI tokens. This report does not mint a new pin.

## Pin names in documented_env_vars and not in code_env_vars

| Variable | Mechanism | File (approx.) | No-op? |
|---|---|---|---|
| `AEROBIM_ALLOW_ANONYMOUS_DEV` | `_read_bool` | `settings.py` ~929 | no |
| `AEROBIM_APPLY_SAMOLET_UPLOAD_CAPS` | `_read_bool` | `settings.py` ~106, ~119 | no |
| `AEROBIM_CLASH_AFFECTS_PASS` | `_optional_bool` | `settings.py` ~783 | no (forced true under pilot/production) |
| `AEROBIM_CLASH_MIN_AABB_VOLUME_M3` | `_read_float` | `settings.py` ~855 | no |
| `AEROBIM_CLASH_SKIP_TINY` | `_read_bool` | `settings.py` ~854 | no |
| `AEROBIM_DEBUG` | `_read_bool` | `settings.py` ~704 | no |
| `AEROBIM_GATES_ATTESTED` | `os.environ.get` | `export_runtime_baseline.py` ~82 | no (CI-only attestation) |
| `AEROBIM_KIMI_API_BASE_URL` | `_env_prefer` alias of `AEROBIM_VLM_API_BASE_URL` | `settings.py` ~940 | no |
| `AEROBIM_KIMI_API_KEY` | `_env_prefer` | `settings.py` ~942 | no |
| `AEROBIM_KIMI_CACHE_DIR` | `_env_prefer` | `settings.py` ~957 | no |
| `AEROBIM_KIMI_CACHE_NAMESPACE` | `_env_prefer` | `settings.py` ~959 | no |
| `AEROBIM_KIMI_CACHE_PROJECT` | `_env_prefer` | `settings.py` ~965 | no |
| `AEROBIM_KIMI_MODEL` | `_env_prefer` | `settings.py` ~943 | no |
| `AEROBIM_KIMI_REASONING_EFFORT` | `_env_prefer` | `settings.py` ~947 | no |
| `AEROBIM_LLM_429_RETRIES` | `_read_int` | `settings.py` ~998 | no |
| `AEROBIM_LLM_ADVISORY_MAX_ISSUES` | `_read_int` | `settings.py` ~997 | no |
| `AEROBIM_LLM_DATA_LOGGING_ENABLED` | `_read_bool` | `settings.py` ~995 | no |
| `AEROBIM_LLM_MAX_COMPLETION_TOKENS` | `_read_int` | `settings.py` ~984 | no |
| `AEROBIM_LLM_MAX_CONCURRENT` | `_read_int` | `settings.py` ~996 | no |
| `AEROBIM_LLM_MAX_TOKENS_PER_CALL` | `_read_int` | `settings.py` ~981 | no |
| `AEROBIM_LLM_MAX_TOKENS_PER_DAY` | `_read_int` | `settings.py` ~983 | no |
| `AEROBIM_LLM_MAX_TOKENS_PER_RUN` | `_read_int` | `settings.py` ~982 | no |
| `AEROBIM_LLM_SEND_SEED` | `_read_bool` | `settings.py` ~990 | no |
| `AEROBIM_MAX_IFC_BYTES` | `_read_int` | `settings.py` ~863 | no |
| `AEROBIM_MAX_MODEL_BYTES` | `_read_int` | `settings.py` ~869 | no |
| `AEROBIM_MAX_OFFICE_BYTES` | `_read_int` | `settings.py` ~865 | no |
| `AEROBIM_MEP_AABB_FILTER` | `_read_bool` | `settings.py` ~936 | no |
| `AEROBIM_PORT` | `_read_int` | `settings.py` ~837 | no |
| `AEROBIM_REPORT_TTL_DAYS` | `_read_optional_int` | `settings.py` ~852 | no |
| `AEROBIM_REQUIRE_CLASH` | `_optional_bool` | `settings.py` ~782 | no (forced true under pilot/production) |
| `AEROBIM_REQUIRE_MEP_SYSTEM_CLASH` | `_optional_bool` | `settings.py` ~786 | no (forced true under pilot/production) |

Count vs the spoken «29»: the pin symmetric difference is the set above (31 names). Speech should use the table, not a rounded count.

## Fix landed in this tree (not a new CI pin)

1. Scanner reads helper calls and `_env_prefer` aliases; also scans `export_runtime_baseline.py` for `AEROBIM_GATES_ATTESTED`.
2. CI gate is bidirectional: **code ⊆ (README Configuration ∪ `audit/internal_env_vars.json`)** and **documented ⊆ code**.
3. Live `code_env_vars` may be a **superset** of the pinned artifact until GitHub Actions regenerates `runtime-baseline-latest.json`. Local pytest is not publishable evidence.
4. Extra helper-read names that are not operator-facing stay in `audit/internal_env_vars.json` (VLM primary names, ODA legal gate, baked pilot quotas).

## Still open

- A new `attested_by=ci` pin after this scanner lands. Do not overwrite the JSON locally.
- GitHub repository description still says `NO_GO` without the README gloss (owner UI, not this file).
