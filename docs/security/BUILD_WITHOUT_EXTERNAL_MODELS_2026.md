<!-- claims-lint: allow-file reason="Offline / no-external-model build boundary; not a product accuracy claim; NO_GO" -->
---
title: "Build without external models"
date: "2026-08-27"
status: active
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Operator note for IB review. Default is no outbound advisory.
  samolet_pilot / production hard-disable LLM and VLM ready().
  Checkpoint GO; customer_go false.
---

# Сборка без внешних обращений к моделям

**Default.** `AEROBIM_LLM_ADVISORY_ENABLED` is `false`. `AEROBIM_VLM_ENABLED` is `false`. No Moonshot/Yandex call happens unless an operator turns a flag on **and** the sign-off profile allows it.

**What IB will see in the public inventory.** Deprecated Kimi aliases (`AEROBIM_KIMI_*`) remain in the README Configuration table so operators who still have those names in scripts are not surprised. They are aliases of `AEROBIM_VLM_*`. Seeing a name in a table is not an open socket.

**Who may enable egress.** Only `development` / `fixture` (and not `samolet_pilot` / `samolet_pilot_demo` / `moscow_agr_2026` / `production`). `Settings.llm_local_ready()` and `Settings.vlm_advisory_ready()` return `false` on those four profiles even if the enable flags are left on.

**Proof in CI.**

| Test | What it shows |
|---|---|
| `backend/tests/test_pilot_profile_blocks_external_llm_egress.py` | `samolet_pilot` + `AEROBIM_LLM_ADVISORY_ENABLED=true` → `llm_local_ready() is False` |
| same file, `test_pilot_profile_blocks_kimi_alias_vlm` | `AEROBIM_KIMI_K3_ENABLED=true` under `samolet_pilot` → `vlm_advisory_ready() is False` |
| `backend/tests/test_vlm_advisory_client.py::test_customer_profile_hard_disables_public_api` | VLM client path hard-disabled on pilot/production |
| `python -m aerobim.tools.offline_bundle` | Docker image-track smoke (CI job `offline-bundle-smoke` is in the attested gate set of the runtime baseline) |

**Possible destinations if someone enables advisory in development.** SSRF-gated. Built-in LLM allowlist includes loopback and Yandex AI Studio hosts; Alibaba/OpenAI hosts are forbidden. Moonshot (`api.moonshot.cn`) is not on the LLM allowlist; a VLM base URL must still pass `assert_safe_outbound_url` at boot.

**ADR-001.** LLM/VLM never write `summary.passed`.

**OIDC BFF.** Production browser SSO remains `DESIGNED / NOT_IMPLEMENTED` (default HTTP 501). That is a separate IB item; see README and `docs/security/PILOT_THREAT_MODEL_2026_07.md`.
