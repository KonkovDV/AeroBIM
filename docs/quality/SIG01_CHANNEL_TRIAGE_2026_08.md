<!-- claims-lint: allow-file reason="SIG-01 channel Red Team triage; volume≠accuracy; ALL/EI45/overlap; NO_GO" -->
---
title: "SIG-01 channel Red Team triage — 2026-08-31"
date: "2026-08-31"
last_updated: "2026-08-31"
status: active
version: "1.0.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: pack_volume_not_accuracy
detected_count: 0
claim_boundary: >
  KILL/HOLD/ACCEPT over the local SIG-01 IFC/PDF rerun after ALL matching.
  Report phrase: объём находок на канале получен. Not product accuracy.
  Not pack processed. Not a customer defect list. Unsigned ALL+eq is not SP.
  Channel totals stay .local. Checkpoint NO_GO.
---

# Триаж канала SIG-01 (31.08.2026)

Машина: `python -c "from aerobim.domain.sig01_channel_triage import triage_snapshot"`.

Проход после фикса `target_ref=ALL` и пре-гейта GUID. Локальный прогон IFC/PDF на канале 25.08 — **не** в git (OA-9). Сырой счётчик записей машины остаётся в `.local/`. Формулировка для отчёта: **«объём находок на канале получен»**.

Носители (без имён): 15 IFC, схема IFC2X3; 6 АР + 5 КР в пакете A; QTO `NetFloorArea` = 0; заполненный `FireRating` стен пакета A — класс **EI 45**, не учебный `REI60` ([deep-study](../evidence/deep-study-carrier-facts-2026-08.md), IUA `SAM-09`). PDF-выборка даёт HITL, не находки чертежа.

Checkpoint **`NO_GO`**. `detected_count: 0`. `publishable_finding_count: 0`.

Связанные: [`FINDING_VOLUME_CLAIM_BOUNDARY_2026_08.md`](FINDING_VOLUME_CLAIM_BOUNDARY_2026_08.md) · [`TRACKER_EIGHT_TASKS_SIGINEVICH_2026_08.md`](TRACKER_EIGHT_TASKS_SIGINEVICH_2026_08.md).

## Этот проход (KILL / ACCEPT)

| ID | Атака | Тормоз |
|---|---|---|
| RT-SIG01-ACCURACY | Сырой total = точность / F1 | `is_accuracy=false`; `publishable_finding_count=0` |
| RT-SIG01-DEFECT | Объём канала = дефекты Самолёта | `is_customer_defect_list=false`; только фраза отчёта |
| RT-SIG01-PACK | 15/15 IFC прогнаны = пакет обработан | `is_pack_processed=false`; census `processed=false` |
| RT-SIG01-SP | Unsigned ALL+eq REI60 = проверка СП 2.13130 / СП 63 | Учебные `samolet-*.txt` / SAM-AR; RT-002b OPEN |
| RT-SIG01-EI45 | EI 45 vs демо-REI60 = провал огнестойкости | IUA SAM-09; не класс II / C0 |
| RT-SIG01-CAP-RAISE | Поднять потолок 50 = полный список дефектов | Потолок — граница честности; suppressor ≠ дефекты |
| RT-SIG01-SUPPRESS-N | «N further suppressed» = N дефектов | `suppressed_remainder_is_finding_count=false` |
| RT-SIG01-EQ-AS-DETECT | Поэлементные ALL+eq (есть GUID) = `element_detection_unsigned` | Класс `unrestricted_eq_sample` |
| RT-SIG01-OVERLAP | REQ-FIRE-001 + SAM-AR-011 = два дефекта | `unsigned_rule_overlap`; exists+eq на одном ключе |
| RT-SIG01-KR-DOOR | «Нет IfcDoor» на файле КР = нет дверей как дефект | `entity_presence`; 6 АР + 5 КР |
| RT-SIG01-PDF-HITL | Строки HITL PDF = находки чертежа / счёт дверей | `service_hitl`; IUA SAM-03 |
| RT-SIG01-PDF-GIT | Имена листов / GUID / тоталы канала в git | OA-9; `names_in_git=false` |
| RT-SIG01-QTO-TEP | Нет NetFloorArea = ТЭП Does-not | `coverage_unsigned`; Missing QTO ≠ ТЭП |
| RT-SIG01-SLA | Время RocksDB = SLA заказчика | `publishable_sla=false`; IUA SAM-06 |
| RT-SIG01-MEP | Skip clash-capability = MEP delivered / failed | `service_capability`; RT-003 OPEN |
| RT-SIG01-IDS | Учебные пакеты закрывают RT-002 | 002a ≠ 002b; `closes_rt002=false` |
| RT-SIG01-F1 | Классы объёма = dual-rater / каталог типовых | `customer_confirmed_patterns=0` |
| RT-SIG01-RAIL | SAM-AR-020 ≥ 1,2 м = проверка перил по СП | Демо-порог шаблона; `unrestricted_eq_sample` |
| RT-SIG01-ALL-FIX | ALL по-прежнему ищет элемент с именем ALL | `is_unrestricted_target_ref` — все экземпляры типа |
| RT-SIG01-GUID-FIX | 22-символьное Name свойства = дубликат GlobalId | Default-deny allowlist IfcRoot |
| RT-SIG01-EXISTS-FIX | exists на ALL проходит, если свойство есть у одного из N | Строка `missing on N of M` |

## Что чинить в движке на этом проходе

1. **Класс `unrestricted_eq_sample`.** Записи «property does not match» на unsigned ALL больше не падают в `element_detection_unsigned` только потому, что у них есть GUID.
2. **Overlap.** Пара `REQ-*` (eq) и `SAM-AR-*` (exists) на том же `entity+pset+prop` — один факт покрытия, не два дефекта. Карта: `unsigned_rule_overlap.overlap_snapshot()`.
3. **Сообщение mismatch.** На unrestricted eq текст несёт `unsigned pack; observed … expected …; not a statutory claim`, чтобы EI 45 vs REI60 не читалось как СП.

Не поднимать потолок 50. Не коммитить `.local/pack-out`. Не публиковать сырой total как метрику продукта.
