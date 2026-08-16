<!-- claims-lint: allow-file reason="PNST 909 22-scenario IDS axis; not product accuracy; NO_GO" -->
---
title: "PNST 909 — 22-scenario second coverage axis"
date: 2026-08-15
status: RUNTIME_PARTIAL
claim_boundary: >-
  Aggregated IDS coverage on Renga pack after ToS cite GO. AUTHOR_CLAIM.
  Not product accuracy. Checkpoint NO_GO.
---

# Вторая ось покрытия: 22 сценария ПНСТ 909-2024

Not product accuracy. Checkpoint **NO_GO**.

| Ось | Эталон | Метрика | Статус |
|---|---|---|---|
| A — Exp B | Перечни госэкспертиз | доля «обнаруживается» | **RUN** |
| B — ПНСТ 909 | 22 сценария + IDS Renga | runtime IDS на эталоне | **RUNTIME_PARTIAL** |

Evidence:  
- Pairing (frozen): [`pnst909-22-scenario-pairing.json`](pnst909-22-scenario-pairing.json)  
- Inventory: [`pnst909-22-scenario-ids-inventory-latest.json`](pnst909-22-scenario-ids-inventory-latest.json)  
- Runtime: [`pnst909-22-scenario-runtime-latest.json`](pnst909-22-scenario-runtime-latest.json) — **generated 2026-08-05**

**ToS cite:** **GO** (2026-08-05, owner relay) — можно публиковать **агрегированные** числа; бинарники в GH по-прежнему нельзя.

**CLI (15.08):** `python -m aerobim.tools.run_pnst909_22_scenario_runtime`  
Live pack on this machine is a **header sample** only (`IFC/pnst909-c14-mf-renga-87.ifc`). CLI returned **`SKIPPED_PACK_INCOMPLETE`** (0/18 paired IDS on disk) and **did not overwrite** the 05.08 snapshot. Do not invent a fresh 18/22.

## Результат прогона 05.08 (IfcTester / ifctester)

| Показатель | Значение |
|---|---:|
| Сценариев ПНСТ | 22 |
| IDS+IFC выполнено | **18** |
| Без IDS в скачанном комплекте | **4** (№ 3, 18, 21, 22) |
| Находки IDS на эталонном IFC | **0** на всех 18 (пакет собран под стандарт) |
| Класс | `runtime_clean` ×18 · `out_of_pack` ×4 |

**Как читать:** на «чистом» стандартоориентированном комплекте внешний IDS отрабатывает без срабатываний — ожидаемо для эталона ПНСТ. Это **не** precision на заказчике и не «90%». Это ось «умеем гонять внешний IDS / покрытие сценариев».

## DoD

1. ~~Пин~~ DONE · 2. ~~IDS inventory~~ DONE · 3. ~~Runtime на 18/22~~ DONE (05.08) · 4. ~~ToS cite GO~~ DONE  
5. Сценарии 3/18/21/22 — out_of_pack до появления IDS у издателя.  
6. CLI in tree (15.08). Fresh 18/22 requires restoring the full publisher extract under `.local/renga-pnst909/pack/`.
