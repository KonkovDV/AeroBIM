---
title: "Norm pack + RASE guide (Samolet pilot)"
status: active
version: "1.1.0"
last_updated: "2026-08-02"
claim_boundary: "Template/draft packs cannot drive positive customer verdict. RT-002 requires customer_approved + pack_hash + full approval object. Expert journal ≠ customer approval."
---

# Norm pack с RASE-разметкой

## Цель

Машиночитаемый пакет требований: отделить **текст нормы / интерпретацию** от **исполняемой проверки**, с fail-closed для неподтверждённых правил.

## Канонические файлы

| Файл | Роль |
|------|------|
| `samples/rule-packs/norm-rule-pack.schema.json` | JSON Schema 1.0.0 (legacy) + 2.0.0 (WP-04) |
| `samples/rule-packs/customer-norm-pack-intake-template.json` | Intake шаблон v2 (draft) |
| `samples/rule-packs/norm-pack-v2-draft-example.json` | Fixture example: deterministic + expert_required + awaiting journal |
| `backend/.../json_norm_rule_pack_loader.py` | Load + hash + status gates |
| `backend/src/aerobim/domain/norm_rule_eligibility.py` | Checkability + expert journal gate |
| `backend/src/aerobim/domain/rase.py` | Advisory R/A/S/E inference из structured requirement |
| `python -m aerobim.tools.list_expert_required_norm_rules` | Listing non-auto-checkable rules |

## RASE на правиле

| Элемент | Смысл | Поля pack (схема) | Поле `rase` |
|---------|-------|-------------------|-------------|
| **R** Requirement | Что должно выполняться | `requirement_text`, `evidence_text`, `clause_number` | `rase.requirement` |
| **A** Applicability | К каким объектам/стадиям | `object_type`, `discipline`, `stage`, `scope` | `rase.applicability` |
| **S** Selection | Какое свойство/величина | `property_set`, `property_name`, `operator`, `expected_value` | `rase.selection` |
| **E** Exclusion | Когда правило не применяется | текст исключения | `rase.exclusion` (`exception` = legacy alias) |

Интерпретация нормы (юридический текст) живёт в `source`/`norm_source` + `norm_edition` + `clause_number` + человекочитаемом R.  
Исполняемый критерий — только S + operator/value (+ A). Без S/operator правило **не** должно давать ERROR PASS.

Schema **2.0.0** требует на каждом правиле: `requirement_text`, `rase`, `object_type`, `discipline`, `stage`, `criticality`, `evidence_required`, `execution_mode`, `expert_confirmation_journal` (может быть `[]` до подтверждения).

## Статусы и fail-closed

| `status` | Использование | Positive verdict? |
|----------|---------------|-------------------|
| `synthetic` / `synthetic-template` / `draft` | Разработка, CI, демо | **Нет** |
| `expired` / `inapplicable` / `expert_required` / `retired` | Архив / вне scope / только эксперт | **Нет** |
| `approved` / `customer_approved` | Только с полным `approval` + `jurisdiction` + `pack_hash` | Да, в согласованном scope (и только checkable rules) |

`approval_ref` / `customer_approval_ref` **никогда** не достаточен без объекта `approval`.  
`claim_labels` с `synthetic` / `fixture` / `template` / `not-customer-evidence` **запрещают** `customer_approved`.

### Expert confirmation (WP-04)

- LLM может помочь структурировать текст правила.
- `execution_mode=deterministic` входит в авто-проверку **только** после journal entry с `decision=confirmed`.
- `execution_mode=expert_required` **никогда** не auto-check — listing via tool/report.
- Fixture `customer_approved` **не закрывает RT-002**.

## Минимальный чеклист правила

- [ ] `rule_id` стабильный
- [ ] R: формулировка требования + clause
- [ ] A: IFC entity / scope
- [ ] S: property + operator (+ expected_value где нужно)
- [ ] E: исключения явны (или «нет»)
- [ ] `norm_source` / edition / clause
- [ ] Тестовый пример (fixture finding или unit)
- [ ] `approval_status` на правиле согласован с пакетом

## Пример (черновик, не customer_approved)

```json
{
  "rule_id": "CUST-AR-SPACE-EXTERNAL-001",
  "scope": "ifc-property",
  "ifc_entity": "IfcSpace",
  "property_set": "Pset_SpaceCommon",
  "property_name": "IsExternal",
  "operator": "exists",
  "expected_value": null,
  "evidence_text": "Для помещений жилой секции свойство IsExternal должно быть задано.",
  "norm_source": "REPLACE-EIR-or-SP",
  "norm_edition": "REPLACE",
  "norm_clause": "REPLACE",
  "approval_status": "draft",
  "rase": {
    "requirement": "IsExternal shall be present on IfcSpace in residential pilot scope",
    "applicability": "IfcSpace in agreed building storeys; stage Р",
    "selection": "Pset_SpaceCommon.IsExternal exists",
    "exception": "Technical shafts marked out of scope in scope memo"
  }
}
```

Поле `rase` обязательно в schema 2.0.0; в 1.0.0 — опционально (вместе с `severity`/`criticality`, `finding_class`, `test_example_ref`). Loader сохраняет исполняемые поля; RASE + journal — критерий для экспертов и аудита.

## Связь с пилотом

1. Самолет утверждает содержимое → `customer_approved` + hash lock (RT-002).  
2. AeroBIM грузит pack через `AEROBIM_NORM_RULE_PACK`.  
3. Неполный / draft pack → capability fail-closed, не Shared-gate green по нормам.  
4. HITL может править правила только через versioned store + audit event (не silent overwrite).

## Вход от заказчика (перечень)

См. также [`../partners/SAMOLET_WHAT_WE_NEED_2026_07-ru.md`](../partners/SAMOLET_ACCEPTANCE_PROFILE_V0_1_2026_08_15.md):

1. Выписка EIR / критерии приёмки на пилот (1–2 стр + таблица свойств).  
2. Список СП/локальных стандартов **в scope** (не «все СП»).  
3. ≥20 типовых ошибок с примерами (калибровка).  
4. Подписант `approved_by` + даты действия.  
5. Область: дисциплины, стадии П/Р, исключения MEP/DWG.
