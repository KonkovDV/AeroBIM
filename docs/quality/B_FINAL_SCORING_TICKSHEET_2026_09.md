<!-- claims-lint: allow-file reason="System B ticksheet; band arithmetic not a forecast; App 3 unseen; NO_GO" -->
---
title: "System B final scoring ticksheet — bands, not a prize forecast"
date: "2026-08-30"
last_updated: "2026-08-30"
status: active
version: "1.0.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Findability pack for attributed System B weights (order briefing, not
  Regulation Appendix 3). Band arithmetic is not a predicted AeroBIM total.
  Not partner validation metrics. Checkpoint NO_GO.
---

# Система B: лист Б1–Б5 (не прогноз)

`predicted_aerobim_total() is None`. Это не прогноз нашего балла. Финал в
приказе — **итоговая сумма**; таблица Приложения 3 к Положению **в git нет**.
Веса ниже — attributed briefing приказа, не `attested_by=ci`.
`finalist_weights_are_regulation_appendix_3() == False`.
`confirmed_partner_validation_metrics() == False`.

Задача Самолёта — **№6** (приложение 4). Комиссия — **№7**. Историческое «07»
в именах файлов **не** номер Положения.

Тай-брейк системы B — только **Б1**.

| Код | Макс | Что на руках | Чего нет | Говорить вслух | Артефакт git | Git не закрывает |
|---|---:|---|---|---|---|---|
| Б1 | 30 | Посадка на карточку: ассистент ПД/РД, HITL, fail-closed native CAD, cap 256 МиБ | Подписанные KPI партнёра | Соответствуем запросу openBIM; native RVT/NWD/DWG закрыты явно | [`K3_PARTNER_FIT_TICKSHEET_2026_08.md`](K3_PARTNER_FIT_TICKSHEET_2026_08.md) · TIER0 | Письмо с KPI; «коллизии >90% сданы» |
| Б2 | 20 | Обложка фикстуры; протокол 0,60; CI pin; план инъекций | Dual-rater и метрики на комплекте партнёра | Pytest — регрессия движка, не валидация партнёра | [`KT3_FIXTURE_VALIDATION_COVER_2026_08.md`](KT3_FIXTURE_VALIDATION_COVER_2026_08.md) · [`DEFECT_INJECTION_RECALL_PLAN_2026_09.md`](../evidence/DEFECT_INJECTION_RECALL_PLAN_2026_09.md) | `confirmed_partner_validation_metrics` |
| Б3 | 20 | Загрузка + BCF ZIP; п. 2.2.2 файловый обмен; RocksDB analyze до 1,5 ГБ | SSO; импорт в СОД | MVP без интеграции в контур | TIER0 · BCF ladder · [`IFC_ANALYZE_VS_INGEST_CAP_2026_08.md`](IFC_ANALYZE_VS_INGEST_CAP_2026_08.md) | CDE-ready; OIDC 501; SPF/WASM остаются 256 МиБ |
| Б4 | 20 | Пустые A1–A8; методика лабораторного замера | Часы партнёра; подписанный до/после | Лабораторный замер ≠ часы Самолёта; −72,1% не наш | [`BEFORE_AFTER_MEASUREMENT_PROTOCOL_2026_09.md`](../partners/BEFORE_AFTER_MEASUREMENT_PROTOCOL_2026_09.md) · [`ECONOMIC_MODEL_LABELED_ASSUMPTIONS_2026_08.md`](../partners/ECONOMIC_MODEL_LABELED_ASSUMPTIONS_2026_08.md) | Эффект для партнёра |
| Б5 | 10 | BOM; LICENSE MIT; карта прозрачности | Соглашение о правах по п. 6.3 | MIT сейчас; развилка прав — вопрос организаторам, не обещание | [`KT3_DELIVERY_BOM_2026_08.md`](KT3_DELIVERY_BOM_2026_08.md) · [`ADR-004-prize-ip-mit-fork-2026.md`](../architecture/ADR-004-prize-ip-mit-fork-2026.md) | Передача исключительных прав |

Шкала процентов — та же, что у отбора (0–20 очень низкий … 81–100 очень высокий).
Баллы критерия = процент × максимум. Итог финала — **сумма**, не среднее.
Порог приза «не менее 50»: знаменатель невиденной таблицы **неизвестен**.
`prize_floor_denominator_known() == False`.

## Полосы сейчас (арифметика полос, не прогноз)

Каждая строка — **полоса, в которую git имеет право садиться**, не балл,
который комиссия поставит. Сумму полос **не** читать как итог AeroBIM.

| Код | Полоса, которую git лицензирует сегодня | Почему не выше |
|---|---|---|
| Б1 | средняя (41–60 % от 30) | Нет подписанных KPI; честность ограничений зачитывается как посадка, не как high |
| Б2 | очень низкая–низкая (0–40 % от 20) | Нет confirmed partner metrics; pytest не поднимает high |
| Б3 | средняя (41–60 % от 20) | Файловый обмен и RocksDB до 1,5 ГБ есть; SSO и T2 СОД нет |
| Б4 | очень низкая (0–20 % от 20) | A1–A8 пустые; нет часов партнёра |
| Б5 | средняя (41–60 % от 10) | BOM и MIT на руках; п. 6.3 не закрыт |

`NO_GO` **не** лицензирует «Б2 высокий».

## Полосы после трёх действий (тоже не прогноз)

Три действия **владельца / лаборатории**, не коммит git:

1. Партнёр подписывает обложку протокола 0,60.
2. Лабораторный замер трудозатрат на **нашем** комплекте (не часы партнёра).
3. Recall на инъекциях с опубликованным seed + precision двумя разметчиками
   на синтетике (~100 находок).

| Код | Куда полоса *может* сдвинуться | Чего по-прежнему нет |
|---|---|---|
| Б1 | к высокой, если KPI письмом | Подпись не ставит git |
| Б2 | протоколы + синтетика = полка, не high партнёра | Метрики на комплекте Самолёта |
| Б3 | без сдвига от этих трёх | SSO / T2 СОД |
| Б4 | лабораторный low возможен; партнёрский остаётся пустым | A1–A8 партнёра |
| Б5 | без сдвига, пока нет ответа по п. 6.3 | Исключительные права |

Даже после трёх действий `predicted_aerobim_total() is None`. Не говорить
«порог 50 у нас в кармане». Не говорить «готово к внедрению» и не подменять
УГТ 4 словом «внедрено».

Связанные: [`MIK_COMMISSION_SCORING_2026_08.md`](MIK_COMMISSION_SCORING_2026_08.md) ·
[`K3_PARTNER_FIT_TICKSHEET_2026_08.md`](K3_PARTNER_FIT_TICKSHEET_2026_08.md).
