<!-- claims-lint: allow-file reason="IFC Acceptance Gate product freeze; TZ 90%/30min as undefined; competitors as non-claims; NO_GO" -->
---
title: "IFC Acceptance Gate — product freeze (16.08.2026)"
status: active
version: "1.1.0"
last_updated: "2026-08-16"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Product freeze. Not product accuracy. Not Tangl/10D integration.
  Not DWG-ready. Not MEP delivered. Checkpoint NO_GO until RT-001/002/003.
  ADR-001: passed follows PackageOutcome; never PASS_WITH_WARNINGS + passed=false.
---

# Продукт: IFC Acceptance Gate

**Срез:** 16 августа 2026. **Рынок: GO. Checkpoint: NO_GO.**  
Не заменяет: [`../gtm/SAMOLET_OSINT_VECTOR_KT2_2026_08_14.md`](../gtm/SAMOLET_OSINT_VECTOR_KT2_2026_08_14.md), [`PROTOCOL_QUALITY_ACCEPTANCE_TASK07_2026_08.md`](PROTOCOL_QUALITY_ACCEPTANCE_TASK07_2026_08.md), [`../pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md`](../pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md).

## Тезис

AeroBIM принимает IFC и машиночитаемые требования, проверяет комплект по согласованным правилам, связывает каждое замечание с объектом, требованием и доказательством и возвращает отчёт + BCF.

Не продаём: универсальный AI; замену эксперта; расчётную экспертизу; «все нормы»; native DWG; federated MEP clash; точность >90% без корпуса; CDE-ready.

Продаём: **preflight / acceptance gate для IFC-поставки** перед согласованием; проверяемый отчёт; меньше итераций «выгрузили → нашли → исправили»; журнал доказательств; слой поверх 10D/CDE/Tangl, не вместо них.

> 10D хранит и ведёт документацию. AeroBIM независимо проверяет пригодность пакета по заданному сценарию.

CLI продукта: `python -m aerobim.tools.run_demo_ifc_acceptance_gate` → `artifacts/ifc-acceptance-gate-demo/` (`report.html` / `acceptance-gate.json` / BCF). Overlay PDF — P1: `run_demo_vertical_slice`.

## Боли Самолёта (закрываем по очереди)

| Боль | Что делает AeroBIM | Сейчас |
|---|---|---|
| A. Модель открывается, но непригодна | Preflight + IDS: требование, GUID, атрибут, rule pack + hash, block/continue | Fixture GO |
| B. ПД/РД/расчёт расходятся | Cross-document **одного класса фактов** (площадь, кол-во, марка, ревизия). VLM — кандидат, не verdict | Fixture PARTIAL |
| C. Повторный preflight руками | Цикл: требование → IDS → IFC → evidence → finding → HTML/JSON/BCF → повтор | Fixture GO |
| D. Замечания без контекста | Finding = объект, не текст: GUID, правило, expected/observed, evidence, ревизия | Fixture GO |
| E. Нельзя честно сравнить решения | Протокол оценки, не «90%» | Предложен; customer BLOCKED |

## ТЗ: делать / ограничить / не обещать

| Требование ТЗ | Решение | Статус |
|---|---|---|
| BIM / атрибуты / IDS | IFC2x3/4/4x3 + IfcOpenShell + IfcTester + rule pack | Делать сейчас |
| Геометрия | Базовые проверки + controlled clash | Делать сейчас |
| 2D PDF | Текстовый слой, координаты, overlay | Ограниченный MVP (P1) |
| Сканы / OCR | Advisory/partial | Не ядро verdict |
| DWG | Fail-closed intake; DXF/derived | Не native DWG |
| MS Office | Текст/таблицы для ТЗ/спек | Поддержка, не ядро |
| ПД↔РД | Ревизия + выбранные факты | Ограниченно |
| Расчёты | Сверка + provenance | Не независимая экспертиза |
| MEP clash | IFC geometry, controlled | Не system-aware |
| NLP ТЗ | Deterministic + optional advisory | Fail-closed |
| Замечания / UI / HITL / BCF 2.1 | Шаблоны, review shell, ZIP | Делать сейчас |
| >90% / ≤30 мин | Только после customer pack + протокол | Не заявлять |

**MVP:** IFC + IDS/requirements + optional PDF/spec → preflight → selected cross-doc → evidence findings → review → BCF/HTML/JSON.

## Сценарий 1 (продаём): IFC Acceptance Gate

Вход: IFC; IDS или JSON rule pack; код проекта, дисциплина, стадия, ревизия; optional PDF/spec; профиль.

Проверки: файл открывается; схема допустима; spatial structure; GUID; обязательные entity/Pset; тип и единица; классификаторы; IDS; выбранные quantity; простые геометрические ограничения по профилю.

Выход: `acceptance-gate.json` — `outcome` + `passed` (**ADR-001**: `passed=true` только у `pass` / `pass_with_warnings`; не рисовать `PASS_WITH_WARNINGS` при `passed=false`) + capabilities (`ifc_schema`, `ids_validation`, `property_validation`, `geometry`, `dwg_native`, `mep_system_clash`) + findings (GUID, rule, expected/observed, evidence_refs) + manifest (engine, rule_pack_hash, input_hash, reproducibility_hash).

## Сценарий 2 (после Gate): один факт cross-document

Площадь / количество / марка / ревизия: IFC ↔ PDF/Excel/ТЗ, допуск, HARD_CONFLICT, evidence с обеих сторон. Не: «понимание» планировки, все двери/окна, свободный LLM по нормам, кто прав при противоречии.

## 10D / Tangl

Не просить глубокий sync в 10D на шаге 1. File/API boundary: СОД export → AeroBIM intake → evidence bundle + BCF/JSON/HTML → эксперт / 10D / BIM-tool.

Минимальный контракт: вход `project_id`, `package_id`, `document_id`, `revision`, `discipline`, `stage`, `source_uri`/`upload`, `rule_pack_id`, `required_capabilities`. Выход: `run_id`, `report_id`, `outcome`, counts, URIs, hashes.

Речь: «У Самолёта уже есть контур хранения и BIM-данных. AeroBIM не конкурирует за хранение и визуализацию. Мы добавляем независимый validation gate перед согласованием.»

## Open-source vs paid

Открыто: kernel, базовые adapters, report contract, IFC/IDS/BCF, fixtures. Коммерция: customer rule packs, нормативные библиотеки, адаптер 10D, on-prem/SLA/support, adjudication, private corpus, расширенные PDF/DWG connectors. Moat не MIT.

## Архитектура: не распыляться

Ядро: Requirement, Rule, EvidenceRef, Finding, CapabilityStatus, PackageOutcome, ReportManifest; Intake → ValidateIfcAcceptance → CompareSelectedFacts → EvidenceBundle → Export → Review.

Заморозить до customer proof: GraphRAG/IfcLLM, agentic verdict, сложный VLM, universal CAD, system-aware MEP, расчётный solver, новые foundation-порты вне demo path.

Правило: нет в 3-минутном демо и нет в KPI пилота — нет приоритета.

## KPI пилота (не «90%»)

Coverage (`executed_rules/required_rules`); critical recall; precision; evidence completeness; reproducibility; cycle time (cold/warm); review efficiency; BCF handoff quality. Отдельно IFC / PDF / OCR / cross-doc / geometry. n=20–30, ≥2 эксперта, holdout. До корпуса: «доказано на fixtures» / «готово к customer evaluation».

## Ask Самолёту

Не «данные для обучения». 1 IFC + IDS/требования + 1 PDF/спека + ревизия до/после + известные замечания + ручной итог + версия требований + нужный outcome + способ обработки + эксперт. Объём: 1 demo / 3–5 smoke / 20–30 оценка. Письмо: [`SAMOLET_KT2_ASK_2026_08_15.md`](SAMOLET_KT2_ASK_2026_08_15.md).

## Этапы / приоритеты / stop-list

0 (до КТ): один путь Gate; 3 мин; одно finding; evidence; BCF; повтор не обязателен на записи.  
1: manifest, versioned rule pack, report hash, BCF consumer, fail-closed production, Docker smoke.  
2: customer pack, baseline, adjudication, kill/scale.  
3: PDF cross-doc, OCR limited, CDE file API — только после 2.

P0: IFC ingest, IDS, evidence findings, deterministic report, capability honesty, BCF 2.1, HTML/JSON, HITL, on-prem, tenant isolation, protocol.  
P1: PDF/tables, quantity compare, overlay, BCF 3.0, API boundary.  
P2: MEP graph, CV/VLM, native DWG, GraphRAG, агенты.

**Stop:** новый AI-агент; новый KG; universal CAD; dashboard без finding; 90% на слайде; «весь ТЗ закрыт»; deep 10D до file/API; сотая fixture-метрика вместо customer pack.

## Речь

> AeroBIM — открытый, локально разворачиваемый acceptance gate для IFC-пакетов. Он встраивается в контур 10D, превращает требования в проверяемые правила, каждое нарушение связывает с доказательством и возвращает эксперту результат, пригодный для решения. Мы не заменяем эксперта и не выдаём непроверенную точность за факт.

## Kill-criteria / лицензии

Нет пакета/разметчиков; критический recall ниже согласованного; нет provenance; нет доверия эксперта; нет эффекта vs baseline. Core PDF = `pypdfium2` + `pdfminer.six`; PyMuPDF только `pdf-agpl`.
