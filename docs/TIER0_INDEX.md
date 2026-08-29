---
title: "AeroBIM — карта для жюри Техлаба и МИК"
status: active
version: "4.8.12"
last_updated: "2026-08-29"
tags: [aerobim, documentation, tier-0, techlab]
claim_boundary: "Jury pack only. Checkpoint NO_GO until RT-001/002/003. Eng readiness ≠ customer GO."
---

# Карта для жюри Техлаба и МИК

**`NO_GO`.** Стадия МИК — **доработка**. На учебном комплекте проверка запускается. Измерений (κ, held-out, два разметчика) на комплекте Самолёта **в git** нет. Канал 25.08 получен — **не** говорить «нет данных заказчика»; хеш-пакет в репозитории отсутствует. Блокеры: [реестр](../audit/reports/CRITICAL_BLOCKERS.md). Граница заявлений: [что проверено](pilot-claim-boundary-2026.md). Кто ставит технический статус: [ADR-001](architecture/ADR-001-verdict-ownership-2026.md). План в репо: [работа после 25.08](quality/KT3_IN_REPO_WORKPLAN_2026_08_27.md).

**Формула стадии (дословно; источник — [карточка речи](demo/KT2_JURY_FAQ_2026_08_12.md)):** Мы на стадии доработки. Одна команда показывает находку с доказательствами на учебном комплекте. Валидация эффективности и внедрение ещё не начались. `NO_GO` сохраняется, пока нет независимого размеченного корпуса, двух разметчиков, профиля приёмки (публичные IDS экспертизы — измерение; подпись Самолёта — внедрение) и подтверждения импорта в СОД.

**Объект КТ#3.** Речь и сценарий: [карточка КТ#3](demo/KT3_JURY_FAQ_2026_08_25.md) · [оператор](demo/KT3_OPERATOR_RUNBOOK_2026_08_25.md) · [трекер](demo/KT3_TRACKER_DMITRY_2026_08.md). Показ жюри = `python -m aerobim.tools.run_kt3_jury` (живой CLI из git). В репозитории нет файлов заказчика. Замечание: суть + пункт нормы (не выдуман) + этаж/ось из `IfcSpatialIndex`, если GUID попал в индекс; иначе явно «нет в индексе», не из OCR. Загрузка модели 1.5 ГБ ≠ разбор IFC (default 256 МиБ). Unsigned OOS: [`../samples/oos/`](../samples/oos/) — в `DATASET_MANIFEST.json`, не закрывает RT.

**Объект КТ#2.** Речь и пакет = текущий `main`. Цифры тестов = CI pin в [`docs/evidence/runtime-baseline-latest.json`](evidence/runtime-baseline-latest.json) (`attested_by=ci`: `commit_sha`, `tests_passed`, `tests_collected`). IUA freeze `f9389bf` (не HEAD). Прочие SHA на поверхностях — исторические. После правок документации pin может отставать на несколько коммитов до следующего прогона CI; локальные прогоны pytest не публикуем.

**Kane IUA.** На учебном комплекте можно показать содержание проверки, IDS с отказом при пропуске и открытый бенч **27/1026**. Нельзя: точность на комплекте заказчика, ТЗ >90%, SLA заказчика, MEP delivered, импорт в СОД, Checkpoint GO. Что цифры вправе значить: [Interpretation/Use](quality/INTERPRETATION_USE_LEDGER_2026_08.md). Заморозка `f9389bf`.

**Six desks.** Техлаб и МИК — основная аудитория этой карты. Intake-form 5/5 полей ≠ Checkpoint GO.

| Документ | Зачем |
|---|---|
| [Техобоснование](docs.md) | Суть решения |
| [ТЗ заказчика](tz/TZ_SAMOLET_TECHLAB_TASK_07_V2_2026.md) | Текст задачи 07 |
| [Матрица ТЗ](tz/TZ_COMPLIANCE_MATRIX_2026.md) | Построчное соответствие |
| [Карта покрытия подачи](../submission/TZ_REQUIREMENTS_COVERAGE_2026_08.md) | Эта подача |
| [Граница заявлений](pilot-claim-boundary-2026.md) | Проверено vs план |
| [План в репо после 25.08](quality/KT3_IN_REPO_WORKPLAN_2026_08_27.md) | Канал ≠ хеш-пакет; CI; не поднимать IFC cap |
| [Стриминг IFC / disk R-tree](quality/IFC_STREAMING_DISK_RTREE_DESIGN_2026_08.md) | Дизайн; parser не shipped; JSON sidecar индекса ≠ R-tree; 256 МиБ analyze |
| [Отказ RVT/NWD](tz/NATIVE_AUTODESK_INGEST_BOUNDARY_2026.md) | IFC-first; тот же класс, что DWG |
| [Сборка без внешних моделей](security/BUILD_WITHOUT_EXTERNAL_MODELS_2026.md) | IB: Kimi/LLM выключены под пилотом |
| [Карточка речи](demo/KT2_JURY_FAQ_2026_08_12.md) | Формула стадии |
| [Сравнение Задачи 07](demo/KT2_TASK07_COMPARISON_2026_08.md) | Пять решений; цифры конкурентов = их claims |
| [Строка корпуса](demo/KT2_CORPUS_SSOT_2026_08.md) | Замороженные открытые прокси |
| [Поля обмена 10D](demo/KT2_10D_INTAKE_CONTRACT_2026_08.md) | Предложение; не коннектор 10D |
| [Карточка речи КТ#3](demo/KT3_JURY_FAQ_2026_08_25.md) | 30 с + 8–12 мин; стоп-лист |
| [Сценарий оператора КТ#3](demo/KT3_OPERATOR_RUNBOOK_2026_08_25.md) | Живой CLI из git |
| [Трекер КТ#3 (6 задач)](demo/KT3_TRACKER_DMITRY_2026_08.md) | Live CLI; не KPI демо в git |
| [ADR-001](architecture/ADR-001-verdict-ownership-2026.md) | Кто пишет `summary.passed` |
| [Заявление о данных](evidence/DATA_STATEMENT_2026_08.md) | Что есть; открытые бенчи ≠ RT-001 |
| [Глоссарий жюри](partners/GLOSSARY_JURY_RU_2026_08.md) | Термины для нетехнического члена жюри |
| [Арифметика комиссии МИК](quality/MIK_COMMISSION_SCORING_2026_08.md) | К1=40; система B Б1=30; порог 50 — не прогноз нашего балла |
| [Обложка валидации фикстуры](quality/KT3_FIXTURE_VALIDATION_COVER_2026_08.md) | Pytest/CLI ≠ метрики партнёра; fixture SLA не representative |
| [Перечень поставки КТ#3](quality/KT3_DELIVERY_BOM_2026_08.md) | Что входит / не входит; MIT; п. 6.3 не закрыт |
| [Допущения эффекта A1–A8](partners/ECONOMIC_MODEL_LABELED_ASSUMPTIONS_2026_08.md) | Часы пустые; ≥20% — гипотеза |
| [Карта критерий → git](quality/MIK_CRITERION_EVIDENCE_MAP_2026_08.md) | Находимость К1–К5 и Б1–Б5; не прогноз балла |
| [Стек ГОСТ ИИ ТК 164](quality/NATIONAL_AI_GOST_STACK_KT3_2026.md) | 71476/42001/72514/72515; совместимость ≠ сертификация |
| [Шаблон матрицы К1](partners/K1_ROLE_MATRIX_TEMPLATE_2026_08.md) | Роли без ФИО; состав — заявка i.moscow |
| [Рычаги системы A за 50](quality/MIK_A_LEVERS_PAST_50_2026_08.md) | 16+36,6=52,6 identity; не прогноз балла |
| [УГТ ГОСТ Р 58048](quality/TRL_GOST_R_58048_SELF_ASSESS_2026.md) | Самооценка 4; не 5; не независимая ОГТ |
| [Лист К3](quality/K3_PARTNER_FIT_TICKSHEET_2026_08.md) | Посадка на карточку партнёра; не метрики Б2 |
| [Путь К4](quality/K4_COMMERCIAL_PATH_2026_08.md) | TAM BIM атрибутирован; не SAM; −72% не наш |
| [Новизна К2 vs витрина](quality/K2_NOVELTY_VS_PEERS_2026_08.md) | Методика vs «90% без протокола»; ablation фикстуры |
| [ПНСТ 841](quality/PNST_841_AI_QUALITY_EVAL_2026.md) | Карта на протокол 0,60; не SQuaRE-сертификат |
| [Брифы кресел](quality/MIK_SEAT_BRIEFS_2026_08.md) | Роли, не ФИО; среднее сидящих |
| [Вставка в заявку](partners/I_MOSCOW_APPLICATION_PASTE_2026_08.md) | Поля без ФИО в git |
| [Обложка 0,60](partners/PARTNER_PROTOCOL_SIGNREADY_COVER_2026_08.md) | Письмо «готово подписать»; не 90% |

Пять полей формы: [пакет подачи](../submission/README.md). Дека: [`aerobim_kt2.pptx`](../submission/03-presentation/aerobim_kt2.pptx) / [`aerobim_kt2.pdf`](../submission/03-presentation/aerobim_kt2.pdf). Ролик 2–3 мин **не записываем и не прилагаем.** Показ — `run_demo_ifc_acceptance_gate`.
