<!-- claims-lint: allow-file reason="KT#3 delivery BOM; MIT handoff; no customer files; NO_GO" -->
---
title: "KT#3 delivery bill of materials"
date: "2026-08-29"
last_updated: "2026-08-30"
status: active
version: "1.0.1"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  What this git tree can hand over. Not a Partner CDE import. Not customer
  files. Not exclusive-rights clearance. Checkpoint NO_GO.
---

# Перечень поставки КТ#3 (минимум для Б5)

П. 6.3 Положения может предусматривать передачу исключительных прав без доплаты
к призу. Этот файл **не** оформляет такую передачу и **не** обещает патентный
контур. LICENSE сейчас **MIT**. Развилка п. 6.3:
[`ADR-004-prize-ip-mit-fork-2026.md`](../architecture/ADR-004-prize-ip-mit-fork-2026.md)
(proposed; LICENSE не меняем).

## Входит

| Артефакт | Где | Что это не значит |
|---|---|---|
| Исходный код движка (MIT) | `backend/`, `frontend/` | Не hosted SaaS и не коннектор СОД |
| Учебный комплект / фикстуры | `samples/` | Не корпус заказчика |
| Живой показ | `python -m aerobim.tools.run_kt3_jury` | `passed=false`; не Checkpoint GO |
| Карта для жюри | [`../TIER0_INDEX.md`](../TIER0_INDEX.md) | Не акт пилота |
| Протокол измерения | [`PROTOCOL_QUALITY_ACCEPTANCE_TASK07_2026_08.md`](../partners/PROTOCOL_QUALITY_ACCEPTANCE_TASK07_2026_08.md) | Не подписан партнёром |
| CI pin | [`../evidence/runtime-baseline-latest.json`](../evidence/runtime-baseline-latest.json) | `attested_by=ci`; не local pytest |
| Обложка валидации фикстуры | [`KT3_FIXTURE_VALIDATION_COVER_2026_08.md`](KT3_FIXTURE_VALIDATION_COVER_2026_08.md) | Не метрики партнёра |
| Помеченный эффект | [`ECONOMIC_MODEL_LABELED_ASSUMPTIONS_2026_08.md`](../partners/ECONOMIC_MODEL_LABELED_ASSUMPTIONS_2026_08.md) | Часы пустые |

## Не входит

- Файлы заказчика, хеш-пакет, внутренние ОРД.
- Веса внешних LLM/VLM и обещание включённого облачного вывода.
- Native RVT / NWD / DWG / `.lir` solver.
- OIDC BFF, импорт BCF в СОД (T2).
- Подпись профиля приёмки Самолёта.

Воспроизведение: [`../TIER0_INDEX.md`](../TIER0_INDEX.md) +
[`../demo/KT3_OPERATOR_RUNBOOK_2026_08_25.md`](../demo/KT3_OPERATOR_RUNBOOK_2026_08_25.md).
