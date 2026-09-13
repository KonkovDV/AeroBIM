<!-- claims-lint: allow-file reason="HD27 Red Team of draft PR 52 walkthrough and FW-19 dirty-role guard; Checkpoint GO; customer_go false; #40/#41/#44 OPEN; PR 51 stays draft" -->
---
title: "Триаж HD27 13.09.2026 — разбор PR #52 и гвард смены режима"
status: active
version: "1.0.0"
last_updated: "2026-09-13"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: coverage_map_only
claim_boundary: >
  Red Team of draft PR 52 (docs-only frontend walkthrough) and the FW-19
  dirty-guard hole on origin/main@5cf113ce. Checkpoint GO
  (regulatory_measurement_mvp). customer_go false. Not product accuracy.
  Not customer SLA. Issues #40 / #41 / #44 stay OPEN. PR #51 stays draft
  until smoke:decision is run locally. Test counts live only in
  runtime-baseline-latest.json; do not remint locally.
auditor: "триаж × Red Team"
audited_head: "origin/main 5cf113ce plus FW-19 guard on this pass"
---

# Триаж HD27 — PR #52 и молчаливая потеря черновика

Метод: входящий текст (PR #52, overlay копирайта, FW-01…FW-24) сверён с
живым `useReviewShell` / `ui-copy.ts` / шапкой. Лексика:
**KILL / HOLD / ACCEPT**. `customer_go` **false**.

Показ ментору был **11.09**. Сегодня **13.09**. Календарный HOLD «не
трогать до показа» больше не действует. Остальные HOLD — по отсутствию
доказательства, не по дате.

## 0. Итог

| ID | Verdict | Что |
|---|---|---|
| **HD27-COPY-01** | **ACCEPT входящее** | `UI_COPY = { ...RU_COPY, ...WORKPLACE_COPY, ...EVIDENCE_COPY, ...ERGONOMICS_COPY }`. Шапка: `AeroBIM` / `Проверка проектной документации` / `Режим просмотра`. Маркеров `checkpoint GO` / `customer_go false` в шапке нет. Граница — свёрнутый блок «Область проверки и ограничения». Скриншот шапки сам по себе дисклеймер не несёт. |
| **HD27-FW19-01** | **KILL на срезе; FIXED в этом проходе** | `changeUiRole` писал роль и снимал рабочее место без `pendingNav`. Гвард стоял только на `requestWorkspaceView` / `requestSelectReport` / `openProjectReport`. Переключение на «Пользователь» при непустом черновике молча теряло правку. Фикс: `pendingNav.kind === "role"`; `setUiRole` + `persistUiRoleAlias` только в `resolveLeave`. «Остаться» роль не пишет. Одна строка `requestWorkspaceView` была бы недостаточна. |
| **HD27-P52-01** | **ACCEPT как снимок; файл на main** | PR #52 — draft, docs-only, MERGEABLE, один файл. Автор не запускал vitest/lint/build/smoke. `baseline-integrity` красный из-за отставания pin `f9383efa` — не дефект разбора. Файл посажен на `main` с баннером HD27; отдельный merge draft-PR с красным pin не делался. |
| **HD27-P51-01** | **HOLD** | PR #51 остаётся **draft**. Календарный «не мержить до 11.09» истёк. Остаётся HOLD: `npm run smoke:decision` локально не прогнан. На `main` при выгрузке с черновиком — `window.confirm`. Это ожидаемое поведение `main` (FW-24 / FE-CRUFT-02), не дефект показа. |
| **HD27-FW-REST-01** | **HOLD бэклог** | FW-01/02 (мёртвый слой `ru.ts`), FW-03 (фокус после отмены прогона), FW-04 (гибрид listbox), FW-12 (кнопка в live region), FW-13 (multi-drop → первый файл), FW-16/17 (изоляция / статус вьюера), FW-22 (раздел не в URL). Не «ментор нашёл дыру вживую». В этом проходе в браузере не гонялись. |
| **HD27-PIN-01** | **HOLD** | Pin `f9383efa`, `attested_by=ci`. Не чеканить локальным pytest/vitest. |
| **HD27-I40-01** | **HOLD** | #40 / #41 / #44 OPEN. Ни #51, ни #52, ни FW-19 их не закрывают. |

**OVERCLAIM: 0.** Недифференцированное CLOSED: 0. Отдельный GitHub issue на FW-19 не открывался: дефект закрыт кодом и тестом.

## 1. Что этот проход делает

1. Гвард черновика на смену «Режима просмотра» + vitest.
2. Текст диалога: «…раздел или режим просмотра».
3. Разбор PR #52 на `main` с честным статусом FW-19 / #51.
4. Речь HD27 + TIER0. PR #51 не merge. Dependabot не merge.

## 2. Что **не** делать сегодня

- Не merge #51, пока нет локального `smoke:decision`.
- Не закрывать #40 / #41 / #44.
- Не чеканить CI pin локальным vitest/pytest.
- Не вливать Dependabot (vitest 5 / plugin-react 6 / three).
- Не говорить «фронт сдан». Восемь разделов остаются `partial`.

## 3. Речь

Показ оболочки: `.\start.bat`. Показ жюри: `python -m aerobim.tools.run_kt3_jury`.
Checkpoint **GO**; `customer_go` **false**.
Шапка дисклеймер не несёт — раскрыть «Область проверки и ограничения».
На `main` выгрузка с черновиком по-прежнему даёт окно браузера; смена
режима просмотра при черновике больше не молчит.
