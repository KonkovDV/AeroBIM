---
title: "Поле «Документация» — состав сопроводительного пакета"
status: active
version: "1.1.0"
last_updated: "2026-09-15"
claim_boundary: >
  Documentation index only. Checkpoint GO; customer_go false; RT-001/002/003 OPEN.
  Fixture evidence ≠ customer корпус.
---

# Документация

**Ссылка для формы:** https://github.com/KonkovDV/AeroBIM/tree/main/docs

**Формула стадии (дословно; источник — [карточка речи для жюри](../../docs/demo/KT2_JURY_FAQ_2026_08_12.md)):** Мы на стадии доработки контура заказчика. Одна команда показывает находку с доказательствами на учебном комплекте. Валидация эффективности и внедрение у назначающей стороны ещё не начались. Checkpoint `GO` — регуляторно-измерительный MVP. `customer_go` остаётся false, пока нет независимого размеченного корпуса, двух разметчиков, подписанного профиля назначающей стороны и подтверждения импорта в СОД.

Порядок чтения для жюри — [`../../docs/TIER0_INDEX.md`](../../docs/TIER0_INDEX.md). Дека подачи: [`../03-presentation/AeroBIM_demo_day.pdf`](../03-presentation/AeroBIM_demo_day.pdf). Архив КТ#2: [`../03-presentation/aerobim_kt2.pptx`](../03-presentation/aerobim_kt2.pptx). Речь КТ#3 — [`../../docs/demo/KT3_JURY_FAQ_2026_08_25.md`](../../docs/demo/KT3_JURY_FAQ_2026_08_25.md); речь демо-дня — [`../../docs/demo/DEMO_DAY_SPEECH_LOCK_2026_09.md`](../../docs/demo/DEMO_DAY_SPEECH_LOCK_2026_09.md).

## 1. Обязательное ядро

| Документ | Роль |
|---|---|
| [`../../docs/docs.md`](../../docs/docs.md) | Техническое обоснование |
| [`../../docs/tz/TZ_COMPLIANCE_MATRIX_2026.md`](../../docs/tz/TZ_COMPLIANCE_MATRIX_2026.md) | Построчная матрица ТЗ ↔ продукт |
| [`TZ_REQUIREMENTS_COVERAGE_2026_08.md`](../TZ_REQUIREMENTS_COVERAGE_2026_08.md) | Карта ТЗ этой подачи |
| [`../../docs/evidence/tz-matrix-status-latest.json`](../../docs/evidence/tz-matrix-status-latest.json) | Снимок возможностей на учебной стенке; `ids=ok` ≠ профиль заказчика |
| [`../../docs/pilot-claim-boundary-2026.md`](../../docs/pilot-claim-boundary-2026.md) | Что проверено, а что запланировано |
| [`../../audit/reports/CRITICAL_BLOCKERS.md`](../../audit/reports/CRITICAL_BLOCKERS.md) | RT-001/002/003 и `customer_go` false |
| [`../../docs/quality/INTERPRETATION_USE_LEDGER_2026_08.md`](../../docs/quality/INTERPRETATION_USE_LEDGER_2026_08.md) | Что цифры вправе значить (заморозка `f9389bf`) |
| [`../../docs/demo/DEMO_DAY_SPEECH_LOCK_2026_09.md`](../../docs/demo/DEMO_DAY_SPEECH_LOCK_2026_09.md) | Что можно сказать 29–30.09 |
| [`../../docs/quality/DEMO_DAY_DECK_REDLINE_2026_09.md`](../../docs/quality/DEMO_DAY_DECK_REDLINE_2026_09.md) | Красная черта деки 13.09; не слайд жюри |

## 2. Разделы ТЗ, закрытые отдельными документами

ТЗ оставляет пять разделов как `TBD`. Ниже — **предложения команды**, не закрытие ТЗ заказчиком. Заказчик может принять или переопределить:

Предложения команды по пяти разделам ТЗ, которые заказчик оставил открытыми (не закрытие ТЗ): архитектура, сборка, образ решения, презентация, сопроводительная документация — в [`../../docs/tz/README.md`](../../docs/tz/README.md).

## 3. Методика измерения качества

| Документ | Что задаёт |
|---|---|
| [`../../docs/pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md`](../../docs/pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md) | Как мерить качество, когда появятся данные заказчика |
| [`../../docs/partners/BEFORE_AFTER_MEASUREMENT_PROTOCOL_2026_09.md`](../../docs/partners/BEFORE_AFTER_MEASUREMENT_PROTOCOL_2026_09.md) | Журнал «до / после»; на фикстуре заполнено только машинное время |
| [`../../docs/sla-benchmark-protocol-2026.md`](../../docs/sla-benchmark-protocol-2026.md) | Как мерить стенные часы; учебный p95 ≠ SLA заказчика |

Методика опубликована **до** получения данных заказчика — чтобы цифры нельзя было подогнать после факта.

## 4. Нормативный контур

[`../../docs/regulatory-baseline-2026.md`](../../docs/regulatory-baseline-2026.md) — срез норм. ГОСТ Р 21.101-2026 (в силе с **1 апреля 2026**, приказ № 129-ст) п. 8.2.4 (GUID документа) совпадает с тем, как мы ведём находки к устойчивому идентификатору; полного соответствия стандарту не заявляем. Дата ГОСТ не смешивается с обязательной подачей ЦИМ АГР в Москве (**2 апреля 2026**; 17-ПП + совместное распоряжение ДИТ/ДГП № ДГП-Р-1/26/64-16-6/26 от 16.01.2026). Официальные IDS экспертизы — линейка измерения (RT-002a); EIR v4 на канале — носитель (RT-002b); профиль приёмки «заказчика канала» не подписан (RT-002c OPEN). Не писать недифференцированно «RT-002 CLOSED».

Полноты «всех норм» не заявляем: машиночитаемо проверяется то, что выражено в IDS или rule pack.

## 5. Что запрошено у заказчика

[`../../docs/partners/CUSTOMER_ACCEPTANCE_PROFILE_V0_1_2026_08_15.md`](../../docs/partners/CUSTOMER_ACCEPTANCE_PROFILE_V0_1_2026_08_15.md) — четыре пункта запроса: комплект одной ревизии, подписанный профиль приёмки, два инженера-разметчика, целевая СОД для BCF. Без них измерение на данных заказчика невозможно, и `customer_go` остаётся false.

Диапазоны железа и людей (не КП и не Гант): [`../../docs/deployment-sizing-and-cost-2026.md`](../../docs/deployment-sizing-and-cost-2026.md).
