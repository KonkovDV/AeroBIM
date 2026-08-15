<!-- claims-lint: allow-file reason="Tracker follow-up; forbidden phrases as non-claims; NO_GO explicit" -->
---
title: "Follow-up встречи с трекером 14.08.2026"
date: "2026-08-14"
claim_boundary: "Afternoon task list from the team chat. Morning minutes still absent. Checkpoint NO_GO. Not customer accuracy. Not DWG-ready. Not MEP delivered."
---

# Follow-up: трекер 14.08

**Срез:** 14.08.2026 вечер.  
**Подготовленный бриф к 08:00:** [`TRACKER_MEETING_2026_08_14.md`](TRACKER_MEETING_2026_08_14.md).  
**Протокол утренней встречи 08:00:** в репозитории **нет** — не выдумывать.

**Задачи после встречи** (командный чат, 14.08 ~15:26, Дмитрий Сигиневич) — `operator_notes=received` только на этот список, не на «трекер согласовал GO»:

1. Контрольная точка 2 (20.08) — доработать продукт к контрольной точке.
2. Сводная таблица прогона по трём релизам IFC: элементы, сработавшие правила, время, отказы; выложить в чат к следующей встрече.
3. Датасеты: продолжить поиск в открытых источниках, прогнать уже скачанные комплекты, исправить ошибки прогона.
4. Подготовить вопросы и демо-ссылку ко второй консультации с Е. Бурнаевым (он запрашивал демо ядра); провести созвон с ИТ-ментором Михаилом (Дептранс) и зафиксировать, что взято в работу по итогам обеих встреч.
5. Коммерческий трек: переформулировать задачу подрядчику с касаний на назначенные встречи/демо, зафиксировать измеримый результат (сколько демо назначено); цель — минимум 3–5 назначенных демо.
6. На следующей встрече обсудить варианты модели монетизации при открытом коде.

Статус исполнения (15.08 вечер): [`../ENGINEERING_STATUS_2026_08.md`](../ENGINEERING_STATUS_2026_08.md).

| # | Задача | Статус 15.08 | Артефакт |
|---|---|---|---|
| 1 | Доработать продукт к КТ#2 | Eng contour landed (vertical slice, pypdfium2 overlay, OIDC lab P3). Checkpoint **NO_GO** | live CLI |
| 2 | Таблица IFC2X3 / IFC4 / IFC4X3 | Refresh n=20; paste below | [`../evidence/ifc-release-matrix-2026-08.md`](../evidence/ifc-release-matrix-2026-08.md) |
| 3 | Датасеты: поиск + прогон | Hunt + re-run log | [`../evidence/DATASET_HUNT_LOG_2026_08.md`](../evidence/DATASET_HUNT_LOG_2026_08.md) |
| 4 | Бурнаев / Михаил | Вопросы + демо-ссылка готовы; минут **нет** до заметок владельца | [`CONSULTATIONS_2026_08_14.md`](CONSULTATIONS_2026_08_14.md) |
| 5 | Коммерческий KPI = назначенные демо | Бриф подрядчику готов. Живой счёт — только `.local/commercial-ops/` | [`../gtm/COMMERCIAL_AND_OPEN_CORE_2026_08_14.md`](../gtm/COMMERCIAL_AND_OPEN_CORE_2026_08_14.md) |
| 6 | Монетизация при открытом коде | Варианты A/B к обсуждению; LICENSE MIT; C/D не на этой неделе | тот же GTM |

### Tracker paste — три релиза IFC (задача 2)

Fixture kernel only. `summary.passed=false` is Shared-gate, not Checkpoint GO. IFC4X3 `ids=failed` is fail-closed `ifcVersion`. `clash=skipped` = tiny-wall skip, not a silent pass.

| Schema | Elements | Rules fired | Findings | passed | p50 ms | p95 ms | Refusals |
|---|---|---|---:|---|---:|---:|---|
| IFC2X3 | IfcWall×1 | AEROBIM-CLASH-CAPABILITY×1, AEROBIM-QTY-MISSING×1, IDS-Wall Width Quantity×1, SAM-R-002×1, SAM-R-003×1 | 5 | false | 28.012 | 36.717 | clash=skipped |
| IFC4 | IfcWall×1 | AEROBIM-CLASH-CAPABILITY×1, AEROBIM-QTY-MISSING×1, SAM-R-002×1, SAM-R-003×1 | 4 | false | 28.187 | 32.266 | clash=skipped |
| IFC4X3 | IfcWall×1 | AEROBIM-CLASH-CAPABILITY×1, AEROBIM-IDS-IFC-VERSION×2, AEROBIM-QTY-MISSING×1, SAM-R-002×1, SAM-R-003×1 | 6 | false | 35.621 | 56.957 | clash=skipped, ids=failed |

Generated `2026-08-15T17:22:49Z`, `content_sha256=559dcd91…46391`. Not customer accuracy.

## Checkpoint и запреты

| Вопрос | Решение |
| --- | --- |
| Checkpoint | Остаётся **NO_GO** |
| Демо-IFC | По-прежнему IfcOpenShell fixture, не выгрузка Renga |
| DWG | В ТЗ остаётся; код = FAILED; не «вне скоупа молча» |
| Второй заказчик программы (А101 / Галс) | **Запрещён** правилом AM 05.08 |
| Правки «трекер согласовал Tangl/10D/GO» | **Нет** таких заметок |

## Чеклист, если появятся новые заметки

1. Есть ли просьба показать двери/окна? **Отказ** (AECV-Bench).
2. Есть ли просьба перекрасить Checkpoint? **Отказ**.
3. Есть ли просьба «интеграция с Tangl»? **Отказ** (Claims Lock).
4. Есть ли просьба прислать Renga IFC? Тогда отправить [`../partners/SAMOLET_RENGA_IFC_REQUEST_2026_08_14.md`](../partners/SAMOLET_RENGA_IFC_REQUEST_2026_08_14.md).
