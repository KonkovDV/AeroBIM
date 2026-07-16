---
title: Norm / rule packs
status: active
last_updated: "2026-07-16"
---

# Подключение согласованного norm / rule pack

AeroBIM загружает версионированные JSON-наборы критериев через
`NormRulePackLoader`. Это **согласованные критерии приёмки проекта/компании**, а не
машинная копия «всех СП/ГОСТ».

## Claim boundary

- `synthetic-template` / badge `synthetic` — только инженерный шаблон; sign-off запрещён;
- `draft` — пакет на согласовании; sign-off запрещён;
- `approved` / alias `customer_approved` — загрузчик требует `approval` object +
  непустой `approval_ref` (`approval.scope_reference` или pack-level `approval_ref`);
  это фиксирует provenance, но не подменяет юридическую проверку;
- `retired` — исторический пакет; не использовать для нового обмена.

В репозитории есть
[`residential-ar-reference-template.json`](../../samples/rule-packs/residential-ar-reference-template.json)
с **20** AR-критериями. Его статус — `synthetic-template`; числовой пример
`SAM-AR-020` не является ссылкой на СП/ГОСТ и должен быть заменён заказчиком.

## Rule / finding provenance (P0.1)

Каждое правило и каждый `ValidationIssue`, порождённый из норм-пака, несёт Optional
поля:

| Поле | Смысл |
|---|---|
| `norm_source` | идентификатор нормы, напр. `СП 54.13330` |
| `norm_edition` | редакция / год |
| `norm_clause` | пункт |
| `approval_status` | `synthetic` \| `draft` \| `customer_approved` (из манифеста пака; default `synthetic`) |
| `approval_ref` | id / scope memo утверждения |

`approval_status` **проставляет loader/use-case из статуса манифеста пака**; rule-level
значение в JSON — декларативное для документации, runtime-authority = pack status.
При `customer_approved` без `approval_ref` загрузка **падает** (явный fail, не silent).

HTML/JSON export показывает бейдж `badge=<approval_status>` + src/ed/§/ref на finding.

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

Явный request-путь с отсутствующим/битым файлом → `capabilities.norm_rule_packs=failed`
и `summary.passed=false` (P0.2 fail-closed). Env-fallback ведёт себя так же: одна
плохая деплой-настройка не маскируется silent skip.

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
- [ ] `status` изменён на `approved`/`customer_approved` только после подписанного scope memo + `approval_ref`;
- [ ] digest и версия заморожены до benchmark run.

До получения пакета Самолёта закрыт только **loader + reference template +
provenance badge + HITL versioning scaffold**; customer-approved residential pack
остаётся внешним blocker.

## HITL-обновление норм-паков (P0.3)

Инженер может предложить/отредактировать правило без выдумывания утверждённого
заказчиком содержимого:

1. `POST /v1/norm-packs/{pack_id}/rule-events` с `base_pack_path` (в storage jail),
   `rule_diff`, `event_type` ∈ `norm_rule_proposed` | `norm_rule_edited`.
2. Use-case создаёт **новую** immutable версию `{base}+hitl.N` в ObjectStore
   (`norm-packs/...`); предыдущие ключи не перезаписываются.
3. `GET /v1/norm-packs/{pack_id}/versions` — история версий.
4. Повышение до `customer_approved` разрешено **только** при непустом
   `approval_ref`; иначе 400.
5. Review-event пишется с `resulting_pack_version` / `rule_diff_json`.
6. Finding provenance (`source` / `approval_status`) указывает на версию пака.

Это каркас «RU-норм-пак с provenance и HITL», **не** «утверждённый Самолётом пак».

## Drawing AI posture (retained local SSOT)

July 2026: [../evidence/DRAWING_AI_WORLD_PRACTICE_2026_07.md](../evidence/DRAWING_AI_WORLD_PRACTICE_2026_07.md).
