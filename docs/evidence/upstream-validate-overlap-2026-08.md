<!-- claims-lint: allow-file reason="Written map of overlap vs MIT upstream; not a product accuracy claim" -->
---
title: "Overlap vs buildingSMART validate / ifc-gherkin-rules / IfcOpenShell ifcbench"
date: "2026-08-14"
claim_boundary: >-
  Written replacement map. We do not claim to run the official Validation Service
  or ifcbench geometry matrix. Not product accuracy. Not CIM compliance.
---

# Что дублирует upstream и что оставляем себе

Источники (проверены 14.08.2026):

- [buildingSMART IFC Validation Service](https://validate.buildingsmart.org/) — четыре слоя
- [buildingSMART/validate](https://github.com/buildingSMART/validate) (MIT) · [dev guide](https://buildingsmart.github.io/validate/dev/index.html)
- [buildingSMART/ifc-gherkin-rules](https://github.com/buildingSMART/ifc-gherkin-rules) (MIT) — слой 3 (Implementer Agreements / Informal Propositions)
- IfcOpenShell/ifcbench — регрессия геометрии по ядрам/флагам, метрики на элемент в SQLite

Демо 20.08 **собирается без** нового Gherkin-движка, EXPRESS-парсера и SQLite geometry matrix. Новый порт для этого не нужен.

## Четыре слоя bSI vs AeroBIM

| Слой bSI | Что делает official service | Что есть у нас | Решение к 20.08 |
| --- | --- | --- | --- |
| 1. STEP / ISO 10303-21 | Полный синтаксис SPF | `BasicIfcSchemaValidator`: заголовок `ISO-10303-21`, `FILE_SCHEMA`, дубли GUID. **Не** полный STEP-парсер | Оставить тонкий pre-gate. Полный синтаксис = bSI service (`HttpBsiValidationService`), не писать свой |
| 2. Схема IFC + EXPRESS | Formal propositions, EXPRESS-функции | Capability явно **NOT_VERIFIED**, кроме SPF identity | Не писать EXPRESS. Звать validate API, когда настроен |
| 3. Нормативные правила (Gherkin) | IA / IP через Behave + IfcOpenShell | Нет Gherkin-раннера | Не писать. Не заявлять «как Validation Service» |
| 4. Отраслевые практики / bSDD | Non-normative + bSDD | Offline `bsdd_term_mapper` (курируемый список), не live bSDD | Не расширять. Адаптер в списке на заморозку |
| IDS 1.0 | Не слой validate; у нас IfcTester | `IfcTesterIdsValidator` + **наш** fail-closed `ifcVersion` / SKIPPED | **Оставить.** Это 0.4; bSI case 0101 как раз разрешает тихий пропуск |
| Геометрия ifcbench | bbox / centroid / VEF / manifold / vertex hash | Fixture kernel timing (`export_ifc_release_matrix`), не per-element SQLite | Не писать ifcbench-клон к КТ#2. Регрессия геометрии = КТ#3, звать upstream |

## Почему «пишем своё» только здесь

1. **Fail-closed IDS.** Official IfcTester / case 0101 трактуют `ifcVersion` как метаданные. Без нашего гейта заявление fail-closed ложно. Это не дубль validate.
2. **Российский IDS-контур.** Официальные файлы МОГЭ ([moexp.ru ТИМ](https://www.moexp.ru/services/tekhnologii-informatsionnogo-modelirovaniya/)) гоняются через IfcTester. Gherkin bSI — про IA/IP схемы IFC, не про требования ГАУ МО.
3. **Вердикт пакета.** `PackageOutcome` + capability policy + Claims Lock — продуктовая политика Shared-gate, её нет в validate.
4. **Вертикальный срез PDF/штамп.** PyMuPDF/pdfium + ICMAP-приём. Это не IFC Validation Service.

## Что не писать (overengineering, трекер)

Не делать до 20.08: свой Gherkin, свой EXPRESS, свой ifcbench SQLite, второй IDS-движок, новый порт «как bSI». Адаптер `bsi_validation_service` уже есть — не развивать, пока нет URL/токена пилота.
