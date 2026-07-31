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

## Status

Governance docs exist; customer-specific retention/DPA = BLOCKED.
