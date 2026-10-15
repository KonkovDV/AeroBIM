<!-- claims-lint: allow-file reason="Jury speech stop-list; Checkpoint GO ≠ customer_go; no Kontur scorecard" -->
---
title: "Jury speech checklist (AeroBIM)"
status: active
version: "1.0.0"
last_updated: "2026-10-15"
---

# Чеклист речи жюри (AeroBIM)

Дословно **формула стадии** — [`../pilot-claim-boundary-2026.md`](../pilot-claim-boundary-2026.md).
FAQ: [`KT3_JURY_FAQ_2026_08_25.md`](KT3_JURY_FAQ_2026_08_25.md) · [`DEMO_DAY_SPEECH_LOCK_2026_09.md`](DEMO_DAY_SPEECH_LOCK_2026_09.md).

## Checkpoint GO ≠ customer_go

- Можно: «Checkpoint GO — регуляторно-измерительный MVP».
- Нельзя: `customer_go=true`, «внедрено», «принято заказчиком», «RT-001/002/003 CLOSED» без буквы тома.
- OPEN тома: **RT-001b/c**, **RT-002c**, **RT-003c** (`mep_system_clash` NOT_VERIFIED), **CDE T2** (`claim_allowed=false`).

## BCF / СОД

- Можно: «структурный BCF T1 AVAILABLE; импорт в СОД NOT_VERIFIED».
- Нельзя: «BCF ready for CDE», «CDE interoperable», «интеграция с СОД/10D готова», «доставлено в СОД» по HTTP 2xx.

## Отказ системы ≠ нарушение

- SKIPPED / NOT_VERIFIED / FAILED capability — не «эксперт нашёл дефект».
- Advisory / низкая confidence — не `summary.passed` (ADR-001).
- Подтверждение находки — только человек (HITL), с reason_code где требуется.

## Стоп-лист (AeroBIM ∪ не смешивать Kontur)

Запрещено в голосе и на слайдах AeroBIM:

- accuracy / полнота продукта >90% на заказчике; SLA ≤30 мин у заказчика
- native DWG/RVT/NWD; MEP delivered; calc correctness; УКЭП trust chain
- masking = анонимизация; LLM/VLM пишет вердикт; «целиком MIT»; «лучше Solibri»
- метрики Контура: `59/132`, Gate I/J/K/L, `tz_low`, CA≥0.95 SILVER как метрика AeroBIM
- цифры baseline без ссылки на [`../evidence/runtime-baseline-latest.json`](../evidence/runtime-baseline-latest.json)
- orphan SHA (`313e050…`) как «текущий HEAD»

Прогон: `python scripts/lint_claims.py --full-docs --matrix-guard --claim-boundary-guard`.
