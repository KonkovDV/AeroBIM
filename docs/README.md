---
title: "Документация AeroBIM — вход для жюри Техлаба и МИК"
status: active
version: "3.5.0"
last_updated: "2026-08-18"
tags: [aerobim, documentation, samolet, techlab, jury]
claim_boundary: "Public GitHub = TechLab jury pack only. Checkpoint NO_GO. Eng readiness ≠ customer GO. Working/debug docs stay local, outside git."
---

# Документация

Checkpoint: **`NO_GO`**. Стадия МИК — **доработка**. Это не «система не запускается»: на учебном комплекте проверка работает. Нет корпуса Самолёта, двух разметчиков, подписанного профиля приёмки и подтверждения импорта в СОД.

Компактная карта: [`TIER0_INDEX.md`](TIER0_INDEX.md). Пакет пяти полей формы: [`../submission/README.md`](../submission/README.md).

## С чего начать

| Документ | Зачем |
|---|---|
| [`docs.md`](docs.md) | Техническое обоснование |
| [`TIER0_INDEX.md`](TIER0_INDEX.md) | Короткая карта пакета |
| [`tz/TZ_COMPLIANCE_MATRIX_2026.md`](tz/TZ_COMPLIANCE_MATRIX_2026.md) | Построчное соответствие ТЗ |
| [`../submission/TZ_REQUIREMENTS_COVERAGE_2026_08.md`](../submission/TZ_REQUIREMENTS_COVERAGE_2026_08.md) | Карта ТЗ этой подачи |
| [`pilot-claim-boundary-2026.md`](pilot-claim-boundary-2026.md) | Что проверено, а что запланировано |
| [`../audit/reports/CRITICAL_BLOCKERS.md`](../audit/reports/CRITICAL_BLOCKERS.md) | RT-001 / RT-002 / RT-003 |
| [`demo/KT2_JURY_FAQ_2026_08_12.md`](demo/KT2_JURY_FAQ_2026_08_12.md) | Формула речи |
| [`architecture/ADR-001-verdict-ownership-2026.md`](architecture/ADR-001-verdict-ownership-2026.md) | Кто ставит технический статус |
| [`evidence/DATA_STATEMENT_2026_08.md`](evidence/DATA_STATEMENT_2026_08.md) | Какие данные есть и каких нет |
| [`evidence/README.md`](evidence/README.md) | Цитируемые учебные прогоны |

## ТЗ и архитектура

| Документ | Зачем |
|---|---|
| [`tz/TZ_SAMOLET_TECHLAB_TASK_07_V2_2026.md`](tz/TZ_SAMOLET_TECHLAB_TASK_07_V2_2026.md) | Текст ТЗ задачи 07 |
| [`tz/README.md`](tz/README.md) | Индекс пакета ТЗ |
| [`architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md`](architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md) | Целевая архитектура |
| [`capability-claim-matrix-2026.md`](capability-claim-matrix-2026.md) | Что можно и нельзя говорить |
| [`../audit/reports/CLAIMS_LOCK_2026_07_17.md`](../audit/reports/CLAIMS_LOCK_2026_07_17.md) | Запрещённые формулировки |

## Показ и доказательства

| Документ | Зачем |
|---|---|
| [`demo/`](demo/) | Ответы на жёсткие вопросы |
| [`demo/KT2_TASK07_COMPARISON_2026_08.md`](demo/KT2_TASK07_COMPARISON_2026_08.md) | Сравнение пяти решений; цифры конкурентов — их заявления |
| [`demo/KT2_CORPUS_SSOT_2026_08.md`](demo/KT2_CORPUS_SSOT_2026_08.md) | Замороженная строка открытых прокси |
| [`partners/_08_15.md`](partners/_08_15.md) | Четыре пункта запроса заказчику |
| [`quality/RED_TEAM_JURY_MIK_NOVATOR_KT2_2026_08_15.md`](quality/RED_TEAM_JURY_MIK_NOVATOR_KT2_2026_08_15.md) | Разбор атак жюри и МИК |
| [`quality/INTERPRETATION_USE_LEDGER_2026_08.md`](quality/INTERPRETATION_USE_LEDGER_2026_08.md) | Что цифры имеют право значить |
| [`pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md`](pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md) | Как измерять качество, когда появятся данные |

Ролик 2–3 мин не записываем и не прилагаем. Показ — живая команда `run_demo_ifc_acceptance_gate`.

Рабочие журналы, черновики и коммерческие контакты в этот каталог не входят.
