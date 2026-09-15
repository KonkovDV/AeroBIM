<!-- claims-lint: allow-file reason="Demo-day speech lock; TRL 5 / CDE / SSO / 90% as non-claims; Checkpoint GO; customer_go false" -->
---
title: "Демо-день 29–30.09.2026 — замок речи"
date: "2026-09-14"
last_updated: "2026-09-14"
status: active
version: "1.1.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: coverage_map_only
claim_boundary: >
  Licensed speech for TechLab demo day. Carrier audit is not pack processed.
  Open-bench clash is not customer MEP. AECV macro_extended is not F1.
  GOST R 58048 self-assess is TRL 4, not 5. Checkpoint GO; customer_go false.
---

# Демо-день — что можно сказать вслух

Машина: `python -c "from aerobim.domain.demo_day_speech_lock import demo_day_speech_lock_snapshot"`.

Карточка КТ#3 остаётся в силе: [`KT3_JURY_FAQ_2026_08_25.md`](KT3_JURY_FAQ_2026_08_25.md). Красная черта дека 13.09: [`../quality/DEMO_DAY_DECK_REDLINE_2026_09.md`](../quality/DEMO_DAY_DECK_REDLINE_2026_09.md). Аудиторская таблица A–F: [`../quality/DEMO_DAY_AUDITOR_PACK_2026_09.md`](../quality/DEMO_DAY_AUDITOR_PACK_2026_09.md) (не exhibit жюри). Текст слайдов: [`../../submission/03-presentation/demo_day_slides.md`](../../submission/03-presentation/demo_day_slides.md).

Checkpoint **`GO`**; `customer_go` **false**. Задача приложения 4 — **№6**. Комиссия — **№7**. Не спорить с витриной.

## Формула на обложку (дословно)

Приёмочный шлюз комплекта проектной и рабочей документации. Сверяем модель, лист, ведомость и ТЗ. В замечании — норма, ось, этаж, GUID. Самооценка по ГОСТ Р 58048 — **TRL 4** (лаборатория) — в приложении, не на титуле. Уровень 5 не заявляем.

## Лицензированные числа

| Что | Значение | Чем не является |
|---|---|---|
| IfcSpace на канале | **16 152**; NetFloorArea заполнен в **0** | Дефект оформления листов; замер ТЭП |
| IfcGrid | **0 / 13 / 53** по трём пакетам | «Осей нет во всём комплекте» |
| Арматура / сети в IFC | **0 / 0** | Проверка MEP или армирования сдана |
| 837 IfcClash | открытый duplex IFC-Bench | Связка АР ↔ ИОС заказчика |
| AECV 0,4325 | `macro_extended`, n полей **585** | Macro F1; точность продукта |
| Extraction macro F1 0,86 | корпус **fixture** | Точность на комплекте заказчика |
| n пилота | **111** (ширина интервала); 62 — только мощность | Подписанный n = 62 |
| Эксперимент Б КР | **16,7 %** (4/24) | 17 %; recall продукта |
| IDS | 24 файла МОГЭ = **389** spec; всего **50** файлов = **847** spec | «389 спецификаций в 50 файлах» |
| Самопроверка ЦИМ АГР | с **29.06.2026** | 23.06.2026 |
| Веса финала Б1–Б5 | 30/20/20/20/10; десктопный скан Положения 14.09 | PDF в git; `attested_by=ci` |
| BCF | ZIP 2.1/3.0 структурно | Импорт в СОД (`NOT_VERIFIED`) |
| SSO | `GET /v1/auth/bff` по умолчанию **501** | SSO на IdP заказчика готов |
| Площадь по геометрии | **not_implemented** | «Считаем по контуру IfcSpace» |

CI-пин (`attested_by=ci`): пять ворот PASS. Число файлов mypy в пине **нет**. Счётчики тестов не копировать в этот файл как SSOT — канон [`../evidence/runtime-baseline-latest.json`](../evidence/runtime-baseline-latest.json).

## Пять кресел (роли, не имена)

| ID | Оптика | Лицензированный ответ | Убивает |
|---|---|---|---|
| mik_piloting_center_chair | Формы Фонда | Программа → соглашение → методика → акт. Формы — у оператора Фонда | Спрашивать форму акта у партнёра |
| mik_demand_center_expert | Класс покупателя | Нулевой вход; профиль — IDS, не форк ядра | Монопродукт; «уже в реестре ПО» |
| partner_tech_customer_director | Дни цикла | E1–E5; два множителя из трёх — их | Их % переноса срока как наш эффект |
| partner_project_office_lead | HITL, BCF-файл | ADR-001; T1 ZIP; T2 не доказан; BFF 501 | «Роли сданы»; замечания уже в их реестре |
| partner_information_modelling_lead | Выгрузка | Пустой QTO, оси 0/13/53, арматуры нет, сети в IFC нет | 837 как их АР↔ИОС; «прогнали MEP» |

Брифы: [`../quality/MIK_SEAT_BRIEFS_2026_08.md`](../quality/MIK_SEAT_BRIEFS_2026_08.md).

## Красная черта (идентификаторы атак)

Каждый идентификатор разобран в redline. На сцене — тормоз, не спор.

RT-DEMO-TRL5 · RT-DEMO-837-CUSTOMER · RT-DEMO-GRID-ALL-PACKS · RT-DEMO-AREA-GEOMETRY · RT-DEMO-F1-043 · RT-DEMO-N62-AS-N · RT-DEMO-KR-17 · RT-DEMO-389-IN-50 · RT-DEMO-SSO-READY · RT-DEMO-BCF-CDE · RT-DEMO-REGISTRY-NOW · RT-DEMO-PACK-PROCESSED · RT-DEMO-IFC4-EXAMPLE · RT-DEMO-NWD-NATIVE · RT-DEMO-REVISION-DUPES · RT-DEMO-MYPY-FILECOUNT · RT-DEMO-AGR-DATE · RT-DEMO-WEIGHTS-PDF · RT-DEMO-ESCROW-NAMED · RT-DEMO-UGT-ON-COVER.

## Три числа, без которых критерий эффекта пуст

1. Рабочие дни одного круга согласования РД по типовой секции — знает техзаказчик / PMO.
2. Часы ручной проверки того же комплекта «до» — знает нормоконтроль / ГИП комплекта.
3. Сколько лишних кругов они считают нормой на секции — знает дирекция технологического заказчика.

Допущения E1–E5: [`../partners/CUSTOMER_CYCLE_ECONOMICS_ASSUMPTIONS_2026_09.md`](../partners/CUSTOMER_CYCLE_ECONOMICS_ASSUMPTIONS_2026_09.md).

## Демо 20 секунд

Команда: `python -m aerobim.tools.run_kt3_jury` из `backend/`. Открыть `report.html`. Показать IDS-строку **с GUID** (FireRating), не `REQ-AREA-*`. Сказать: учебный комплект из git; `summary.passed=false` здесь ожидаем. BCF ZIP — структурный файл, не импорт в СОД. Сценарий: [`KT3_OPERATOR_RUNBOOK_2026_08_25.md`](KT3_OPERATOR_RUNBOOK_2026_08_25.md).

## Запрещено

- УГТ-5, TRL 5 как заявленный уровень, production-ready, CDE-ready, MEP delivered
- точность >90%, SLA заказчика, native DWG/RVT/NWD
- пакет заказчика проверен, 43 ГБ обработаны
- BCF в ваш реестр как факт, SSO на вашем IdP как факт
- в реестре российского ПО как статус
- площади считаем по геометрии
- прогон выполнен на вашем комплекте как список дефектов заказчика
