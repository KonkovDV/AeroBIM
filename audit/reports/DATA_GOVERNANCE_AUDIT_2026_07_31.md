# Data governance audit — 2026-07-31

See also: `docs/data-governance-2026.md`, `docs/ai-safety-and-document-ingestion-2026.md`.

## Inventory (engineering)

| Data | Storage | Logs | Prompts | BCF | External |
|---|---|---|---|---|---|
| Uploaded IFC/PDF | object store / FS | hashes/paths | default deny customer→cloud | topics from findings | deny by default |
| Reports | FS/PG | metadata | n/a | export | n/a |
| Audit trail | JSONL | structured | n/a | n/a | n/a |

## Rules

- Masking ≠ anonymization.
- TTL via `AEROBIM_REPORT_TTL_DAYS` (optional).
- No-cloud / no-LLM modes: hybrid policy + capability disabled.
- Deletion/purge: implement per deployment runbook — customer procedure BLOCKED until signed DPA.

## Model-call audit primacy (Yandex AI Studio)

Vendor Q&A states request history is **not retrievable** from platform logs (data stored anonymized, not account-bound). Therefore AeroBIM `audit_event` (prompt/response hashes, model URI, `x-data-logging-enabled: false` fact, token counters, correlation id) is the **primary** record of model calls — not a duplicate of vendor history. See `audit/llm_provider_policy.json` (`vendor_request_history_retrievable: false`) and [`../../docs/architecture/YANDEX_AI_STUDIO_GRANT_KT2_2026_08_03.md`](../../docs/architecture/YANDEX_AI_STUDIO_GRANT_KT2_2026_08_03.md).

## Status

Governance docs exist; customer-specific retention/DPA = BLOCKED.
