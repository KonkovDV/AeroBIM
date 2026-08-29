<!-- claims-lint: allow-file reason="K4 commercial path; TAM not SAM; 72% not ours; NO_GO" -->
---
title: "K4 commercial path — TAM is not SAM, 72% is not ours"
date: "2026-08-29"
last_updated: "2026-08-29"
status: active
version: "1.0.1"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Labeled market context for System A K4. Not revenue. Not a second contract.
  Not partner hours. Not the 72% labor cut from a published analog. Checkpoint
  NO_GO.
---

# К4: путь коммерциализации, не выручка

К4 — **потенциал** тиража. Часы A1–A8 по-прежнему пустые. Выручка в git = 0.
`k4_revenue_claimed() == False`.

## Три слоя (не склеивать)

| Слой | Что можно сказать | Источник | Чего нельзя |
|---|---|---|---|
| TAM | Рынок BIM РФ: **10,1 млрд ₽** (2022, +14,4% к 2021) | [TAdviser](https://www.tadviser.ru/index.php/%D0%A1%D1%82%D0%B0%D1%82%D1%8C%D1%8F:BIM-%D1%82%D0%B5%D1%85%D0%BD%D0%BE%D0%BB%D0%BE%D0%B3%D0%B8%D0%B8_%28%D1%80%D1%8B%D0%BD%D0%BE%D0%BA_%D0%A0%D0%BE%D1%81%D1%81%D0%B8%D0%B8%29) со ссылкой на «ГидМаркет», авг. 2023 | 10,1 млрд ₽ — не наш SAM |
| TAM горизонт | **25,1 млрд ₽** к 2030 (CAGR 13,7%) | ПИШ СПбПУ «Цифровой инжиниринг» / [FEA.RU](https://fea.ru/news/9217) | Не прогноз нашей выручки. `tam_horizon_is_our_revenue() == False` |
| SOM | Приз задачи = платный пилот **2 млн ₽** | Приложение 4 / ЛЭТИ | «Мы уже заработали 2 млн» |

SAM (автопроверка ПД/РД как слой поверх СОД/BIM-данных) **в рублях не оцениваем**.
Другой продукт МИК («упаковка инвестпроекта», рынок ≥500 млн) сюда не переносится.
Смешанная оценка PLM+BIM порядка 100 млрд ₽ сюда тоже не берётся.

## Путь, который комиссия может зачесть

1. MIT-ядро + коммерческая граница ADR-002 (adjudication, SLA-ops, SSO) — план,
   не поставленные SKU.
2. Второй покупатель = тот же класс: застройщик с IFC/IDS и своей СОД. Письма
   о намерениях в git **нет**.
3. Не конкурировать с checker атрибутов модели заказчика: мы — содержательная
   сверка комплекта (п. 2.2.2: файловый обмен на MVP достаточен).

Опубликованный аналог «−72,1% трудозатрат» на одной модели 5240 м²
([ИНФРА-М / Editorum](https://zh-szf.ru/ru/nauka/article/117090/view)) — **их**
корпус. Не переносить как эффект AeroBIM и не заполнять им A1–A8.
`foreign_labor_cut_as_ours() == False`.
