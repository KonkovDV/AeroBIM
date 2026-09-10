<!-- claims-lint: allow-file reason="HD24 reconciliation of incoming re-audit vs live git; Checkpoint GO; customer_go false; #40/#41/#44 OPEN; historical injection NO_GO pin" -->
---
title: "Триаж HD24 10.09.2026 — входящий переаудит vs живой git"
status: active
version: "1.0.0"
last_updated: "2026-09-10"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: coverage_map_only
claim_boundary: >
  Reconciles an incoming re-audit (public GitHub + attachments the author
  listed) with live AeroBIM git on 10.09 evening. Checkpoint GO
  (regulatory_measurement_mvp). customer_go false. Not product accuracy.
  Not customer SLA. Test counts live only in runtime-baseline-latest.json.
  1508 / 15 IFC / CNE 3419 are team 31.08 speech, not an independent re-run
  in this pass. Issues #40 / #41 / #44 stay OPEN. Do not quote 2/10 or
  4-5/10 as a customer-confirmation score.
auditor: "триаж × Red Team"
audited_head: "working tree 10.09 evening; origin/main 1c6352cc plus uncommitted launcher"
---

# Триаж HD24 — входящий переаудит vs живой git

Метод: входящий текст «Что сделано» (девять вложений, публичный GitHub,
buildingSMART / mos.ru / CII / NIST) сверён с живым деревом. Лексика:
**KILL / HOLD / ACCEPT**. Issues **#40 / #41 / #44** остаются **OPEN**.
`customer_go` **false**.

Входящий автор **не клонировал** репозиторий. Часть цифр у него — снимок
09.09 (`eff1f830…`, frontend 323, collected 3040). Живой pin — другой.

## 0. Итог

| ID | Verdict | Что |
|---|---|---|
| **HD24-PIN-01** | **ACCEPT входящее; pin уже сдвинут** | Цифры инвентаризации только из [`runtime-baseline-latest.json`](../evidence/runtime-baseline-latest.json). Сейчас: `attested_by=ci`, `commit_sha` `f9383efa40b1`, backend **3143** passed / **3163** collected / **20** skipped, frontend **350**, `source_loc` 100954, `test_loc` 66039. Не цитировать 323 / 3040 / `3c727a7` / `eff1f830` как HEAD. `extraction_macro_f1=0.86` — фикстура, **не** точность продукта. |
| **HD24-DATE-01** | **ACCEPT** | Прогон канала: **31.08**, не 03.09. 03.09 — письмо с шестью вопросами и трекер. 28.08 — эскалация режима данных, не «скачали 43 ГБ». Числа 31.08 (15 IFC, дисковый АР) — речь команды, не независимый повтор в этом проходе. |
| **HD24-PIK-01** | **ACCEPT** | В переданном наборе нет «анализа ПИК». Есть «Вопросы Самолёту» и «Жюри 5 человек». Не тащить ПИК в claims-lock речь. |
| **HD24-INJ-01** | **HOLD (не переписывать JSON)** | 0 убитых / **6** applied; `MISSING_ELEMENT` и `IDS_VIOLATION` не применялись. `control_issue_count=97`, `determinism_check=pass`, `plan_deviation` — пакет не seam-clean. Речь: «прокси-чувствительность выхода на неподготовленном пакете». Поле `"checkpoint": "NO_GO"` — HISTORICAL_PIN 03.09; живой SSOT GO. Remint = owner. Тест `LiveInjectionPinTests` запрещает ручной edit знаменателя. |
| **HD24-JOB-01** | **ACCEPT + комментарий в коде** | Нет durable worker (lease/heartbeat). Есть `Idempotency-Key`, лимит параллелизма (429), `request_cancel`, `reclaim_stale_queued`. Не говорить «заданий нет совсем». |
| **HD24-MEP-01** | **ACCEPT уже в коде** | `IfcSystemAwareClash`: выключен по умолчанию, нужен `scope_memo_ref`, fail-closed без `IfcSystem`, кольцо соседних пар среди первых ≤20 систем, геометрия не claimed. ТЗ по пересечениям инженерных систем **не** закрыто. |
| **HD24-CNE-01** | **HOLD** | Книги ЦНЭ № 3419 и «ПД после экспертизы» — рычаг отбора карточек (`WP-R19`), не PrecisionClaim.publishable и не 1:1 матч со строкой чек-листа (`RT-PLAN-22`). Не ставить жюри числовую оценку «подтверждения на данных заказчика». Не поднимать `customer_go`. |
| **HD24-PDF-01** | **ACCEPT уже в поставке 14.09** | Полный объём PDF канала не прогонялся; большие чертежи таймаутятся. Если карточки только с IFC — писать в «что не проверено». |
| **HD24-CAL-01** | **ACCEPT уже в git** | К **14.09**: стенд + 10–25 карточек + выжимка + просьба организатору переслать эксперту **до** 14.09 (`OA-25`). SBOM / checksum / restore — **19–21.09** (`OA-26`). Freeze 18.09. Не класть версионированный бандл в письмо 14.09. |
| **HD24-ABOUT-01** | **ACCEPT уже на GitHub** | `gh repo view` 10.09 вечер: About = «Checkpoint GO (regulatory_measurement_mvp). customer_go stays false until customer evidence.» Входящий «NO_GO until customer evidence» — устаревший снимок About, не текущий. |
| **HD24-DECK-01** | **HOLD** | Бинарь всё ещё `aerobim_kt2.pptx` / `.pdf`. Речь КТ#3 — `KT3_JURY_FAQ`. Пересборка pptx — owner, P2 до 18.09, не этот проход. |
| **HD24-I44-01** | **HOLD** | #44 остаётся OPEN как бэклог пилота (`OA-27`). Не закрывать комментарием агента. |
| **HD24-MIK-01** | **ACCEPT уже в git** | Три кресла партнёра **не** владеют 65 баллами. 40 баллов — отбор, не финал. Порог «не менее 50» vs «менее 50» — `OA-20` UNVERIFIED. |
| **HD24-DGP-01** | **ACCEPT уже в README** | Распоряжение ДГП-Р-56/26/64-16-473/26 от 18.08.2026 и городской плагин АГР под Revit — в шапке README. Native RVT не ingest. Не конкуренция Tangl/10D. |
| **HD24-UNVER-01** | **ACCEPT границу входящего** | `analyze_project_package.py` и PDF/OCR адаптеры входящий автор построчно не читал. Копии Положения МИК не в git. Веса 30/20/20/20/10 и 40/20/15/15/10 — `UNVERIFIED` до сверки с организатором. |

**OVERCLAIM продукта: 0.** Недифференцированное CLOSED: 0.

## 1. Что этот проход делает в git

1. Речь HD24 + строка в TIER0.
2. Комментарий JOB-01: идемпотентность / 429 / cancel / reclaim, без durable worker.
3. Evidence README + run-note: HISTORICAL_PIN на поле checkpoint инъекции.
4. GitHub #44: явный бэклог, не close.

## 2. Что **не** делать

- Не переписывать `defect-injection-recall-run-latest.json`.
- Не закрывать #40 / #41 / #44.
- Не перечеканивать CI pin локальным vitest/pytest.
- Не тащить 1508 / ЦНЭ 3419 в публичный git.
- Не называть покрытие книг экспертизы точностью продукта.
- Не собирать `aerobim_kt3.pptx` в этом проходе.
- Не ставить `samolet_pilot` и не обещать импорт в СОД.

## 3. Календарь (живой, не новый)

| Когда | Что | Не это |
|---|---|---|
| до 14.09 | Стенд, 10–25 карточек, двухстраничная выжимка, канал организаторов, OA-25 | Docker/SBOM/restore |
| 18.09 | Feature freeze | Новые фичи «чтобы набрать баллы» |
| 19–21.09 | Версионированная поставка КТ №3 | Письмо 14.09 |
| 19.09 11:00–12:20 | Репетиция с трекером | Сдача Самолёту |
| 22.09 | Демо-день трекера | customer_go |

## 4. Финал

Checkpoint **GO** (`regulatory_measurement_mvp`); `customer_go` **false**.
Входящий переаудит по содержанию совпадает с уже лежащими в git правилами
речи (14.09 vs 19–21.09, 0/6 не 0/8, JOB-01, MEP ring ≤20, GitHub About GO).
Устаревшие цифры входящего (323 / 3040 / About NO_GO) **не** копировать.
Это не приёмка, не SLA, не MEP delivered.
