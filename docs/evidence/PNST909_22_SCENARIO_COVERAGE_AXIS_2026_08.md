---
title: "PNST 909 — 22-scenario second coverage axis"
date: 2026-08-05
status: IDS_INVENTORY_DONE_RUNTIME_NOT_RUN
claim_boundary: >-
  Coverage map vs external standard scenarios + IDS. Not product accuracy.
  IDS inventory only until IFC runs. Checkpoint NO_GO.
---

# Вторая ось покрытия: 22 сценария ПНСТ 909-2024

**Зачем:** Exp B даёт карту vs типовые замечания экспертизы (AUTHOR_CLAIM). ПНСТ 909 даёт **независимый** машиночитаемый эталон требований (IDS).

| Ось | Эталон | Метрика | Статус |
|---|---|---|---|
| A — Exp B | Перечни госэкспертиз | доля «обнаруживается» | **RUN** (КР ≈16,7%; АР СПб/Амур — recount) |
| B — ПНСТ 909 | 22 сценария + IDS Renga | доля сценариев с IDS / runtime | **IDS inventory** — runtime **NOT_RUN** |

Evidence: [`pnst909-22-scenario-ids-inventory-latest.json`](pnst909-22-scenario-ids-inventory-latest.json)

## Inventory (локальный пин `.local/renga-pnst909/`)

| Показатель | Значение |
|---|---:|
| Сценариев ПНСТ | 22 |
| С IDS в скачанном комплекте | **18** |
| Без IDS в комплекте | **4** (№ 3, 18, 21, 22) |
| Файлов `.ids` | 45 |
| Runtime IFC+IDS выполнено | **0** |

Класс на сейчас: **ids_available** (18) / **out_of_pack** (4). Классы fires / conditional / out_of_scope — после прогона.

## DoD

1. ~~Пин комплекта Renga~~ **DONE**.  
2. ~~Таблица 22× IDS presence~~ **DONE** (JSON).  
3. Runtime proof per scenario — **NOT_RUN**.  
4. Публичные цифры — после ToS-GO от Renga.

**Не смешивать** с % Exp B в одной цифре.
