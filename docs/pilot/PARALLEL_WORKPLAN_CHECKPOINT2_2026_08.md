<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
---
title: "AeroBIM parallel workplan → Checkpoint #2 (Aug 2026) → final (Sep 2026)"
status: active
version: "1.0.0"
last_updated: "2026-07-24"
claim_boundary: "Methodology and engineering contour only. Customer precision / SLA / CDE-ready BCF remain NO_GO until RT-001/002/003."
---

# Параллельный план до контрольной точки №2

**Цель (4–20 августа):** промежуточная версия на согласованном сценарии Самолёта — границы применимости, воспроизводимый прогон, измеримые критерии.  
**Цель (3–21 сентября):** пилотный отчёт на данных заказчика и подтверждённый экономический эффект.

**Checkpoint продукта:** `NO_GO` до закрытия RT-001 / RT-002 / RT-003 с evidence.

## Пять параллельных потоков

| # | Поток | Результат | Критерий готовности | Артефакты в репо |
|---|--------|-----------|---------------------|------------------|
| 1 | Протокол пилота + методика разметки | Утверждённый протокол + инструкция двум экспертам | У каждого типа проверки: вход, ожидаемый результат, источник доказательства, эксперт, способ измерения | [`../pilot-protocol-samolet-2026.md`](../pilot-protocol-samolet-2026.md), [`EXPERT_LABELING_INSTRUCTION_2026.md`](EXPERT_LABELING_INSTRUCTION_2026.md), [`../partners/SAMOLET_WHAT_WE_NEED_2026_07-ru.md`](../partners/SAMOLET_WHAT_WE_NEED_2026_07-ru.md) |
| 2 | Живой демо-прогон + evidence-бандл | Воспроизводимый демо-сценарий | Повторный запуск сопоставим; у замечания есть ссылка на файл/лист/элемент | `python -m aerobim.tools.run_demo_ifc_acceptance_gate`, `aerobim.tools.export_evidence_bundle` |
| 3 | Norm pack + RASE | Шаблон + первый набор правил (fail-closed) | У правила: источник, область, исключения, исполняемый критерий, тест; неподтверждённый pack ≠ positive verdict | [`NORM_PACK_RASE_GUIDE_2026.md`](NORM_PACK_RASE_GUIDE_2026.md), `samples/rule-packs/norm-rule-pack.schema.json`, `customer-norm-pack-intake-template.json` |
| 4 | Harness размеченного среза | Отчёт TP/FP/FN + κ + время без ручных таблиц | Один запуск → метрики, конфиг, размер корпуса, согласие экспертов, ошибки по категориям | `evaluate_detection_precision`, `measure_adjudicator_agreement` |
| 5 | Матрица трассируемости ТЗ | Требование → модуль → evidence → статус → next | Нет требования без статуса, владельца и критерия | [`../tz/TZ_COMPLIANCE_MATRIX_2026.md`](../tz/TZ_COMPLIANCE_MATRIX_2026.md), [`../tz/README.md`](../tz/README.md), Claims Lock |

## Календарь

| Окно | Фокус | Зависимость от Самолёта |
|------|--------|-------------------------|
| **28–31 июля** | Протокол, схема разметки, структура norm pack, перечень входных данных | Список запросов готов; данные ещё не обязательны |
| **1–3 августа** | Демо-прогон, evidence-бандл, harness; вопросы к Самолёту | Стабильный демо-комплект (fixture OK) |
| **4–10 августа** | Intake комплекта, норм, двух экспертов; baseline | **Блокирует** customer KPI |
| **11–20 августа** | Промежуточный прогон, правка правил, передача версии | Обратная связь экспертов |
| **21 авг – 2 сен** | Оценка на размеченном срезе; BCF в контуре заказчика | Корпус + adjudication + CDE |
| **3–21 сентября** | Пилотный отчёт, метрики, ограничения, внедрение | Подписанный scope + evidence |

## Критические зависимости (не заявлять без них)

| Нужно | Без этого нельзя |
|-------|------------------|
| Согласованный комплект ПД/РД/IFC/ТЗ/расчёты | Customer SLA / precision |
| Утверждённый norm pack (`customer_approved` + `pack_hash`) | Positive verdict по нормам (RT-002) |
| ≥2 эксперта-разметчика + dual-blind + adjudication | κ/α, TP/(TP+FP), экономический эффект (RT-001) |
| Federated MEP + signed matrix (если MEP в scope) | MEP system-aware claim (RT-003) |

**Отдельные проверяемые направления (не заявленные результаты промежуточной версии):** нативный DWG; полноценный MEP system-aware clash; независимая проверка корректности расчётов; импорт BCF в конкретную СОД.

**Инженерный gap-анализ четырёх направлений:** [`FOUR_DIRECTION_GAP_ANALYSIS_2026_07_24.md`](FOUR_DIRECTION_GAP_ANALYSIS_2026_07_24.md).

**Kickoff-карта (входы заказчика ↔ intake gates ↔ этапность):** [`../partners/SAMOLET_KT2_ASK_2026_08_15.md`](../partners/SAMOLET_KT2_ASK_2026_08_15.md).

**Протокол сравнения VLM/OCR (Qwen · Kimi · Gemma, окно 4–20 авг):** [`VLM_OCR_COMPARISON_PROTOCOL_2026_08.md`](VLM_OCR_COMPARISON_PROTOCOL_2026_08.md) — вспомогательный инструмент, не критерий приёмки.

## Claims Lock (промежуточная версия)

Запрещено до evidence: «>90%», «SLA ≤30 мин на комплекте заказчика», «DWG готов», «MEP delivered», «AI читает чертежи как инженер», «BCF готов к CDE», positive verdict по неподтверждённому norm pack.

Допустимо: «инженерная готовность контура», «fixture GO», «методика готова», «ожидаем корпус / pack / экспертов».

## Владельцы потоков (внутренняя)

| Поток | Owner | Соисполнитель |
|-------|-------|---------------|
| 1 Протокол / разметка | Tech lead | openBIM lead |
| 2 Демо / evidence | Tech lead | — |
| 3 Norm / RASE | openBIM lead | Samolet (утверждение) |
| 4 Harness | Tech lead | Adjudicators (labels) |
| 5 TZ matrix | Tech lead | Claims Lock guardian |

## Definition of Done — Checkpoint #2 (промежуточная)

- [x] Протокол + инструкция экспертов — **черновик на согласование с 2026-07-26** ([протокол](../pilot-protocol-samolet-2026.md), [инструкция](EXPERT_LABELING_INSTRUCTION_2026.md)); sign-off Самолёта ожидается в окне 4–10 авг
- [x] Демо-бандл воспроизводим на fixture-комплекте — dry-run 2026-07-26: два независимых прогона дали идентичный `reproducibility_hash` (`artifacts/evidence-bundle/checkpoint2-dryrun/`)
- [x] Norm pack template + RASE-гайд + fail-closed — задокументированы: [`NORM_PACK_RASE_GUIDE_2026.md`](NORM_PACK_RASE_GUIDE_2026.md), `norm-rule-pack.schema.json`, fail-closed тесты (`test_norm_pack_env_capability`, `test_norm_rule_pack_loader`); customer pack = RT-002 OPEN
- [x] Harness одним запуском даёт precision/recall/F1/FP-rate + κ/α + nDCG — `aerobim.tools.run_pilot_harness` (2026-07-26); пороги корпуса обоснованы `plan_adjudication_corpus`
- [x] TZ matrix без «пустых» TBD — верифицировано 2026-07-26: ТЗ v2 §19 (ТР-1..62 со статусами/критериями) + [трёхисточниковая матрица](../tz/TRI_SOURCE_REQUIREMENTS_MATRIX_2026.md)
- [x] Список входных данных / вопросов Самолёту актуален — [ASK КТ#2](../partners/SAMOLET_KT2_ASK_2026_08_15.md)
- [x] Claims Lock не нарушен — enforced fail-closed (`enforce_honesty_capabilities`, forbidden phrases, publishable-гейты) + док-ревью 2026-07-26; обязательство непрерывное до КТ3
