---
title: "AeroBIM — карта для жюри Техлаба и МИК"
status: active
version: "4.8.24"
last_updated: "2026-08-31"
tags: [aerobim, documentation, tier-0, techlab]
claim_boundary: "Jury pack only. Checkpoint NO_GO until RT-001/002/003. Eng readiness ≠ customer GO."
---

# Карта для жюри Техлаба и МИК

**`NO_GO`.** Стадия МИК — **доработка**. На учебном комплекте проверка запускается. Измерений (κ, held-out, два разметчика) на комплекте Самолёта **в git** нет. Канал 25.08 получен — **не** говорить «нет данных заказчика»; хеш-пакет в репозитории отсутствует. Блокеры: [реестр](../audit/reports/CRITICAL_BLOCKERS.md). Граница заявлений: [что проверено](pilot-claim-boundary-2026.md). Кто ставит технический статус: [ADR-001](architecture/ADR-001-verdict-ownership-2026.md). План в репо: [работа после 25.08](quality/KT3_IN_REPO_WORKPLAN_2026_08_27.md).

**Формула стадии (дословно; источник — [карточка речи](demo/KT2_JURY_FAQ_2026_08_12.md)):** Мы на стадии доработки. Одна команда показывает находку с доказательствами на учебном комплекте. Валидация эффективности и внедрение ещё не начались. `NO_GO` сохраняется, пока нет независимого размеченного корпуса, двух разметчиков, профиля приёмки (публичные IDS экспертизы — измерение; подпись Самолёта — внедрение) и подтверждения импорта в СОД.

**Объект КТ#3.** Речь и сценарий: [карточка КТ#3](demo/KT3_JURY_FAQ_2026_08_25.md) · [оператор](demo/KT3_OPERATOR_RUNBOOK_2026_08_25.md) · [трекер](demo/KT3_TRACKER_DMITRY_2026_08.md). Показ жюри = `python -m aerobim.tools.run_kt3_jury` (живой CLI из git). В репозитории нет файлов заказчика. Замечание: суть + пункт нормы (не выдуман) + этаж/ось из `IfcSpatialIndex`, если GUID попал в индекс; иначе явно «нет в индексе», не из OCR. Модель 1,5 ГБ — RocksDB, не SPF RAM; WASM 256 МиБ. Unsigned OOS: [`../samples/oos/`](../samples/oos/) — в `DATASET_MANIFEST.json`, не закрывает RT.

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
| [План в репо после 25.08](quality/KT3_IN_REPO_WORKPLAN_2026_08_27.md) | Канал ≠ хеш-пакет; CI; SPF cap 256 МиБ |
| [Стриминг IFC / disk R-tree](quality/IFC_STREAMING_DISK_RTREE_DESIGN_2026_08.md) | Дизайн; parser не shipped; JSON sidecar индекса ≠ R-tree; RocksDB over SPF |
| [SPF 256 МиБ / RocksDB 1,5 ГБ](quality/IFC_ANALYZE_VS_INGEST_CAP_2026_08.md) | SPF default не поднят; 413 свыше 1,5 ГБ; SPF ×10 литература |
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
| [Арифметика комиссии МИК](quality/MIK_COMMISSION_SCORING_2026_08.md) | Отбор — среднее; финал — сумма; Приложение 3 Положения не в git |
| [Обложка валидации фикстуры](quality/KT3_FIXTURE_VALIDATION_COVER_2026_08.md) | Pytest/CLI ≠ метрики партнёра; fixture SLA не representative |
| [Перечень поставки КТ#3](quality/KT3_DELIVERY_BOM_2026_08.md) | Что входит / не входит; MIT; п. 6.3 не закрыт |
| [Допущения эффекта A1–A8](partners/ECONOMIC_MODEL_LABELED_ASSUMPTIONS_2026_08.md) | Часы пустые; ≥20% — гипотеза |
| [Карта критерий → git](quality/MIK_CRITERION_EVIDENCE_MAP_2026_08.md) | Находимость К1–К5 и Б1–Б5; не прогноз балла |
| [Стек ГОСТ ИИ ТК 164](quality/NATIONAL_AI_GOST_STACK_KT3_2026.md) | 71476/42001/72514/72515; совместимость ≠ сертификация |
| [Шаблон матрицы К1](partners/K1_ROLE_MATRIX_TEMPLATE_2026_08.md) | Роли без ФИО; состав — заявка i.moscow |
| [Рычаги системы A за 50](quality/MIK_A_LEVERS_PAST_50_2026_08.md) | 16+36,6=52,6 identity; не прогноз балла |
| [УГТ ГОСТ Р 58048](quality/TRL_GOST_R_58048_SELF_ASSESS_2026.md) | Самооценка 4; не 5; не независимая ОГТ |
| [Лист К3](quality/K3_PARTNER_FIT_TICKSHEET_2026_08.md) | Посадка на карточку партнёра; не метрики Б2 |
| [Лист системы B Б1–Б5](quality/B_FINAL_SCORING_TICKSHEET_2026_09.md) | Полосы, не прогноз; Приложение 3 Положения не в git |
| [Лабораторный до/после](partners/BEFORE_AFTER_MEASUREMENT_PROTOCOL_2026_09.md) | Не часы партнёра; A1–A8 пустые |
| [План recall на инъекциях](evidence/DEFECT_INJECTION_RECALL_PLAN_2026_09.md) | Синтетика; seed 20260824; не корпус Самолёта |
| [ADR-004 MIT vs п. 6.3](architecture/ADR-004-prize-ip-mit-fork-2026.md) | Развилка; LICENSE не меняем |
| [Сверка весов с PDF](quality/ORDER_WEIGHTS_VERIFICATION_2026_09.md) | Колонка PDF пустая; UNVERIFIED; attributed |
| [Действия владельца](OWNER_ACTIONS_2026_09.md) | Git не закрывает письмо, ФИО, PDF, разметчиков |
| [Лицензионная вилка CAD (OSINT 30.08)](quality/NATIVE_CAD_LICENSE_FORK_OSINT_2026_08.md) | Sustaining ≠ BimRv; не DWG-ready |
| [Критический путь окна КТ#3](quality/KT3_WINDOW_CRITICAL_PATH_2026_09.md) | OIDC 501; Wilson n=6; RT-002 split; TBD confirm |
| [Восемь задач трекера 29.08](quality/TRACKER_EIGHT_TASKS_SIGINEVICH_2026_08.md) | SIG-01…08; volume≠accuracy; BFF 501 |
| [Триаж канала SIG-01](quality/SIG01_CHANNEL_TRIAGE_2026_08.md) | ALL≠accuracy; EI45≠REI60; overlap unsigned; NO_GO |
| [Максимум на копии Самолёта 31.08](quality/CHANNEL_SAMOLET_MAX_PASS_2026_08.md) | SIG-01…08 на NDA-копии; Uncertain; volume≠accuracy |
| [Триаж семейств пакета 31.08](quality/CHANNEL_PACK_TRIAGE_2026_08.md) | LIRA majority≠solver; token≠MATCH; ГиБ не в git |
| [Pack family facts 31.08](evidence/pack-family-facts-2026-08.md) | 6408; named calc ext 235; 6 docx / 46 xlsx shortlist |
| [Unpack census 30.08](evidence/unpack-census-2026-08.md) | SIG-02 carriers; evening 2552 / 6408 (утро 2618/6467 — оболочки); not processed |
| [Deep-study carrier facts 30.08](evidence/deep-study-carrier-facts-2026-08.md) | SIG-02 depth; IFC2X3; QTO 0; FireRating walls EI 45; not processed |
| [Пакет вопросов Самолёту](partners/SAMOLET_QUESTION_PACK_KT3_2026_08.md) | SIG-05 черновик; RT-002b; TBD confirm v2 |
| [Одностраничник RVT/NWD/CV](demo/KT3_RVT_NWD_CV_ONEPAGER_2026_08.md) | SIG-07; CADSoftTools от 765 USD; Sustaining ≠ BimRv |
| [Четыре проверки vs записка](quality/CALCULATION_COMPARE_FOUR_CHECKS_2026_09.md) | Сопоставление, не решатель |
| [Путь К4](quality/K4_COMMERCIAL_PATH_2026_08.md) | Нулевой вход; МСФО ≠ РСБУ; TAM ≠ SAM; −72% не наш |
| [Новизна К2 vs витрина](quality/K2_NOVELTY_VS_PEERS_2026_08.md) | Четыре пункта методики; карточка ≠ публичный след |
| [ПНСТ 841](quality/PNST_841_AI_QUALITY_EVAL_2026.md) | Карта на протокол 0,60; не SQuaRE-сертификат |
| [Брифы кресел](quality/MIK_SEAT_BRIEFS_2026_08.md) | Роли, не ФИО; отбор — среднее; финал — сумма |
| [Пороги заказчика](quality/CUSTOMER_THRESHOLD_VS_ACTUAL_2026_08.md) | Целевое vs фактическое; 256 МиБ; cap не поднимаем |
| [Вставка в заявку](partners/I_MOSCOW_APPLICATION_PASTE_2026_08.md) | Поля без ФИО в git |
| [Обложка 0,60](partners/PARTNER_PROTOCOL_SIGNREADY_COVER_2026_08.md) | Письмо «готово подписать»; не 90% |

Пять полей формы: [пакет подачи](../submission/README.md). Дека: [`aerobim_kt2.pptx`](../submission/03-presentation/aerobim_kt2.pptx) / [`aerobim_kt2.pdf`](../submission/03-presentation/aerobim_kt2.pdf). Ролик 2–3 мин **не записываем и не прилагаем.** Показ — `run_demo_ifc_acceptance_gate`.
