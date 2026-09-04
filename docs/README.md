---
title: "Документация AeroBIM — вход для жюри Техлаба и МИК"
status: active
version: "3.7.0"
last_updated: "2026-09-04"
tags: [aerobim, documentation, samolet, techlab, jury]
claim_boundary: "Public GitHub = TechLab jury pack only. Checkpoint GO; customer_go false. Eng readiness ≠ customer GO. Working/debug docs stay local, outside git."
---

# Документация

Checkpoint: **`NO_GO`**. Стадия МИК — **доработка**. На учебном комплекте проверка работает. Корпуса Самолёта, разметчиков, подписанного профиля Самолёта (RT-002c) и подтверждения импорта в СОД нет. Публичные IDS экспертизы — линейка измерения (RT-002a). EIR v4 на канале — носитель (RT-002b), не «RT-002 CLOSED».

Полная карта: [`TIER0_INDEX.md`](TIER0_INDEX.md). Пакет формы: [`../submission/README.md`](../submission/README.md).

Показ для сидящего члена жюри — команда `python -m aerobim.tools.run_kt3_jury` (не ролик). Оболочка ревью (`../frontend/`) — ноутбук ИТ-ментора, не СОД.

| Документ | Зачем |
|---|---|
| [`docs.md`](docs.md) | Техническое обоснование |
| [`demo/KT3_JURY_FAQ_2026_08_25.md`](demo/KT3_JURY_FAQ_2026_08_25.md) | Карточка речи КТ#3 |
| [`tz/TZ_COMPLIANCE_MATRIX_2026.md`](tz/TZ_COMPLIANCE_MATRIX_2026.md) | Соответствие ТЗ (строка Web UI — **partial**, не done) |
| [`../submission/TZ_REQUIREMENTS_COVERAGE_2026_08.md`](../submission/TZ_REQUIREMENTS_COVERAGE_2026_08.md) | Карта этой подачи |
| [`pilot-claim-boundary-2026.md`](pilot-claim-boundary-2026.md) | Что проверено, а что нет |
| [`../audit/reports/CRITICAL_BLOCKERS.md`](../audit/reports/CRITICAL_BLOCKERS.md) | RT-001 / RT-002a·b / RT-003 (тома измерения vs остаток) |
| [`evidence/rt-blocker-volumes-2026-09.md`](evidence/rt-blocker-volumes-2026-09.md) | Чем заменили Самолёта; что нельзя подменить |
| [`architecture/ADR-001-verdict-ownership-2026.md`](architecture/ADR-001-verdict-ownership-2026.md) | Кто ставит технический статус |
| [`architecture/ADR-005-customer-data-handling-2026.md`](architecture/ADR-005-customer-data-handling-2026.md) | Производные канала заказчика не в публичный git |
| [`evidence/DATA_STATEMENT_2026_08.md`](evidence/DATA_STATEMENT_2026_08.md) | Какие данные есть |
| [`../frontend/README.md`](../frontend/README.md) | Оболочка ревью в браузере |

Ролик не записываем и не прилагаем.
