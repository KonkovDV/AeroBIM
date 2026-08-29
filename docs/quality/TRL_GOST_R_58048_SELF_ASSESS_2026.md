<!-- claims-lint: allow-file reason="GOST R 58048 TRL self-assessment; not TRL 5; not independent OGT; NO_GO" -->
---
title: "TRL / УГТ self-assessment — GOST R 58048, not TRL 5"
date: "2026-08-29"
last_updated: "2026-08-29"
status: active
version: "1.0.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Self-assessment against GOST R 58048-2017 language. Not an independent
  technology-readiness examination. Not TRL 5 or 6. Checkpoint NO_GO.
---

# УГТ (ГОСТ Р 58048-2017) — самооценка, не экспертиза

**Совместимость не сертификация.** Независимая команда ОГТ по п. 5.1.2
стандарта **не** проводилась. Приказ 29.12.2017 № **2128-ст**
([ГАРАНТ, приложение Г](https://base.garant.ru/72237776/172a6d689833ce3e42dc0a8a7b3cddf9/)).

Программный пол К2 Техлаба — **не ниже TRL / УГТ 3**. Мы не заявляем УГТ 5
(окружение, близкое к эксплуатации = комплект партнёра) и не УГТ 6
(городской контур [i.moscow/pilot](https://i.moscow/pilot)).

| Уровень | Что это значит здесь | Статус AeroBIM |
|---|---|---|
| УГТ 3 | Критические функции показаны аналитически и экспериментально | Ниже нас: движок + IDS + HITL на фикстуре |
| **УГТ 4** | Компоненты испытаны в **лабораторном** окружении | **Самооценка:** CI pin `attested_by=ci`; CLI; открытые пакеты; фикстура |
| УГТ 5 | Испытания в окружении, близком к реальному | **Нет:** нет dual-rater на комплекте партнёра; RT-001 OPEN |
| УГТ 6+ | Пилот / штатная эксплуатация | **Нет.** Checkpoint `NO_GO` |

Лаборатория ≠ заказчик. Pytest и `run_kt3_jury` — доводы **УГТ 4**, не УГТ 5.

Постановление 2204 (пилот внедрения, УГТ ≥5) и грант площадок — **другие**
инструменты. Не подставлять их как оценку К2 этой комиссии.
