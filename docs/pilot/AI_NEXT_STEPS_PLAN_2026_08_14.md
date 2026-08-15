<!-- claims-lint: allow-file reason="Engineering plan after Wave A; forbidden phrases cited as non-claims per Claims Lock" -->
---
title: "План работ — следующие шаги без корпуса «Самолёта»"
date: "2026-08-14"
status: active
claim_boundary: >
  Plan only. Checkpoint NO_GO. RT-001/002/003 stay OPEN. Ports/DI freeze lifted
  14.08 evening by operator. Not customer accuracy. Not MEP delivered. Not CDE-ready.
---

# План работ (после 14.08)

Операторский план. **Wave A приземлена в `005b7bc`.** Следующий SSOT:
[`AI_KT2_EXECUTOR_REPORT_2026_08_14.md`](AI_KT2_EXECUTOR_REPORT_2026_08_14.md) —
**верификация + демо + baseline**, не новый фичевый слой.

Funding Red Team 15.08: [`../quality/RED_TEAM_FUNDING_ATTACKS_KT2_2026_08_15.md`](../quality/RED_TEAM_FUNDING_ATTACKS_KT2_2026_08_15.md).  
Academic Red Team 15.08 (Messick/Kane/ISO 19650/Solihin): [`../quality/RED_TEAM_ACADEMIC_KT2_2026_08_15.md`](../quality/RED_TEAM_ACADEMIC_KT2_2026_08_15.md).  
HEAD × Task 07 × MIK audit: [`../quality/AUDIT_HEAD_005B7BC_SAMOLET_TECHLAB_MIK_2026_08_15.md`](../quality/AUDIT_HEAD_005B7BC_SAMOLET_TECHLAB_MIK_2026_08_15.md).  
Питч ведёт с NO_GO; ask = слот/комплект, не раунд. Не копировать local 2259 в README.  
Репетиция 20.08: [`../demo/KT2_DEMO_REHEARSAL_2026_08_12.md`](../demo/KT2_DEMO_REHEARSAL_2026_08_12.md) — live CLI, не wall-guid HTML.

## 0. Жёсткие правила (нарушение = стоп)

1. **Ports/DI freeze снят оператором 14.08.** Новые порты — только atomic (port+adapter+token+wiring). Предпочитать extra-method на существующем адаптере, если протокол не требует нового контракта.
2. `closes_rt001/002/003` всегда `false`. Не трогать `test_rt_customer_blocker_honesty_lock.py`.
3. Не вендорить LibreDWG (GPL-3). Не скрейпить закрытые API ЕГРЗ. Не копировать чужие клиентские BCF (G55/Solibri).
4. Один заказчик программы Техлаб — Самолёт. А101/Галс запрещены как замена корпуса.
5. Каждая новая фикстура → `python -m aerobim.tools.export_samples_manifest --merge-missing` + `pytest tests/test_samples_manifest_gate.py -q`.
6. После правок: `ruff`, focused pytest, `scripts/lint_claims.py --matrix-guard`, `--full-docs`, `export_runtime_baseline --check-readme`. LOC-дрейф > ±50 → обновить `docs/evidence/runtime-baseline-latest.json` + README-сниппет (не выдумывать `tests_passed`).
7. Коммит — только по явной команде пользователя.

## Статус волны A (14.08 вечер, freeze снят)

| # | Результат | Честность |
|---|-----------|-----------|
| A1 | Вендорены `EngineeringSurveysTask-01-00.xsd` и `GeologicalReport-01-00.xsd`; intake fail-closed | Схемы этапа строительства **не** найдены в каталоге 14.08 — файлы не выдуманы. `closes_rt001=false` |
| A2 | `XmlIdsDocumentAuditor` на 3 официальных IDS → `docs/evidence/ids-audit-2026-08.*` (0 document issues) | Не binary IDS-Audit-tool. `customer_pack_hash=null`. RT-002 OPEN |
| A3 | Пропущен | Нужен человеческий аккаунт validate.buildingsmart.org |
| A4 | `detect_clearance_between` + gap pair ~30 мм | HVAC fixture без геометрии — не использовался. `mep_system_clash=NOT_VERIFIED` |
| A5 | Planted clash → `export_bcf` → `consume_bcf_zip` | `cde_import=NOT_VERIFIED`. RT-003 OPEN |
| A6 | `samples/rule-packs/sp63-cover-template.json` | Template 20 мм, не таблица 8.1, не solver. `calculation_correctness=NOT_IMPLEMENTED` |

Новые порты/DI **не** добавлялись. Checkpoint **NO_GO**.

## Волна A — код/фикстуры сейчас

### A1. Вендорить новые XML-схемы Минстроя (07.08.2026)

- **Факт:** 07.08.2026 Минстрой опубликовал XML-схемы этапа строительства (протокол инструментального обследования, протокол отбора проб, уведомления ГСН); в силу с **05.11.2026**. Заключение экспертизы XML — переход до **03.01.2027**; задание на изыскания — с **03.10.2026**. Источник: minstroyrf.gov.ru/tim/xml-skhemy, cntd.ru/news 07.08.2026.
- **Шаги:** скачать схемы с minstroyrf.gov.ru → `samples/xsd/minstroy/` (+ `SOURCE.md` с URL и датой); пустые/битые fixtures по образцу `samples/xsd/minstroy/fixtures/`; расширить `egrz_intake_xml_checks.py` распознаванием новых корневых элементов (без новых портов); тесты по образцу `test_egrz_intake_xml_checks.py`.
- **Приёмка:** новые схемы валидируют fixture XML; `closes_rt001=false` сохранён; манифест обновлён.
- **Не утверждать:** «поддержка экспертизы», «машиночитаемые замечания заказчика». Это intake-формат, не корпус замечаний.

### A2. IDS-Audit на вендоренные IDS (МОГЭ / АГР / СПб ЦГЭ)

- **Факт:** официальный open-source `buildingSMART/IDS-Audit-tool` проверяет сам .ids (кардинальность, entity по версии IFC, официальные pset). Веб-обёртка: xbim.it/ids.
- **Шаги:** прогнать аудит (dotnet-инструмент локально или xbim веб вручную) на `samples/ids/moexp/`, `moscow-agr/`, `spbexp/`; зафиксировать отчёт в `docs/evidence/ids-audit-2026-08.md` + JSON-пин с хешами файлов.
- **Приёмка:** отчёт приложен; расхождения либо исправлены в IDS, либо задокументированы как known-gap.
- **Не утверждать:** «IDS одобрены заказчиком». `customer_pack_hash` остаётся null.

### A3. buildingSMART IFC Validation Service на samples/ifc

- **Факт:** бесплатный сервис (validate.buildingsmart.org), 4 слоя (STEP syntax, schema, normative rules, industry practices), лимит 256 МБ, нужен аккаунт. IFC2X3/IFC4/IFC4X3_ADD2.
- **Шаги:** человек создаёт аккаунт и загружает 3–5 ключевых фикстур (`clash-federated-box-*.ifc`, `wall-fire-rating-rei60.ifc`, `mep/hvac-sprinkler-systems.ifc`); ИИ фиксирует PDF/JSON-отчёты в `docs/evidence/bsi-validation-2026-08/` с хешами файлов.
- **Приёмка:** внешнее независимое подтверждение conformity наших фикстур запинено.
- **Не утверждать:** сертификация продукта; это валидация файлов, не софта.

### A4. Clearance-clash (soft) на HVAC-фикстуре через IfcOpenShell tree

- **Факт:** ifcopenshell 0.8.5 `geometry tree` имеет `clash_clearance_many(group_a, group_b, clearance, check_all)`; IfcClash 0.8.5 (13.04.2026) поддерживает режимы intersection/collision/clearance, селекторы, группировку, экспорт BCF-XML/JSON.
- **Шаги:** в существующем MEP-контуре (без новых портов) добавить engine-level прогон clearance по парам систем из `clearance-matrix-template.json` на `samples/mep/hvac-sprinkler-systems.ifc`; тест по образцу `test_p2_perf_2d_mep.py`; evidence JSON с хешами и счётчиками.
- **Приёмка:** строка 14 матрицы ТЗ остаётся VERIFIED_FIXTURE_ONLY с расширенным fn14 (clearance engine-level); `mep_system_clash` остаётся **NOT_VERIFIED**; default DI = Unconfigured.
- **Не утверждать:** MEP delivered, системный clash как продукт, RT-003 closed.

### A5. IfcClash → BCF round-trip на planted паре

- **Факт:** IfcClash экспортирует результаты в BCF-XML. У нас есть `consume_bcf_zip_path` (file ingest) и XSD-верификатор.
- **Шаги:** прогнать planted `clash-federated-box-a/b` → BCF из IfcClash → ingest нашим consumer → сверка GUID/заголовков; тест рядом с `test_bcf_export_and_clash.py`; evidence в `docs/evidence/`.
- **Приёмка:** round-trip зелёный; `cde_import=NOT_VERIFIED` не тронут.
- **Не утверждать:** CDE import, RT-008 T2.

### A6. СП 63 детерминированные нормо-правила (не solver)

- **Факт:** открытого решателя СП 63.13330 нет (аналоги: IS 456 lib, Genkai EN 1992 pre-alpha). Честный максимум — правила вида «минимальный процент армирования / защитный слой» как norm rules.
- **Шаги:** 3–5 правил из СП 63.13330.2018 (мин. армирование плит, защитный слой) в существующий `NormRulePackLoader`-формат как synthetic template; тесты fail-closed; явный `claim_boundary` «не проверка расчёта».
- **Приёмка:** `calculation_correctness` остаётся **NOT_IMPLEMENTED**; сверка остаётся сверкой.
- **Не утверждать:** независимая проверка расчётов, «проверено по СП».

## Волна B — к КТ#3 (человек + лицензия / живой CDE)

| # | Что | Ключ | Примечание |
|---|-----|------|-----------|
| B1 | ODA Drawings SDK trial: регистрация (человек), spike в private lane, решение по лицензии | ODA: 60 дней trial; Commercial $3000/год; SaaS = Sustaining $7500 | Адаптер `OdaCadModelIngestor` уже существует как честный scaffold; native DWG остаётся MISSING до лицензии |
| B2 | BCF T2 CDE import по `BCF_T2_IMPORT_RUNBOOK_2026.md` | openCDE Foundation API (discovery `/foundation/versions`, OAuth2) → BCF API 3.0 topics CRUD; trial-аккаунт openCDE-совместимой CDE | Нужен живой CDE + скриншоты + хеши; до этого `cde_import=NOT_VERIFIED` |

## Волна C — только с заказчиком (не трогать)

RT-001 (корпус ПД/РД + замечания + 2 адъюдикатора), RT-002 (подписанный пакет приёмки), RT-003 (федеративный IFC заказчика + signed scope + геометрический clash). Видео 19.08 и КТ#2 20.08 — человек.

## Команды верификации после каждого шага

```bash
cd backend
python -m ruff check src tests
python -m pytest tests/<focused> -q
python -m aerobim.tools.export_samples_manifest --merge-missing
python ../scripts/lint_claims.py --matrix-guard
python ../scripts/lint_claims.py --full-docs
python -m aerobim.tools.export_runtime_baseline --check-readme
```

## Источники (проверено 14.08.2026)

- ODA pricing/trial: opendesign.com/pricing, /products/drawings (trial 60 дней)
- IfcClash 0.8.5: pypi.org/project/ifcclash (clearance, selectors, BCF export)
- IfcOpenShell tree: docs.ifcopenshell.org/ifcopenshell-python/geometry_tree.html (`clash_clearance_many`)
- openCDE/BCF API 3.0: github.com/buildingSMART/BCF-API (release_3_0), foundation-API v1.1
- IFC Validation Service: validate.buildingsmart.org (бесплатно, аккаунт, 256 МБ)
- IDS-Audit-tool: github.com/buildingSMART/IDS-Audit-tool; веб: xbim.it/ids
- Минстрой XML: minstroyrf.gov.ru/tim/xml-skhemy; cntd.ru/news 07.08.2026 (схемы этапа строительства, в силе 05.11.2026); pro-expertiza.com (заключение экспертизы XML — переход до 03.01.2027)
- Расчёты: github.com/Pravin-surawase/structural_engineering_lib (IS 456), pypi.org/project/genkai (EN 1992, pre-alpha) — СП 63 открытого нет
