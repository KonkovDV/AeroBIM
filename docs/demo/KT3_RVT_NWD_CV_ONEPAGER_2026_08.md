<!-- claims-lint: allow-file reason="RVT/NWD/CV one-pager; OSINT prices; DWG-ready is forbidden; NO_GO" -->
---
title: "КТ#3 one-pager — RVT/NWD and computer vision (SIG-07)"
date: "2026-08-30"
last_updated: "2026-08-30"
status: active
version: "1.0.2"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Counted license fork plus CV scope. Not a native RVT/NWD reader.
  DWG-ready is forbidden. CADSoftTools 1660 USD is stale. Checkpoint NO_GO.
---

# RVT / NWD / CV — одна страница (защита)

Пункт 1.1.5 ТЗ называет закрытые форматы. Позиция **посчитанная**, не оправдательная. Источники OSINT: [`../quality/NATIVE_CAD_LICENSE_FORK_OSINT_2026_08.md`](../quality/NATIVE_CAD_LICENSE_FORK_OSINT_2026_08.md). Retrieved **2026-08-30**. Покупка не совершена.

## Лицензии (attributed)

| Путь | Цена (USD) | Что закрывает | Чего нет |
|---|---:|---|---|
| ODA Sustaining (1-й год) | 7 500 | DWG-контур ODA | **Не** Revit, **не** Navisworks |
| ODA BimRv | +6 250 / год | `.rvt` | Нужен Sustaining |
| ODA BimNv | +6 250 / год | Navisworks | Нужен Sustaining |
| Пара RVT+NWD, нижняя оценка 1-й год | **20 000** | — | Юрлицо; ежегодное продление |
| CADSoftTools CAD .NET | от **765** | DWG/DXF | Не RVT/NWD; «1 660» **устарело** |
| LibreDWG | GPL-3 | DWG | Несовместимо с MIT-ядром |
| Autodesk API для РФ юрлица | канал закрыт (news 2022+) | — | Не путь закупки к КТ#3 |

**Речь:** Sustaining 7 500 $ **не** покупает native RVT.

## Обход, который уже в ТЗ обмена

Штатный экспорт IFC 2x3 / IFC4 / IFC4x3 из authoring tool. Сводная NWD → IFC — на стороне назначающей стороны (вопрос SIG-05). Native ingest в MVP **fail-closed**. Локальный unpack 30.08: wrapper 27 `.rvt` / 21 Navis; unpack-дерево 75 `.rvt` / 8 Navis; unique-by-name **87** RVT (**2020** = 81, **2023** = 6; 20 workshared `RSN://`) и **3** NWD-федерации — носители, не reader.

## Компьютерное зрение (скоуп называем сами)

Сделано на фикстуре: зона листа, текстовый слой / overlay, привязка к sheet id.  
Нет: полноценный CV-разбор растра, подсчёт элементов, «чертёж как инженер».

## К3 / К5

Честный отказ + посчитанная вилка + регламент IFC. Честный NO_GO **без** плана обхода бьёт по посадке на карточку партнёра. Это не «мы читаем RVT».
