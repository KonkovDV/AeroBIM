---
title: "Поле «Документация» — состав сопроводительного пакета"
status: active
version: "1.0.2"
last_updated: "2026-08-17"
claim_boundary: >
  Documentation index only. Checkpoint NO_GO; RT-001/002/003 OPEN.
  Fixture evidence ≠ customer корпус.
---

# Документация

**Ссылка для формы:** https://github.com/KonkovDV/AeroBIM/tree/main/docs

**Формула стадии (дословно, SSOT [`../../docs/demo/KT2_JURY_FAQ_2026_08_12.md`](../../docs/demo/KT2_JURY_FAQ_2026_08_12.md)):** Мы на стадии доработки. Одна команда показывает находку с доказательствами на учебном комплекте. Валидация эффективности и внедрение ещё не начались. `NO_GO` сохраняется, пока нет корпуса Самолёта, двух разметчиков, подписанного профиля приёмки и подтверждения импорта в СОД.

Порядок чтения для жюри — [`../../docs/TIER0_INDEX.md`](../../docs/TIER0_INDEX.md).

## 1. Обязательное ядро

| Документ | Роль |
|---|---|
| [`../../docs/docs.md`](../../docs/docs.md) | Техническое обоснование проекта (RU) |
| [`../../docs/tz/TZ_COMPLIANCE_MATRIX_2026.md`](../../docs/tz/TZ_COMPLIANCE_MATRIX_2026.md) | Построчная матрица ТЗ ↔ продукт со статусами |
| [`TZ_REQUIREMENTS_COVERAGE_2026_08.md`](../TZ_REQUIREMENTS_COVERAGE_2026_08.md) | Карта ТЗ этой подачи |
| [`../../docs/pilot-claim-boundary-2026.md`](../../docs/pilot-claim-boundary-2026.md) | Что проверено, а что запланировано |
| [`../../docs/capability-claim-matrix-2026.md`](../../docs/capability-claim-matrix-2026.md) | Разрешённые и запрещённые формулировки |
| [`../../audit/reports/CRITICAL_BLOCKERS.md`](../../audit/reports/CRITICAL_BLOCKERS.md) | RT-001/002/003 и статус `NO_GO` |
| [`../../docs/ENGINEERING_STATUS_2026_08.md`](../../docs/ENGINEERING_STATUS_2026_08.md) | Инженерный статус на дату |
| [`../../docs/quality/INTERPRETATION_USE_LEDGER_2026_08.md`](../../docs/quality/INTERPRETATION_USE_LEDGER_2026_08.md) | Kane IUA: что цифры вправе значить (заморозка `f9389bf`) |

## 2. Разделы ТЗ, закрытые отдельными документами

ТЗ оставляет пять разделов как `TBD`. Ниже — **предложения команды**, не закрытие ТЗ заказчиком. Заказчик может принять или переопределить:

| Раздел ТЗ | Наш документ |
|---|---|
| Требования к архитектуре решения | [`../../docs/tz/TZ_ARCHITECTURE_REQUIREMENTS_2026.md`](../../docs/tz/TZ_ARCHITECTURE_REQUIREMENTS_2026.md) |
| Требования к коду и сборке | [`../../docs/tz/TZ_BUILD_AND_QUALITY_2026.md`](../../docs/tz/TZ_BUILD_AND_QUALITY_2026.md) |
| Образ финального решения | [`../../docs/tz/TZ_SOLUTION_IMAGE_AND_PRESENTATION_2026.md`](../../docs/tz/TZ_SOLUTION_IMAGE_AND_PRESENTATION_2026.md) §1 |
| Требования к презентации | тот же документ §2–4 |
| Требования к сопроводительной документации | [`../../docs/tz/TZ_ACCOMPANYING_DOCS_2026.md`](../../docs/tz/TZ_ACCOMPANYING_DOCS_2026.md) |

Предложения по незакрытым пунктам ТЗ: [`../../docs/partners/TZ_TBD_PROPOSALS_TASK07_2026_08.md`](../../docs/partners/TZ_TBD_PROPOSALS_TASK07_2026_08.md).

## 3. Методика измерения качества

| Документ | Что задаёт |
|---|---|
| [`../../docs/pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md`](../../docs/pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md) | Протокол измерения: разметка, TP/FP, согласие экспертов |
| [`../../docs/partners/PROTOCOL_QUALITY_ACCEPTANCE_TASK07_2026_08.md`](../../docs/partners/PROTOCOL_QUALITY_ACCEPTANCE_TASK07_2026_08.md) | Приёмка качества по Задаче 07 |
| [`../../docs/sla-benchmark-protocol-2026.md`](../../docs/sla-benchmark-protocol-2026.md) | Как корректно мерить время обработки комплекта |
| [`../../docs/quality/RT001_LABELING_PROTOCOL_RT026_2026_08_03.md`](../../docs/quality/RT001_LABELING_PROTOCOL_RT026_2026_08_03.md) | Разметка корпуса под RT-001 |

Методика опубликована **до** получения данных заказчика — чтобы цифры нельзя было подогнать после факта.

## 4. Нормативный контур

[`../../docs/regulatory-baseline-2026.md`](../../docs/regulatory-baseline-2026.md) — срез норм; ГОСТ Р 21.101-2026 п. 8.2.4 (GUID документа) разобран в [`../../docs/evidence/N2_GUID_GOST_21_101_2026_2026_08.md`](../../docs/evidence/N2_GUID_GOST_21_101_2026_2026_08.md). Официальные IDS Мособлгосэкспертизы подключены как эталонный набор; профиль приёмки «Самолёта» не подписан (RT-002 OPEN).

Полноты «всех норм» не заявляем: машиночитаемо проверяется то, что выражено в IDS или rule pack.

## 5. Что запрошено у заказчика

[`../../docs/partners/_08_15.md`](../../docs/partners/_08_15.md) — четыре пункта запроса: комплект одной ревизии, подписанный профиль приёмки, два инженера-разметчика, целевая СОД для BCF. Без них измерение на данных заказчика невозможно, и Checkpoint остаётся `NO_GO`.
