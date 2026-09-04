<!-- claims-lint: allow-file reason="RASE four-role demo on SP63 cover template; not customer_approved; NO_GO" -->
---
title: "RASE demo — SP63-COVER-SLAB-001 (template)"
date: "2026-08-28"
last_updated: "2026-08-28"
status: active
version: "1.0.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Four-role markup of one synthetic cover rule. Not SP 63 table 8.1.
  Not customer_approved. No fabricated DOI. Checkpoint GO; customer_go false.
---

# Четыре роли RASE на одном пункте (шаблон)

Источник разметки: Hjelseth & Nisbet 2011, CIB W78 Paper 45,
<https://itc.scix.net/paper/w78-2011-Paper-45>. DOI не выдумывается.

Правило: `SP63-COVER-SLAB-001` в
[`samples/rule-packs/sp63-cover-template.json`](../../samples/rule-packs/sp63-cover-template.json).
Пункт **8.3 (template)**. Это **not SP 63 table 8.1**. Пакет `approval: null`,
статус `synthetic-template`, на правиле `approval_status=synthetic`. Не
`customer_approved`. Не закрывает RT-002.

IDS 1.0 final: **2024-06-01**. IDS задаёт information requirements; этот
демо-ряд — инженерный порог толщины защитного слоя как **шаблон**, не таблица
эксплуатационных классов СП 63.

## R / A / S / E

| Роль | Смысл | Значение на `SP63-COVER-SLAB-001` | Поле отчёта |
|------|--------|-----------------------------------|-------------|
| **R** Requirement | Что должно выполняться | `CoveringThickness gte 20 mm` — template threshold, not SP 63 table 8.1 | `expected_value` / текст замечания |
| **A** Applicability | К кому | `IfcSlab` | `ifc_entity` |
| **S** Selection | Какое свойство | `Pset_CoveringCommon.CoveringThickness` | `property_set` / `property_name` |
| **E** Exception | Когда не применяется | not stated — template, not exposure class | не авто-выводится (`rase.py`) |

Трасса в находку: `norm_source` = СП 63.13330.2018, `norm_clause` = 8.3
(template), `expected_value` / `observed_value`, `rase_elements` (R+A+S,
advisory; E не авто). Машина:
`python -c "from aerobim.domain.rase_sp63_demo import rase_four_roles_from_cover_rule"`.

## Запрещено

- шаблон СП 63 утверждён заказчиком
- customer_approved на этом шаблоне
- выдуманный DOI
- точность >90%

Checkpoint **GO**; customer_go false.
