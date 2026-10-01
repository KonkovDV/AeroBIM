# LLM data privacy

**claim_level:** policy note  
**Related:** `LlmDataPolicy` in `domain/llm_advisory.py`, Claims Lock

## Defaults

| Rule | Default |
|---|---|
| Customer package to cloud LLM | **Denied** unless explicit approval |
| Synthetic / public fixtures to mock providers | Allowed |
| Retention | Treat as unknown (`retention_unknown=true`) unless vendor DPA says otherwise |
| Secrets in prompts / logs | Forbidden (API keys, full confidential docs) |
| Advisory vs verdict | Advisory never flips Shared-gate `summary.passed` |

## Contour choices

1. **On-prem / local OpenAI-compat** — preferred for expertise orgs.  
2. **Cloud (Kimi / Yandex / …)** — only with written customer allowance and redaction policy.  
3. **Mock bench** — CI default; no network.

## Audit fields

Prefer `LlmAuditRecord` / run manifests: provider, model, latency, status, error_class, token_usage — **not** raw confidential prompts.

## Sprint 2 stance

Comparative artifacts stay `fixture_only` / `synthetic_only`. No invented customer privacy incidents or org names in git.
