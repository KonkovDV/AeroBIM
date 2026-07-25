---
title: "Norm pack + RASE guide (Samolet pilot)"
status: active
version: "1.0.0"
last_updated: "2026-07-24"
claim_boundary: "Template/draft packs cannot drive positive customer verdict. RT-002 requires customer_approved + pack_hash + full approval object."
---

# Norm pack с RASE-разметкой

## Цель

Машиночитаемый пакет требований: отделить **текст нормы / интерпретацию** от **исполняемой проверки**, с fail-closed для неподтверждённых правил.

## Канонические файлы

| Файл | Роль |
|------|------|
| `samples/rule-packs/norm-rule-pack.schema.json` | JSON Schema 1.0.0 |
| `samples/rule-packs/customer-norm-pack-intake-template.json` | Intake шаблон (draft) |
| `backend/.../json_norm_rule_pack_loader.py` | Load + hash + status gates |
| `backend/src/aerobim/domain/rase.py` | Advisory R/A/S/E inference из structured requirement |

## RASE на правиле

| Элемент | Смысл | Поля pack (текущая схема) | Поле `rase` (рекомендуемо) |
|---------|-------|---------------------------|----------------------------|
| **R** Requirement | Что должно выполняться | `evidence_text`, `instructions`, `norm_clause` | `rase.requirement` |
| **A** Applicability | К каким объектам/стадиям | `ifc_entity`, `scope`, disciplines пакета | `rase.applicability` |
| **S** Selection | Какое свойство/величина | `property_set`, `property_name`, `operator`, `expected_value`, `unit` | `rase.selection` |
| **E** Exception | Когда правило не применяется | Текст в `instructions` / notes | `rase.exception` |

Интерпретация нормы (юридический текст) живёт в `norm_source` + `norm_edition` + `norm_clause` + человекочитаемом R.  
Исполняемый критерий — только S + operator/value (+ A). Без S/operator правило **не** должно давать ERROR PASS.

## Статусы и fail-closed

| `status` | Использование | Positive verdict? |
|----------|---------------|-------------------|
| `synthetic` / `synthetic-template` / `draft` | Разработка, CI, демо | **Нет** |
| `approved` / `customer_approved` | Только с полным `approval` + `jurisdiction` + `pack_hash` | Да, в согласованном scope |
| `retired` | Архив | Нет |

`approval_ref` **никогда** не достаточен без объекта `approval`.  
`claim_labels` с `synthetic` / `fixture` / `template` / `not-customer-evidence` **запрещают** `customer_approved`.

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

Поле `rase` опционально в `norm-rule-pack.schema.json` (вместе с `severity`, `finding_class`, `test_example_ref`). Loader сохраняет исполняемые поля; RASE — документация критерия для экспертов и аудита.

## Связь с пилотом

1. Самолет утверждает содержимое → `customer_approved` + hash lock (RT-002).  
2. AeroBIM грузит pack через `AEROBIM_NORM_RULE_PACK`.  
3. Неполный / draft pack → capability fail-closed, не Shared-gate green по нормам.  
4. HITL может править правила только через versioned store + audit event (не silent overwrite).

## Вход от заказчика (перечень)

См. также [`../partners/SAMOLET_WHAT_WE_NEED_2026_07-ru.md`](../partners/SAMOLET_WHAT_WE_NEED_2026_07-ru.md):

1. Выписка EIR / критерии приёмки на пилот (1–2 стр + таблица свойств).  
2. Список СП/локальных стандартов **в scope** (не «все СП»).  
3. ≥20 типовых ошибок с примерами (калибровка).  
4. Подписант `approved_by` + даты действия.  
5. Область: дисциплины, стадии П/Р, исключения MEP/DWG.
