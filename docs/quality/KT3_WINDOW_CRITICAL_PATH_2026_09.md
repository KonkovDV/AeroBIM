<!-- claims-lint: allow-file reason="KT#3 window critical path; Red Team; not a score forecast; NO_GO" -->
---
title: "КТ#3 window — critical path, Red Team pass 25 (03–21.09.2026)"
date: "2026-08-30"
last_updated: "2026-08-30"
status: active
version: "1.0.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Academic critical-path note for the KT#3 window. Not a predicted
  commission total. Not customer pack contents. Checkpoint NO_GO.
---

# Окно КТ#3: критический путь (Red Team, проход 25)

Рамка окна: **3–21 сентября 2026**; демо-день 29–30 сентября; трек-встречи по пятницам 08:00. Этот файл — **не** содержимое канала заказчика и **не** прогноз балла (`predicted_aerobim_total() is None`).

Машина: `python -c "from aerobim.domain.tracker_eight_tasks import tracker_eight_snapshot"`.
SSOT восьми задач: [`TRACKER_EIGHT_TASKS_2026_08.md`](TRACKER_EIGHT_TASKS_2026_08.md).

Три блокера приёмки кодом не закрываются: размеченный корпус (RT-001), подпись назначающей стороны на профиле (RT-002b), федеративная MEP-модель (RT-003). Поэтому коммуникации (данные, профиль, вузы) не отодвигаются разработкой. Из восьми задач трекера **единственная с реальной угрозой сорвать 21.09 по коду** — внешний контур (задача 3): production OIDC BFF = `DESIGNED` / `NOT_IMPLEMENTED`, default HTTP **501**; лабораторный cookie-путь честно не production SSO. Фича-фриз **18.09** — нагрузка, не формальность.

## Конструкт-валидность (Messick 1995; Kane 2013)

| Вывод, который просят | Лицензия сейчас | Почему нет |
|---|---|---|
| «Норм нет, RT-002 открыт» | запрещён | RT-002a CLOSED: публичные IDS (Мособлгосэкспертиза, 06.03.2026, [moexp.ru/news/395](https://www.moexp.ru/news/395/); АГР Москвы; СПб ЦГЭ) + `pack_hash`. Открыт **002b** (нет подписи Самолёта). Разница: нет *подписи*, не нет *норм* |
| Fixture AABB P/R = 1,0 при n=6 как аргумент жюри | запрещён | Wilson score 95% (Wilson 1927; Brown, Cai & DasGupta 2001): при 6/6 нижняя граница ≈ **0,61** (`wilson_interval(6, 6)` в `study_design.py`). Wald на крайней доле вырождается; показывать «единицу» даже с оговоркой — Messick *consequence*: жюри услышит точность. Стоп-лист карточки речи, п. 28 |
| «TBD в ТЗ — заполните» | запрещён | Пять разделов закрыты редакцией v2 в `docs/tz/` (архитектура, код/сборка, образ, презентация, сопроводительная). Организаторам — **подтвердить редакцию**, не писать с нуля |
| «Неэффективное использование пространства сдано / не нужно» | запрещён | Единственная целевая строка «не реализовано» в карте покрытия. Заказчик назвал критерий 25.08 (продаваемая площадь, МОП, коридоры). Скоуп — **OA-14**, до репетиции 22.09 |
| «Sustaining ODA 7 500 $ = native RVT/NWD» | запрещён | [`NATIVE_CAD_LICENSE_FORK_OSINT_2026_08.md`](NATIVE_CAD_LICENSE_FORK_OSINT_2026_08.md): BimRv/BimNv — отдельные 6 250 $ |
| «Поднимим SPF cap — перепишем парсер» | запрещён | `AEROBIM_MAX_IFC_BYTES` — SPF in-memory, сопоставим с капом bSI Validation Service (256 MB несжатого `.ifc`). 1,5 ГБ — ingest + RocksDB. Подъём SPF = нагрузочный RSS, не rewrite |
| Lab cookie = production SSO | запрещён | `auth_bff=NOT_IMPLEMENTED`; Phase 3 gated |

## Последовательность задач (логика, не обещание сроков)

Задача 2 (инвентарь) → задача 1 (прогон поддерживаемого: IFC + PDF) → задача 4 (классификатор и метрики). Задача 3 параллельна с первого дня. Задачи 5, 6, 7, 8 — коммуникация и аналитика. Реестр и производные канала **не** коммитятся до письменного режима данных (OA-9).

Метрика прогона без эталона: **объём находок на данных канала**, не процент точности. Macro F1 = 0,86 (закрытые фикстуры) и 0,43 (AECV-Bench) **не** смешивать с третьей цифрой.

## Сдача окна (19–21.09) — честный состав

Реестр (вне git до OA-9) · отчёты прогонов · классификатор ≥ 20 типов · протокол измерения · стенд двух ролей **если** OIDC не 501 · записка ЛИРА (четыре проверки) · позиция RVT/NWD+CV · журнал запросов. Если замера на размеченном комплекте нет — нести **NO_GO** с работающим ядром, не перекрашивать.

Связанные: [`KT3_IN_REPO_WORKPLAN_2026_08_27.md`](KT3_IN_REPO_WORKPLAN_2026_08_27.md) · [`TZ_LIVE_TREE_TRIAGE_2026_08_27.md`](TZ_LIVE_TREE_TRIAGE_2026_08_27.md) · [`OWNER_ACTIONS_2026_09.md`](../OWNER_ACTIONS_2026_09.md) · [`CALCULATION_COMPARE_FOUR_CHECKS_2026_09.md`](CALCULATION_COMPARE_FOUR_CHECKS_2026_09.md) · [`KT3_HYPERPLAN_TRIAGE_RT_WH_2026_09.md`](KT3_HYPERPLAN_TRIAGE_RT_WH_2026_09.md).
