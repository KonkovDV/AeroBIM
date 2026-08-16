<!-- claims-lint: allow-file reason="Video dry-run checklist; not a recorded mp4; NO_GO" -->
---
title: "КТ#2 — сухой прогон видео 17–18.08 + fallback"
date: "2026-08-16"
status: active
claim_boundary: "Operator checklist. Does not claim the mp4 exists in git. Checkpoint NO_GO."
---

# Dry-run видео (буфер до записи 19.08)

Трекер: запись 19.08 без буфера. Этот лист — **что сделать 17–18.08**. Сам mp4 в git не кладём.

## 17–18.08 (человек, чистая машина)

1. `cd backend && python -m aerobim.tools.run_demo_ifc_acceptance_gate`
2. Открыть свежие `artifacts/ifc-acceptance-gate-demo/report.html` и `acceptance-gate.json`.
3. Проговорить скрипт [`KT2_VIDEO_SCRIPT_3MIN_2026_08_19.md`](KT2_VIDEO_SCRIPT_3MIN_2026_08_19.md): PII первым, формула, framing сужения.
4. Записать **fallback-ролик** в `artifacts/demo/kt2-demo-fallback.mp4` (локально). Если железа нет — на защите **live CLI**, не молчать.

## Fallback на защите (если запись сломалась)

| Приоритет | Команда | Что открыть |
|---|---|---|
| 1 (sell-path) | `python -m aerobim.tools.run_demo_ifc_acceptance_gate` | `acceptance-gate.json` |
| 2 (overlay P1) | `python -m aerobim.tools.run_demo_vertical_slice` | `report.html` `#kt2-overlay` |

Не открывать snapshot `docs/evidence/kt2-handoff-2026-08-11/`.

Статус записи mp4: **NOT_IN_GIT** (ожидается оператор 17–19.08). Этот файл не заменяет ролик.
