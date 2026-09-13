<!-- claims-lint: allow-file reason="HD28 Red Team of FE-CRUFT-02 export dialog; Checkpoint GO; customer_go false; #40/#41/#44 OPEN; live smoke is rehearsal not OA-21 close" -->
---
title: "Триаж HD28 13.09.2026 — диалог выгрузки вместо native confirm"
status: active
version: "1.0.0"
last_updated: "2026-09-13"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: coverage_map_only
claim_boundary: >
  Lands FE-CRUFT-02 / FW-24 on main after a local live-review smoke.
  Checkpoint GO (regulatory_measurement_mvp). customer_go false. Not
  product accuracy. Not customer SLA. Issues #40 / #41 / #44 stay OPEN.
  The rehearsal does not close OA-21. Test counts live only in
  runtime-baseline-latest.json; do not remint locally.
auditor: "триаж × Red Team"
audited_head: "origin/main 5f5846d5 plus FE-CRUFT-02 on this pass"
---

# Триаж HD28 — FE-CRUFT-02 / FW-24

Метод: черновик PR #51 сверён с `main@5f5846d5` (после FW-19), конфликт
только в `workplace.ts`. Диалог посажен на текущий `main` одним проходом
вместе со смоуком и сторожем. Лексика: **KILL / HOLD / ACCEPT**.
`customer_go` **false**.

## 0. Итог

| ID | Verdict | Что |
|---|---|---|
| **HD28-CRUFT02-01** | **KILL на срезе; FIXED в этом проходе** | Нативный `window.confirm` убран. `ExportUnsavedDialog` (`<dialog role="alertdialog">`). Текст `exportUnsavedConfirm` не менялся. Сторож HD24-FE-01 больше не имеет списка исключений. Репетиция читает разметку (`settleUnsavedExportDialog`) и падает на любом нативном окне (`nativeDialogs: []`). |
| **HD28-SMOKE-01** | **ACCEPT репетицию; не OA-21** | `python -m aerobim.tools.run_live_review_smoke --skip-demo-seed` на этой машине: `decision_smoke.ok=true`, draft `reviewState=null`, confirmed `accepted`, 501 на `/v1/auth/bff` ожидаем. Это репетиция стенда, не закрытие #41 / OA-21. |
| **HD28-P51-01** | **ACCEPT код; draft PR не merge** | Ветка PR #51 пересекалась с FW-19 в `dirtyLeaveBody`. Код взят с ветки, строка FW-19 сохранена. Squash-merge красного backend CI той ветки не делался. |
| **HD28-FW01-01** | **ACCEPT сторож; не чистка** | Vitest `ui-copy-overlay.test.ts` фиксирует 90 ключей `ru.ts`, которые на экран не попадают. Новый тихий overlay сломает тест. Сами мёртвые строки не удалялись. |
| **HD28-PIN-01** | **HOLD** | Pin `f9383efa`. Не чеканить локальным pytest/vitest. |
| **HD28-I40-01** | **HOLD** | #40 / #41 / #44 OPEN. Смоук не живой артефакт владельца. |

**OVERCLAIM: 0.** Недифференцированное CLOSED: 0. Dependabot не merge.

## 1. Что этот проход делает

1. Диалог выгрузки + смоук + сторож на `main`.
2. Сторож перекрытого копирайта (FW-01/02).
3. Речь HD28 + TIER0. #40 / #41 / #44 не закрывать.

## 2. Что **не** делать сегодня

- Не закрывать #40 / #41 / #44.
- Не чеканить CI pin.
- Не вливать Dependabot (vitest 5 / plugin-react 6 / three).
- Не говорить «фронт сдан». Восемь разделов остаются `partial`.
- Не называть репетицию смоука закрытием OA-21.

## 3. Речь

Показ оболочки: `.\start.bat`. Показ жюри: `python -m aerobim.tools.run_kt3_jury`.
Checkpoint **GO**; `customer_go` **false**.
Шапка дисклеймер не несёт — раскрыть «Область проверки и ограничения».
Выгрузка с черновиком спрашивает диалогом оболочки, не окном браузера.
