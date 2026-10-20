---
title: "Документация AeroBIM — вход для жюри Техлаба и МИК"
status: active
version: "3.7.1"
last_updated: "2026-10-20"
tags: [aerobim, documentation, customer, techlab, jury]
claim_boundary: "Public GitHub = TechLab jury pack only. Checkpoint GO; customer_go false. Eng readiness ≠ customer GO. Operator notes stay local, outside git."
---

# Документация

На учебном комплекте проверка уже поднимает находку. Checkpoint — **`GO`** (`regulatory_measurement_mvp`). Публичные IDS экспертизы — линейка измерения (RT-002a). EIR v4 на канале — носитель (RT-002b CLOSED). RT-002a и RT-002c называйте раздельно.

Полная карта: [`TIER0_INDEX.md`](TIER0_INDEX.md). Пакет формы: [`../submission/README.md`](../submission/README.md).

Показ для сидящего члена жюри — живая команда `python -m aerobim.tools.run_kt3_jury`. Оболочка ревью (`../frontend/`) — браузерный стол эксперта.

| Документ | Зачем |
|---|---|
| [`docs.md`](docs.md) | Техническое обоснование |
| [`demo/KT3_JURY_FAQ_2026_08_25.md`](demo/KT3_JURY_FAQ_2026_08_25.md) | Карточка речи КТ#3 |
| [`tz/TZ_COMPLIANCE_MATRIX_2026.md`](tz/TZ_COMPLIANCE_MATRIX_2026.md) | Карта строк ТЗ |
| [`../submission/TZ_REQUIREMENTS_COVERAGE_2026_08.md`](../submission/TZ_REQUIREMENTS_COVERAGE_2026_08.md) | Карта этой подачи |
| [`pilot-claim-boundary-2026.md`](pilot-claim-boundary-2026.md) | Граница заявлений |
| [`../audit/reports/CRITICAL_BLOCKERS.md`](../audit/reports/CRITICAL_BLOCKERS.md) | RT-001 / RT-002a·b / RT-003 |
| [`evidence/rt-blocker-volumes-2026-09.md`](evidence/rt-blocker-volumes-2026-09.md) | Чем измеряли вместо канала |
| [`architecture/ADR-001-verdict-ownership-2026.md`](architecture/ADR-001-verdict-ownership-2026.md) | Кто ставит технический статус |
| [`architecture/ADR-005-customer-data-handling-2026.md`](architecture/ADR-005-customer-data-handling-2026.md) | Производные канала заказчика не в публичный git |
| [`evidence/DATA_STATEMENT_2026_08.md`](evidence/DATA_STATEMENT_2026_08.md) | Какие данные есть |
| [`../frontend/README.md`](../frontend/README.md) | Оболочка ревью в браузере |

Показ идёт живой командой.
