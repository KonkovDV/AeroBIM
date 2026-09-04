<!-- claims-lint: allow-file reason="Order-weight verification sheet; PDF column empty; UNVERIFIED; NO_GO" -->
---
title: "Order weights verification — attributed until PDF column is filled"
date: "2026-08-30"
last_updated: "2026-08-30"
status: active
version: "1.0.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Six-row checklist to reconcile the owner briefing with Fund PDFs. The PDF
  column stays empty. While UNVERIFIED, weights stay attributed, not
  attested_by=ci. Not a predicted score. Checkpoint GO; customer_go false.
---

# Сверка весов с PDF (колонка PDF пустая)

PDF приказа и Положения **в git нет**. Пока строка UNVERIFIED, цитата в речи —
**attributed** (`attested_by=owner_briefing`). Не `attested_by=ci`.

Машина: `python -c "from aerobim.domain.mik_commission_scoring import scoring_snapshot"`.

| # | Что сверяем | В git сейчас | В PDF | Статус |
|---|---|---|---|---|
| 1 | Наименования критериев отбора и финала | К1–К5 (протокол приказа); Б1–Б5 — брифинг, **не** Приложение 3 Положения | | **UNVERIFIED** |
| 2 | Веса | A: 40/20/15/15/10; B-briefing: 30/20/20/20/10; сумма каждой таблицы 100 | | **UNVERIFIED** |
| 3 | Формулировка порога приза | Рабочий порог **не менее 50**; в Порядке встречается «менее 50»; `prize_floor_wording_is_ambiguous=True`; знаменатель финальной суммы неизвестен | | **UNVERIFIED** |
| 4 | Тай-брейк | A: К3, затем К4 (новизна не участвует); B-briefing: только Б1 | | **UNVERIFIED** |
| 5 | Кворум и счёт | Отбор: среднее, кворум ≥3; финал: **сумма**; круг финала шире номинала | | **UNVERIFIED** |
| 6 | П. 6.3 исключительные права | Риск программы; LICENSE MIT; [`ADR-004-prize-ip-mit-fork-2026.md`](../architecture/ADR-004-prize-ip-mit-fork-2026.md) | | **UNVERIFIED** |

Заполнение колонки «В PDF» — действие владельца (OWNER_ACTIONS), не этот файл.
Пока UNVERIFIED: `regulation_appendix_3_in_git() == False`.

Задача Самолёта — **№6** (приложение 4). Комиссия — **№7**.
