# Checklist self-audit — 2026-08-03 (post-remediation)

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | `verdict_impact` `none` + `init=False` | PASS | `hybrid/audit_event.py`; `test_hybrid_audit_event` |
| 2 | Named OFF==ON includes Studio | PASS | `test_advisory_vlm_off_equals_on.test_llm_studio_flag_does_not_change_verdict_on_uc_path` |
| 3 | Profile does not widen `decide_route` | PASS | matrix unchanged; schema≥1.1 only adds `model_revision` pin |
| 4 | Missing `model_revision` fail-closed at boot | PASS | `Settings.from_env` RuntimeError; `llm_local_ready` requires revision; ProviderRegistry schema≥1.1 |
| 5 | Model unavailable → SKIPPED | PASS | compose maps `transport_error:*` → `SKIPPED`/`model_unavailable` |
| 6 | `/v1/system/capabilities` | PASS | `llm_advisory.status=skipped`, `studio_profile`, `requires_model_revision` |
| 7 | Secrets / env docs | PASS | no key in repo; `.env.example` + README Configuration table; audit redaction |
| 8 | SSRF / egress | PASS | remote=`safe_urlopen`; loopback=`safe_datastore_urlopen`; outbound invariant includes adapter |
| 9 | Token budget fail-closed | PASS | `LlmTokenBudget` pre-call |
| 10 | README port/adapter/token counts | PASS | updated to **48 / 67 / 58** with SSOT pointer |
| 11 | Claims Lock / matrix / ENGINEERING_STATUS | PASS | Claims Lock 07-31 + forbidden wording + status row |
| 12 | offline_bundle | PASS (CI path unchanged) | no new network in offline path; LLM opt-in |

Focused pytest (this wave): **45 passed, 1 skipped**.
