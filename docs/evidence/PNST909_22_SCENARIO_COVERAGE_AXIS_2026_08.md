---
title: "PNST 909 — 22-scenario second coverage axis"
date: 2026-08-05
status: RUNTIME_PARTIAL
claim_boundary: >-
  Aggregated IDS coverage on Renga pack after ToS cite GO. AUTHOR_CLAIM.
  Not product accuracy. Checkpoint NO_GO.
---

# Вторая ось покрытия: 22 сценария ПНСТ 909-2024

| Ось | Эталон | Метрика | Статус |
|---|---|---|---|
| A — Exp B | Перечни госэкспертиз | доля «обнаруживается» | **RUN** |
| B — ПНСТ 909 | 22 сценария + IDS Renga | runtime IDS на эталоне | **RUNTIME_PARTIAL** |

Evidence:  
- Inventory: [`pnst909-22-scenario-ids-inventory-latest.json`](pnst909-22-scenario-ids-inventory-latest.json)  
- Runtime: [`pnst909-22-scenario-runtime-latest.json`](pnst909-22-scenario-runtime-latest.json)

**ToS cite:** **GO** (2026-08-05, owner relay) — можно публиковать **агрегированные** числа; бинарники в GH по-прежнему нельзя.

## Результат прогона (IfcTester / ifctester)

| Показатель | Значение |
|---|---:|
| Сценариев ПНСТ | 22 |
| IDS+IFC выполнено | **18** |
| Без IDS в скачанном комплекте | **4** (№ 3, 18, 21, 22) |
| Находки IDS на эталонном IFC | **0** на всех 18 (пакет собран под стандарт) |
| Класс | `runtime_clean` ×18 · `out_of_pack` ×4 |

**Как читать:** на «чистом» стандартоориентированном комплекте внешний IDS отрабатывает без срабатываний — ожидаемо для эталона ПНСТ. Это **не** precision на заказчике и не «90%». Это ось «умеем гонять внешний IDS / покрытие сценариев».

## DoD

1. ~~Пин~~ DONE · 2. ~~IDS inventory~~ DONE · 3. ~~Runtime на 18/22~~ DONE · 4. ~~ToS cite GO~~ DONE  
5. Сценарии 3/18/21/22 — out_of_pack до появления IDS у издателя.
