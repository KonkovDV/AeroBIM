---
title: "Red Team — Studio grant stamp/PII gate (2026-08-03)"
status: active
version: "1.5.0"
last_updated: "2026-08-03"
claim_boundary: "Self red-team. Checkpoint NO_GO. PII gate active; effectiveness on real sheets NOT_MEASURED."
---

# Red Team — Yandex Studio advisory contour (2026-08-03)

**Checkpoint:** **NO_GO**  
**Allowed claim:** «PII-гейт активен; эффективность на реальных листах не измерена»  
**Forbidden claim:** «ПДн гарантированно не уходят в облако»

## Closed this wave

| ID | Verdict |
|---|---|
| RT-BUDGET-01..04 | **MITIGATED** — `record_failed`, per-retry `check_before`, file ledger + `budget_tz` |
| RT-INJ-01/02 | **MITIGATED** — no model severity; data delimiters; VLM ungrounded → zero observations |
| RT-STAMP-14..16 | **MITIGATED** — `/Rotate` priors, overflow/area reject, role/crs/clip counters |
| RT-META-01 | **MITIGATED** — opaque UUIDv4 `x-client-request-id` |

## Still open (external)

RT-001 / RT-002 / RT-003 · Samolet sheet prior validation · DPA/C2 for CONFIDENTIAL
