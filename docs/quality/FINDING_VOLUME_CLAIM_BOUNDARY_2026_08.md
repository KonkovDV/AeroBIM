<!-- claims-lint: allow-file reason="SIG-01 volume taxonomy; ALL/GUID/eq-sample/overlap; report phrase not accuracy; NO_GO" -->
---
title: "Finding volume claim boundary — SIG-01 taxonomy and engine fixes"
date: "2026-08-31"
last_updated: "2026-08-31"
status: active
version: "1.3.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  SIG-01 machine-record taxonomy and engine fixes (target_ref ALL on
  IFC/drawings/Qto, EXISTS coverage, mismatch cap, unrestricted_eq_sample,
  unsigned pack overlap, shared named-ref attributes, SPF GUID allowlist).
  Report phrase: объём находок на канале получен. Not product accuracy.
  Not pack processed. Not a customer defect list. Checkpoint NO_GO.
---

# Объём находок: граница заявления и исправления движка

Формулировка для отчёта: **«объём находок на канале получен»**.

Это **не** точность продукта, **не** «пакет обработан», **не** список дефектов заказчика, **не** ТЗ >90 %, **не** dual-rater F1. Checkpoint `NO_GO`. Имена и хэши пакета канала в git не публикуются (OA-9).

Машина: `python -c "from aerobim.domain.finding_volume import volume_from_findings, REPORT_PHRASE"`.

## Что считать записью

`volume_from_findings` хранит сырой счётчик `total` / `machine_record_count` и раскладывает записи по `by_volume_class`:

| Класс | Что это | Находка? |
|---|---|---|
| `unrestricted_eq_sample` | Поэлементное eq/gte на **неподписанном ALL** (потолок 50), даже если есть `element_guid` | Образец шаблона, не дефект |
| `element_detection_unsigned` | Поэлементное срабатывание на **именованном** `target_ref` | Детекция движка, порог не из СП |
| `coverage_unsigned` | Свойство/Qto не найдено ни на одном экземпляре типа; `missing on N of M`; suppressor после потолка; `AEROBIM-QTY-*`; `SAM-AR-001…019` | Факт покрытия пакета |
| `entity_presence` | В модели нет сущностей типа (`No elements found for entity …`) после корректного ALL | Честное отсутствие типа (в т.ч. файл КР без дверей) |
| `unsigned_universal_rule` | `REQ-FIRE-*` / `REQ-STR-*` / `REQ-MEP-*` без текста сообщения (учебный ALL-скоуп) | Не дефект заказчика |
| `data_integrity` | Дубликат/невалидный **IfcRoot.GlobalId** | Дефект данных, если GUID настоящий |
| `advisory_unsigned` | `AEROBIM-SPACE-EFFICIENCY-CANDIDATE` | Совет, пороги не подписаны |
| `service_hitl` | `AEROBIM-DRAWING-REGION-HITL` | Очередь эксперта, не находка |
| `service_capability` | `AEROBIM-CLASH-CAPABILITY` / IDS capability | Флаг возможности, не находка |
| `engine_record` | Прочее | Не классифицировать как дефект заказчика |

`service_record_count` = HITL + capability. `capped_eq_sample_count` = `unrestricted_eq_sample`. `publishable_finding_count` = 0, пока нет dual-rater. `suppressed_remainder_sum` — сумма «N further … suppressed», **не** число находок.

Учебные наборы (`samples/requirements/samolet-*.txt`, `samples/rule-packs/residential-ar-reference-template.json`) — **synthetic / unsigned**. `SAM-AR-020` (перила ≥ 1,2 м) на ALL — `unrestricted_eq_sample`, демо-порог, не СП.

Наблюдаемый `FireRating` стен канала (пакет A) — класс **EI 45**, не учебный `REI60` (IUA `SAM-09`). Это не «стены провалили СП 2.13130».

## Исправление 1: `target_ref=ALL`

В pipe-формате колонка `target_ref` со значением `ALL` (также `*`, `ANY`, пусто) значит «все экземпляры `ifc_entity`».

До исправления валидатор искал элемент с именем `all` (`_matches_target_ref`) и на живой модели со стенами выдавал `No elements found for entity IFCWALL`. Это артефакт шаблона×движка, не «стен нет».

После исправления: `aerobim.domain.target_ref.is_unrestricted_target_ref`. Именованный `target_ref` сверяется без учёта регистра по GlobalId / Name / LongName / Tag / ObjectType / Description (`element_matches_named_target_ref`) — и в IFC-валидаторе, и в Qto-сверке. Элемент, у которого Name буквально `ALL`, адресуется через GlobalId.

`eq REI60` на **всех** стенах в unsigned-пакете остаётся заведомо слишком широким правилом. После фикса ALL оно проверяет свойства. Если свойства нет ни на одном — одна запись покрытия. Если нет на части — одна запись `is missing on N of M`, не N ошибок. Несовпадения значения режутся потолком `UNRESTRICTED_ELEMENT_MISMATCH_CAP` (50) плюс одна строка «suppressed» (класс `coverage_unsigned`). Поэлементные образцы до потолка — класс `unrestricted_eq_sample`, даже при GUID. Текст mismatch на ALL: `unsigned pack; observed … expected …; not a statutory claim`. Тот же потолок — на чертежных правилах с `target_ref=ALL`. Qto на ALL не берёт первое совпадение: одна строка `mismatch on N of M`. Подписанный IDS должен сузить applicability.

`exists` на ALL — это покрытие «у скольких экземпляров есть свойство», а не «хотя бы у одного». Иначе один заполненный `IfcSpace` из 16 000 закрывал бы правило.

## Исправление 2: 22-символьное Name ≠ GlobalId

Пре-гейт схемы сканировал первую кавычечную строку длины 22 как GUID. `IfcPropertySingleValue.Name` = `TreadLengthAtInnerSide` (22 символа) и `IfcMaterial.Name` = `Stainless Steel_Weland` повторяются у не-IfcRoot сущностей — это не дубликат GlobalId.

Скан default-deny: только IfcRoot-семейства (`REL*`, стены/плиты/арматура `REINFORCING*` / `TENDON*`, `PROPERTYSET`) с алфавитом IfcGloballyUniqueId (`spf_line_rooted_global_id`). `IfcReinforcementDefinitionProperties` не сканируется (это не IfcRoot). Перенос GUID на следующую строку SPF склеивается. Настоящий дубликат на `IfcWall` по-прежнему WARNING (`AEROBIM-GUID-DUPLICATE`, verdict-neutral). Полный разбор IfcRoot — `collect_global_id_integrity_issues`.

## Исправление 3: overlap unsigned-пакетов

`REQ-FIRE-*` / `REQ-STR-*` (eq/gte/lte) и `SAM-AR-*` (в основном exists) делят ключ `entity+pset+property`. Пара `REQ-FIRE-001` и `SAM-AR-011` — это `Pset_WallCommon.FireRating` на `IFCWALL`, не два дефекта. Карта: `aerobim.domain.unsigned_rule_overlap.overlap_snapshot()`. `volume_from_findings` пишет `overlap_unsigned_groups` по правилам, которые реально встретились в прогоне.

## Что не утверждать

- Сырой `total` после прогона канала — не F1 и не «дефекты Самолёта».
- Не подписывать учебный ALL+eq как проверку СП 2.13130 / СП 63.
- Не выносить в git имена файлов, хэши, пообъектные GUID и сырой total пакета канала до письменного режима данных.
- Не складывать `REQ-*` и `SAM-AR-*` на одном свойстве как независимые дефекты.
- Не читать «N further suppressed» как N дефектов.

Связанные: [`TRACKER_EIGHT_TASKS_SIGINEVICH_2026_08.md`](TRACKER_EIGHT_TASKS_SIGINEVICH_2026_08.md) · [`SIG01_CHANNEL_TRIAGE_2026_08.md`](SIG01_CHANNEL_TRIAGE_2026_08.md) · ADR-001 (`summary.passed` не пишет LLM).
