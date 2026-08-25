---
title: "AeroBIM — карта для жюри Техлаба и МИК"
status: active
version: "4.7.3"
last_updated: "2026-08-25"
tags: [aerobim, documentation, tier-0, techlab]
claim_boundary: "Jury pack only. Checkpoint NO_GO until RT-001/002/003. Eng readiness ≠ customer GO."
---

# Карта для жюри Техлаба и МИК

**`NO_GO`.** Стадия МИК — **доработка**. На учебном комплекте проверка запускается. Локальный корпус Техлаба у владельца есть; **измерения** (κ, held-out, два разметчика) на комплекте Самолёта нет. Блокеры: [реестр](../audit/reports/CRITICAL_BLOCKERS.md). Граница заявлений: [что проверено](pilot-claim-boundary-2026.md). Кто ставит технический статус: [ADR-001](architecture/ADR-001-verdict-ownership-2026.md).

**Формула стадии (дословно; источник — [карточка речи](demo/KT2_JURY_FAQ_2026_08_12.md)):** Мы на стадии доработки. Одна команда показывает находку с доказательствами на учебном комплекте. Валидация эффективности и внедрение ещё не начались. `NO_GO` сохраняется, пока нет независимого размеченного корпуса, двух разметчиков, профиля приёмки (публичные IDS экспертизы — измерение; подпись Самолёта — внедрение) и подтверждения импорта в СОД.

**Объект КТ#3.** Речь и сценарий: [карточка КТ#3](demo/KT3_JURY_FAQ_2026_08_25.md) · [оператор](demo/KT3_OPERATOR_RUNBOOK_2026_08_25.md). Показ жюри = живой CLI из git, не диск `files/`. Re-scope: [без файлов в git](partners/_2026_08_23.md).

**Объект КТ#2.** Речь и пакет = текущий `main`. Цифры тестов = CI pin в [`docs/evidence/runtime-baseline-latest.json`](evidence/runtime-baseline-latest.json) (`attested_by=ci`: `commit_sha`, `tests_passed`, `tests_collected`). IUA freeze `f9389bf` (не HEAD). Прочие SHA на поверхностях — исторические. После правок документации pin может отставать на несколько коммитов до следующего прогона CI; локальные прогоны pytest не публикуем.

**Kane IUA.** На учебном комплекте можно показать содержание проверки, IDS с отказом при пропуске и открытый бенч **27/1026**. Нельзя: точность на комплекте заказчика, ТЗ >90%, SLA заказчика, MEP delivered, импорт в СОД, Checkpoint GO. Что цифры вправе значить: [Interpretation/Use](quality/INTERPRETATION_USE_LEDGER_2026_08.md). Заморозка `f9389bf`.

**Six desks.** Техлаб и МИК — основная аудитория этой карты. Разбор атак: [красная команда жюри × МИК](quality/RED_TEAM_JURY_MIK_NOVATOR_KT2_2026_08_15.md). Intake-form 5/5 полей ≠ Checkpoint GO.

| Документ | Зачем |
|---|---|
| [Техобоснование](docs.md) | Суть решения |
| [ТЗ заказчика](tz/TZ_SAMOLET_TECHLAB_TASK_07_V2_2026.md) | Текст задачи 07 |
| [Матрица ТЗ](tz/TZ_COMPLIANCE_MATRIX_2026.md) | Построчное соответствие |
| [Карта покрытия подачи](../submission/TZ_REQUIREMENTS_COVERAGE_2026_08.md) | Эта подача |
| [Граница заявлений](pilot-claim-boundary-2026.md) | Проверено vs план |
| [Карточка речи](demo/KT2_JURY_FAQ_2026_08_12.md) | Формула стадии |
| [Сравнение Задачи 07](demo/KT2_TASK07_COMPARISON_2026_08.md) | Пять решений; цифры конкурентов = их claims |
| [Враждебный QA](demo/) | Ответы на жёсткие вопросы |
| [Строка корпуса](demo/KT2_CORPUS_SSOT_2026_08.md) | Замороженные открытые прокси |
| [Поля обмена 10D](demo/KT2_10D_INTAKE_CONTRACT_2026_08.md) | Предложение; не коннектор 10D |
| [Запрос к Самолёту](partners/_08_15.md) | Четыре пункта, без которых NO_GO |
| [Разбор 24.08 10:45](partners/BRIEFING_2026_08_24_1045.md) | Клин + IDS; RT-002a/b; оффер; бинарные метрики |
| [Red Team 24.08](partners/_2026_08_24.md) | OSINT + атаки на формулировки; checkpoint NO_GO |
| [КТ#3 без файлов заказчика](partners/_2026_08_23.md) | Re-scope 23.08; ждать комплект в git не план |
| [Ответы Самолёта 25.08](partners/) | SSOT ответов; URL ≠ корпус; RT OPEN |
| [План по ответам 25.08](roadmap/SAMOLET_ANSWERS_WORKPLAN_2026_08_25.md) | Фазы A–D; не закрывает RT |
| [Карточка речи КТ#3](demo/KT3_JURY_FAQ_2026_08_25.md) | 30 с + 8–12 мин; ТЗ vs roadmap; стоп-лист |
| [Сценарий оператора КТ#3](demo/KT3_OPERATOR_RUNBOOK_2026_08_25.md) | Трек A жюри / трек B NDA; две ноги |
| [Карта покрытия КР дома 5](evidence/-kr13-coverage-map-2026-08.md) | `coverage_map_only`; не RT-001 |
| [Наука + OSINT корпуса Техлаба](research/TECHNILAB_ACADEMIC_OSINT_2026_08_25.md) | Литература 05–08.2026; новости Самолёта; файлы ≠ RT CLOSED |
| [Глубокий план Техлаба](roadmap/TECHNILAB_DEEP_WORKPLAN_2026_08_25.md) | C0–C9; coverage map; dual rater; MEP/арматура ask |
| [ADR-001](architecture/ADR-001-verdict-ownership-2026.md) | Кто пишет `summary.passed` |
| [Итоговый вердикт](quality/RED_TEAM_FINAL_VERDICT_2026_08_16.md) | Checkpoint NO_GO |
| [Красная команда жюри / МИК](quality/RED_TEAM_JURY_MIK_NOVATOR_KT2_2026_08_15.md) | Стадия = доработка |
| [Заявление о данных](evidence/DATA_STATEMENT_2026_08.md) | Что есть; открытые бенчи ≠ RT-001 |

Пять полей формы: [пакет подачи](../submission/README.md). Дека: [`aerobim_kt2.pptx`](../submission/03-presentation/aerobim_kt2.pptx) / [`aerobim_kt2.pdf`](../submission/03-presentation/aerobim_kt2.pdf). Ролик 2–3 мин **не записываем и не прилагаем.** Показ — `run_demo_ifc_acceptance_gate`.
