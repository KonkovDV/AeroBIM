---
title: Norm / rule packs
status: active
last_updated: "2026-07-11"
---

# Подключение согласованного norm / rule pack

AeroBIM загружает версионированные JSON-наборы критериев через
`NormRulePackLoader`. Это **согласованные критерии приёмки проекта/компании**, а не
машинная копия «всех СП/ГОСТ».

## Claim boundary

- `synthetic-template` — только инженерный шаблон; sign-off запрещён;
- `draft` — пакет на согласовании; sign-off запрещён;
- `approved` — загрузчик требует `approved_by`, timezone-aware `approved_at` и
  `scope_reference`; это фиксирует provenance, но не подменяет юридическую проверку;
- `retired` — исторический пакет; не использовать для нового обмена.

В репозитории есть
[`residential-ar-reference-template.json`](../../samples/rule-packs/residential-ar-reference-template.json)
с **20** AR-критериями. Его статус — `synthetic-template`; числовой пример
`SAM-AR-020` не является ссылкой на СП/ГОСТ и должен быть заменён заказчиком.

## Контракт

Schema: [`norm-rule-pack.schema.json`](../../samples/rule-packs/norm-rule-pack.schema.json).
Загрузчик дополнительно обеспечивает:

1. UTF-8 JSON, schema version `1.0.0`, лимит 2 MiB;
2. обычный файл `.json`, symlink отклоняется;
3. уникальные `pack_id@version` в одном запросе и уникальные `rule_id` внутри pack;
4. максимум 500 rules;
5. строгие `scope` / `operator`, обязательные поля по типу правила;
6. SHA-256 в `capabilities.norm_rule_packs.reason`;
7. fail-closed при ошибке parsing/approval — анализ не выдаёт пустой PASS.

Поддержаны `ifc-property`, `ifc-quantity`, `drawing-annotation` и операторы
`eq`, `gte`, `lte`, `exists`. IDS 1.0 остаётся отдельным входом: JSON pack не
выдаётся за IDS и не содержит геометрических predicates.

## API path

1. Загрузить IFC и JSON pack через `POST /v1/uploads`.
2. Передать возвращённые storage-relative paths в analyze:

```json
{
  "ifc_path": "uploads/<id>/model.ifc",
  "requirement_text": "",
  "norm_rule_pack_paths": [
    "uploads/<id>/customer-ar-pack.json"
  ]
}
```

Для синхронного и job-based анализа используется один и тот же
`ValidationRequest`; path jail применяется до loader.

## Путь до пакета: manifest / env (не хардкод)

Путь до customer-пакета задаётся **двумя** способами, без хардкода:

1. **Через manifest запроса** — поле `norm_rule_pack_paths` в теле analyze
   (см. выше). Имеет приоритет; несколько пакетов допустимы.
2. **Через env** `AEROBIM_NORM_RULE_PACK` — storage-relative fallback, когда
   запрос не перечислил пакеты (например единый корпоративный pack на
   деплой). Резолвится внутри storage jail (`resolve_storage_path`).

Состояния capability `norm_rule_packs` (честно, без silent degradation):

| Условие | `capabilities.norm_rule_packs.status` |
|---|---|
| Пакеты не заданы (ни manifest, ни env) | `skipped` |
| Задан env-путь, но файл **отсутствует** | `failed` (fail-closed, **не** silent skip) |
| Пакет(ы) загружены | `ok`; `reason` содержит `pack_id@version[status] sha256:…` |
| Загружен non-approved пакет (`synthetic-template`/`draft`) | `ok` + пометка `advisory: non-approved pack(s) — not for deterministic sign-off` |

Явный request-путь с отсутствующим/битым файлом по-прежнему fail-closed через
исключение loader (жёсткая ошибка запроса); env-fallback деградирует до `failed`
capability, чтобы одна плохая деплой-настройка не роняла каждый анализ.

## Свойство → rule pack / IDS (how-to)

Короткая шпаргалка: **что** проверяем и **чем** — JSON rule pack (property /
quantity / drawing acceptance criteria) или IDS 1.0 (facet-based требования). IDS
остаётся отдельным входом; JSON pack не выдаётся за IDS и не содержит геометрии.

| Что проверяем | scope | operator | Поля пакета (пример) | Или через IDS |
|---|---|---|---|---|
| Огнестойкость стены = REI60 | `ifc-property` | `eq` | `ifc_entity=IFCWALL`, `property_set=Pset_WallCommon`, `property_name=FireRating`, `expected_value=REI60` | IDS property facet |
| Высота помещения ≥ 2.5 м | `ifc-quantity` | `gte` | `ifc_entity=IFCSPACE`, `property_name=Height`, `expected_value=2.5`, `unit=m` | IDS + quantity |
| Наличие несущего признака | `ifc-property` | `exists` | `ifc_entity=IFCWALL`, `property_name=LoadBearing` | IDS existence facet |
| Класс бетона на чертеже = B25 | `drawing-annotation` | `eq` | `target_ref=CONCRETE-NOTE`, `property_name=concrete.class`, `expected_value=B25` | — (2D аннотация) |

Правило: **геометрия / клэши / пространственные предикаты — НЕ в property pack и
НЕ в IDS**; они идут через clash / SPATIAL контур (см. claim boundary). Единицы
нормализуются в SI на сравнении (`m`/`mm`/`m2`/угол), как в section pairing.

## Customer intake / approval checklist

- [ ] зафиксированы типология, стадия, дисциплина и обмен;
- [ ] каждый `rule_id` привязан к EIR/ТЗ/корпоративному критерию;
- [ ] значения и единицы проверены ГИП/нормоконтролем;
- [ ] geometry/clash rules вынесены из IDS/property pack;
- [ ] два инженера подтвердили pilot scope и правила adjudication;
- [ ] `status` изменён на `approved` только после подписанного scope memo;
- [ ] digest и версия заморожены до benchmark run.

До получения пакета Самолёта закрыт только **loader + reference template**;
customer-approved residential pack остаётся внешним blocker.

## Drawing AI posture (retained local SSOT)

July 2026: [../evidence/DRAWING_AI_WORLD_PRACTICE_2026_07.md](../evidence/DRAWING_AI_WORLD_PRACTICE_2026_07.md).
