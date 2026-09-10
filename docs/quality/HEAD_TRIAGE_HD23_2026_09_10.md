<!-- claims-lint: allow-file reason="HD23 Red Team + triage of PR #48 CI, local polish, D-04/D-08 code; Checkpoint GO; customer_go false; residual RT OPEN" -->
---
title: "Триаж HD23 10.09.2026 — PR #48, оболочка, P0 до показа"
status: active
version: "1.0.0"
last_updated: "2026-09-10"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: coverage_map_only
claim_boundary: >
  Red Team + triage of PR #48 CI, local review-shell polish, and D-04/D-08
  code on the working tree. Checkpoint GO (regulatory_measurement_mvp).
  customer_go false. Not a MIK score. Not product accuracy. Not customer SLA.
  Test counts live only in docs/evidence/runtime-baseline-latest.json.
auditor: "триаж × Red Team"
audited_head: "lands on main 10.09 evening; PR #48 red head must not merge"
---

# Триаж HD23 — 10.09 вечер

Метод: живой `main@71f5039`, открытый PR #48 (`c14061d`), лог Actions,
стенд Vite-dev; нужная работа садится на `main`. Лексика: **KILL / HOLD / ACCEPT**.
Issues **#40 / #41 / #44** остаются **OPEN**. `customer_go` **false**.

## 0. Итог

| ID | Verdict | Что |
|---|---|---|
| **HD23-CI-01** | **KILL → FIXED on main** | PR #48 `frontend` / `frontend-plan`: `TS2503 Cannot find namespace 'JSX'` в `IfcViewerErrorBoundary.test.tsx:10`. `function Fine(): JSX.Element` на React 19. CI `typecheck` — **mypy бэкенда**, не `tsc`. |
| **HD23-CI-02** | **KILL → FIXED on main** | На `c14061d` ещё `process.env.NODE_ENV`. На `main` — `import.meta.env.DEV`. Красный head #48 **не** вливать; ветку закрыть после посадки на `main`. |
| **HD23-SHOW-01** | **ACCEPT** | Показ — текущий `main` после этого коммита. Предыдущий CI-зелёный срез `71f5039` (run `34486902791`) — история. Локальный vitest **не** пин. |
| **HD23-PIN-01** | **HOLD** | Пин `3143 / 350`, `f9383efa40b1`, `attested_by=ci`, `workflow_ref=refs/pull/47/merge`. Не перечеканить локальным vitest. |
| **HD23-D04** | **HOLD → code** | Один `<main id="work-area">` в `App.tsx`. Вложенные `<main>` сняты. Не сертификат WCAG. |
| **HD23-D08** | **HOLD → code** | На экране «Эффект» карта покрытия (в т.ч. «не проверялось») **выше** блокеров и карты ТЗ. Не три слоя отчёта D-07. |
| **HD23-P40** | **KILL → FIXED on main** | Бейдж `P{n}` снят с карточки находки. Сортировка по `priority` остаётся серверной. |
| **HD23-D05** | **HOLD** | Виртуализация списка уже с `VIRTUALIZE_AFTER=40`. Не замерено на 1508 находках заказчика. |
| **HD23-D06** | **HOLD** | `thead` липкий у `.coverage-table` / `.capability-table`. Не закрывать WP-FE-36 без живого длинного списка. |
| **HD23-D07** | **HOLD** | Иерархия решение → находка → доказательство не сделана. Плотность ≠ закрытие отзыва 09.09. |
| **HD23-D12** | **HOLD** | Время эксперта не измерено. Только пилот. |
| **HD23-I40** | **HOLD** | WP-FE-26: чужой офлайн-ноутбук. Своя машина 09.09 и 10.09 не заменяет. |
| **HD23-I41** | **HOLD** | Живая пара `export-draft.json` / `export-confirmed.json` снята **локально** (оверлей `SMOKE-DRAW-001`). OA-21 закрывает владелец. |
| **HD23-I44** | **HOLD** | 0/6 и 1/8 injection; remint на HEAD — owner. |
| **HD23-RT** | **ACCEPT** | RT-001b/c, RT-002c, RT-003c OPEN. BFF 501. UI не пишет `summary.passed`. |

**OVERCLAIM продукта: 0.** Недифференцированное CLOSED: 0.

## 1. Что чинить в коде (этот проход)

1. Не вливать PR #48 с `JSX.Element`. Эквивалент (тест без `JSX.Element` + `import.meta.env.DEV`) садится на `main`.
2. Не показывать служебный `P 40` эксперту.
3. Скринридер: одна рабочая область `<main>`, skip → `#work-area`.
4. «Что не проверялось» — первый блок экрана «Эффект», не хвост после KPI.

## 2. Что **не** чинить «заодно» (Red Team)

- Не закрывать GitHub #40 / #41 / #44 комментарием агента.
- Не виртуализировать заново то, что уже есть; не объявлять D-05 закрытым.
- Не писать маршрут печати заказчику как «CDE-ready PDF».
- Не ставить `samolet_pilot` на чужой ноутбук.
- Не цитировать локальный счётчик vitest вместо пина.

## 3. Очередь доработки (после показа)

| Когда | Работа | Доказательство | Запрет |
|---|---|---|---|
| Сразу | Закрыть PR #48 без merge; единственная ветка `main` | Комментарий на #48 + `--delete-branch` | Не merge красного `c14061d` |
| До 14.09 | 10–25 карточек + CSV эксперту Самолёта с квитанцией | Receipt, не git push | Не «точность продукта» |
| До 14.09 | #41: владелец смотрит живую пару файлов | draft `review.state=null` vs confirmed `accepted` | Не «импорт в СОД» |
| Чужой ноутбук | #40 / WP-FE-26 | Пустой `AEROBIM_STORAGE_DIR`, HAR без CDN | Не vitest |
| После 18.09 freeze | WP-FE-37 слои отчёта, WP-FE-38 печать | Отзыв эксперта | Не feature-breadth |
| Owner | Remint injection на HEAD; колода `aerobim_kt2` | JSON прогона | Не править `checkpoint: NO_GO` у исторического файла |

## 4. Финал

Checkpoint **GO** (`regulatory_measurement_mvp`); `customer_go` **false**.
Этот проход чинит красный `tsc` PR #48 **на `main`**, снимает отладочный приоритет
с карточки и ставит ориентир `<main>` плюс «не проверялось» на первый слой
экрана «Эффект». Это не приёмка, не SLA, не MEP, не CDE-ready BCF.
