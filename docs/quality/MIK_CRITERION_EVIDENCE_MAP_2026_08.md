<!-- claims-lint: allow-file reason="Criterion-to-artifact map for K/B; not a predicted score; NO_GO" -->
---
title: "MIK criterion → git evidence map"
date: "2026-08-29"
last_updated: "2026-08-30"
status: active
version: "1.4.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Findability pack for selection K/B briefing. Regulation Appendix 3 is not
  in git. Not a predicted total. Not certification. Checkpoint NO_GO.
---

# Карта доказательств: критерий → git

Комиссия ставит балл за то, что **находит**. Этот файл — указатель, не прогноз.
`predicted_aerobim_total() is None`. Checkpoint **`NO_GO`**.

Публичная сверка приложения 4 (ЛЭТИ, 30.04.2026): задача Самолёта — **№6**,
приз — платное пилотное тестирование 2 млн ₽.
Источник: [etu.ru](https://new.etu.ru/ru/home/nauka/konkursy-i-granty-na-provedenie-niokr/konkursy-i-granty-na-provedenie-nauchno-issledovatelskih-rabot/programma-dorabotki-i-vnedreniya-naukoemkih-ii-reshenij).
Историческое «07» в именах файлов **не** этот номер. На витрине i.moscow
заголовок несёт 07; в приложении 4 это строка 6. Не спорить с сайтом.

## Система A

| Код | Что комиссия должна увидеть | Где в git | Что git не закрывает |
|---|---|---|---|
| К1 | Научная + инженерная компетенция (текст ЛЭТИ: оба класса) | [`K1_ROLE_MATRIX_TEMPLATE_2026_08.md`](../partners/K1_ROLE_MATRIX_TEMPLATE_2026_08.md) | ФИО, степени, патенты, совместные R&D — **только заявка** |
| К2 | Прототип не ниже TRL 3; ИС; нацстандарты ИИ | CLI + CI pin; MIT + ADR-002; [`NATIONAL_AI_GOST_STACK_KT3_2026.md`](NATIONAL_AI_GOST_STACK_KT3_2026.md); [`PNST_841_AI_QUALITY_EVAL_2026.md`](PNST_841_AI_QUALITY_EVAL_2026.md); [`K2_NOVELTY_VS_PEERS_2026_08.md`](K2_NOVELTY_VS_PEERS_2026_08.md) | Сертификат 42001; патентный забор (п. 6.3); сертификация ПНСТ 841 |
| К3 | Адаптация под партнёра; измеримость | Карта покрытия; веб без интеграции; протокол 0,60 | Подпись профиля; замер на их комплекте |
| К4 | Тираж; нулевой вход; не CAPEX | [`K4_COMMERCIAL_PATH_2026_08.md`](K4_COMMERCIAL_PATH_2026_08.md); ADR-002; A1–A8 пустые часы | Выручка; второй контракт; 10,1 млрд как SAM; −72% как наш эффект; «инвестируйте»; МСФО как наш эффект |
| К5 | План и риск | Workplan; путь без хеш-пакета; [i.moscow/pilot](https://i.moscow/pilot) ≠ приз 2 млн | Соглашение площадки |

## Система B (брифинг; Приложение 3 к Положению не в git)

| Код | Что комиссия должна увидеть | Где в git | Что git не закрывает |
|---|---|---|---|
| Б1 | Функционал + ограничения | [`B_FINAL_SCORING_TICKSHEET_2026_09.md`](B_FINAL_SCORING_TICKSHEET_2026_09.md); TIER0; native RVT/NWD fail-closed; cap 256 МиБ | KPI партнёра письмом |
| Б2 | Протоколы **и** метрики валидации | ticksheet Б2; обложка фикстуры + WP-07; [`DEFECT_INJECTION_RECALL_PLAN_2026_09.md`](../evidence/DEFECT_INJECTION_RECALL_PLAN_2026_09.md) | Dual-rater на партнёре; синтетика ≠ корпус Самолёта |
| Б3 | Импорт/экспорт MVP | ticksheet Б3; Upload + BCF export; OIDC NOT_IMPLEMENTED | SSO; 1,5 ГБ analyze |
| Б4 | До/после | ticksheet Б4; A1–A8; [`BEFORE_AFTER_MEASUREMENT_PROTOCOL_2026_09.md`](../partners/BEFORE_AFTER_MEASUREMENT_PROTOCOL_2026_09.md) | Часы партнёра |
| Б5 | Поставка + прозрачность | ticksheet Б5; [`KT3_DELIVERY_BOM_2026_08.md`](KT3_DELIVERY_BOM_2026_08.md); [`ADR-004-prize-ip-mit-fork-2026.md`](../architecture/ADR-004-prize-ip-mit-fork-2026.md) | Передача исключительных прав |

## Что поднимает вилку, а что нет

| Действие | Вилка | Git? |
|---|---|---|
| Заполнить шаблон К1 в **заявке** именами и подтверждениями | К1 21–40 → 41–60 | Нет, капитан |
| Капитан закрывает **два класса** (не 10 голов) | К1 к верху низкой полосы (до 16) | Заявка |
| УГТ 4 (лаборатория), не УГТ 5 | К2 | [`TRL_GOST_R_58048_SELF_ASSESS_2026.md`](TRL_GOST_R_58048_SELF_ASSESS_2026.md) |
| К3 как посадка на карточку, не как Б2 | К3 | [`K3_PARTNER_FIT_TICKSHEET_2026_08.md`](K3_PARTNER_FIT_TICKSHEET_2026_08.md) |
| TAM BIM атрибутировать, не клеить в SAM | К4 | [`K4_COMMERCIAL_PATH_2026_08.md`](K4_COMMERCIAL_PATH_2026_08.md) |
| Методика vs витрина «90% без протокола» | К2 | [`K2_NOVELTY_VS_PEERS_2026_08.md`](K2_NOVELTY_VS_PEERS_2026_08.md) |
| Бриф на кресло (роли, не ФИО) | среднее | [`MIK_SEAT_BRIEFS_2026_08.md`](MIK_SEAT_BRIEFS_2026_08.md) |
| Этот указатель + BOM + ГОСТ-стек | К2, Б5 найти | Да |
| Подписать протокол 0,60 | К3, Б1, Б2 | Партнёр |
| Fixture SLA как 30 мин | — | Запрещено |

Идентичность: верх К1-low (16) + низ rest-high (36,6) = **52,6 ≥ 50**.
Десять фамилий не требуются. [`MIK_A_LEVERS_PAST_50_2026_08.md`](MIK_A_LEVERS_PAST_50_2026_08.md).

Городской контур [i.moscow/pilot](https://i.moscow/pilot) — **другой** инструмент
(площадки, экспертиза инновационности). Не подменять им приз задачи №6 и не
считать 449-ПП входом в Техлаб.
