<!-- claims-lint: allow-file reason="KT#3 tracker six-task card; TZ 90%/SLA/MEP as non-claims; NO_GO" -->
---
title: "КТ#3 — карточка для трекера (6 задач 14.08)"
date: "2026-08-27"
last_updated: "2026-08-30"
checkpoint: NO_GO
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Tracker six-task status for KT#3. Not product accuracy. Not customer SLA.
  Not scheduled-demo counts in git. Checkpoint NO_GO.
---

# КТ#3 — трекер (6 задач)

Назначены **14.08 ~15:26**. КТ#2 был 20.08. Окно КТ#3: **03–21.09**.  
Машина: `python -c "from aerobim.domain.tracker_six_tasks import tracker_snapshot"`.  
Показ одной командой: `python -m aerobim.tools.run_kt3_jury`.

**Речь (дословно):** Tangl — слой модели. AeroBIM — шов комплекта (требования ↔ IFC ↔ листы ↔ ревизии). Не «заменим Tangl».

**После 29.08:** восемь задач трекера (назначены 29.08) — отдельный SSOT [`../quality/TRACKER_EIGHT_TASKS_2026_08.md`](../quality/TRACKER_EIGHT_TASKS_2026_08.md) (`tracker_eight_snapshot`). Не смешивать с таблицей ниже.

Checkpoint **`NO_GO`**. Письмо Самолёту отправляет человек, не репозиторий.

**После 25.08:** канал получен. Не говорить «нет данных заказчика». Хеш-пакет в git отсутствует. План в репо: [`../quality/KT3_IN_REPO_WORKPLAN_2026_08_27.md`](../quality/KT3_IN_REPO_WORKPLAN_2026_08_27.md).

| ID | Задача | В репо к КТ#3 | Не говорить |
|---|---|---|---|
| TRK-01 | Доработать продукт | Live CLI, `passed=false` на фикстуре | Checkpoint GO |
| TRK-02 | Таблица IFC2X3/4/4X3 | Kernel n=20, `passed=false` | Точность продукта по релизу IFC |
| TRK-03 | Открытые датасеты | IFC-Bench 27/1026 countable; Harbor NOT_RUN | Open bench = RT-001 |
| TRK-04 | Наука / ИТ-ментор | Вопросы в карточках КТ#3 | Выдуманные минуты консультаций |
| TRK-05 | KPI = 3–5 демо | Только локальный файл владельца | Число назначенных демо как факт git |
| TRK-06 | Монетизация при MIT | ADR-002 accepted | «Трекер согласовал Tangl/10D/SKU» |

Семь задач сравнения Техлаба — **не** эти шесть. Четыре бумаги Самолёта не склеивать. M2/M8 Фонда — `VERIFY_WITH_OPERATOR`.
