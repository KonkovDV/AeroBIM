---
title: "AeroBIM Academic Audit And Recommendations"
status: active
version: "0.5.0"
last_updated: "2026-04-12"
tags: [aerobim, audit, explanation, evidence]
---

# AeroBIM: Академический rebaseline-аудит и рекомендации

## 1. Метод и границы исследования

Этот аудит основан не на прежних narrative claims, а на повторной проверке текущего repository snapshot.

Исследованы:

- активные docs поверхности `README.md`, `docs/**`, `ops/**`;
- backend composition root, HTTP API, domain contracts, use cases и ключевые adapters;
- тестовые и fixture surfaces под `backend/tests/` и `samples/**`;
- внешний standards baseline: buildingSMART IDS, buildingSMART BCF, W3C SHACL, IfcOpenShell.

Цель аудита: определить, чем `AeroBIM` является уже сейчас, где реальные границы системы, какие architectural bets оказались верными, и какой следующий tranche даст наибольший product value без разрушения текущих контрактов.

## 2. Краткий вердикт

`AeroBIM` больше не является docs-first концептом. На апрель 2026 это уже **рабочее детерминированное ядро BIM QA**, состоящее из:

- Python backend с явной Clean Architecture;
- live IFC + IDS validation path;
- report persistence и export surfaces (`json`, `html`, `bcf`);
- multimodal project-package flow с narrative, structured drawing и PDF/OCR baseline;
- initial browser spatial review shell для отчётов, provenance и IFC-guided selection.

При этом `AeroBIM` пока **не является полноценной review platform**. В нём ещё нет:

- 2D problem-zone overlay surface;
- richer clash-pair and multi-selection review ergonomics;
- benchmark-grade performance rail;
- project/tenant-aware operating model;
- thin Revit roundtrip runtime.

Правильное позиционирование на текущей фазе: **deterministic multimodal BIM validation kernel with minimal review shell**, а не full-stack BIM coordination suite.

## 3. Архитектурная оценка

### 3.1. Что сделано правильно

#### A. Clean Architecture здесь не декоративна, а рабочая

Пятислойная схема `core -> domain -> application -> infrastructure -> presentation` подтверждается кодом, а не только документацией. Domain ports и typed models действительно изолируют IfcOpenShell, IfcTester, PyMuPDF, RapidOCR, filesystem persistence и export logic.

Практическое следствие: более сильные adapters можно добавлять без переписывания application semantics. Это особенно важно для будущего перехода от deterministic PDF/OCR baseline к heavier VLM path.

#### B. Product truth задан через typed intermediate contracts

Это главная сильная сторона проекта.

Вместо того чтобы превращать OCR, IDS, narrative parsing или exports в хаотичные side channels, система опирается на typed contracts:

- `ParsedRequirement`
- `DrawingAnnotation`
- `ValidationIssue`
- `ValidationReport`

Такой подход академически более устойчив, чем LLM-first или viewer-first designs. Он задаёт строгую промежуточную семантику и удерживает provenance в продуктовой модели.

#### C. Правильный standards stack

Выбранный стек подтверждается официальными источниками:

- IDS у buildingSMART остаётся machine-readable exchange-contract surface;
- BCF остаётся стандартным issue-transport слоем для IFC-centric coordination;
- SHACL остаётся корректным semantic-overlay кандидатом, но не заменой IFC/IDS на MVP-фазе;
- IfcOpenShell остаётся canonical OSS IFC toolkit and geometry engine.

Это означает, что архитектурное ядро не упирается в vendor-specific gravity и не строится на слабом стандарте.

#### D. Review shell появился вовремя и в правильной роли

Frontend не захватывает domain truth. Он работает как inspection surface поверх persisted reports. Это зрелое решение: сначала стабилизируется report/provenance model, затем на неё навешивается review UX.

## 4. Что уже подтверждено как рабочее

| Область | Статус | Комментарий |
|---|---|---|
| IFC property / quantity validation | ✅ | Live backend capability |
| IDS validation | ✅ | Live adapter + sample-backed path |
| Narrative rule synthesis | ✅ baseline | Deterministic, provenance-preserving |
| Structured drawing validation | ✅ | Active through drawing contracts |
| PDF / OCR drawing extraction | ✅ baseline | Live via PyMuPDF + RapidOCR |
| Clash detection | ✅ with optional extra | Real path exists, but depends on `.[clash]` |
| Report persistence | ✅ | Filesystem-backed live default |
| JSON / HTML / BCF export | ✅ | Live endpoints and tests |
| Browser review shell | ✅ initial spatial runtime | Report shell plus browser IFC viewer with GUID-driven selection |
| Thin Revit client | ❌ | Boundary only |

## 5. Подтверждённые ограничения и product gaps

### 5.1. Spatial review gap

Первый 3D rail уже появился: findings теперь можно связывать с IFC element GUID прямо в browser viewer. Но spatial review всё ещё неполный, потому что пока нет 2D problem-zone overlays и richer review interactions для нескольких элементов или clash pairs.

### 5.2. Optional-capability transparency gap

`.[vision]` уже встроен в common development lane, но `.[clash]` и `.[docling]` остаются явными opt-in extras. Это нормально как техническое решение, но плохо, если не видно на уровне operator documentation и capability framing.

Именно поэтому в этом tranche пришлось синхронизировать docs: система уже умеет больше, чем раньше, но и capability gating нужно описывать честнее.

### 5.3. Benchmark and scale gap

На текущей фазе у проекта есть fixture-backed correctness confidence, но ещё нет полноценного benchmark rail для:

- large IFC models;
- long-running multimodal jobs;
- throughput and latency baselines;
- repeated export and persistence pressure.

Без этого нельзя делать серьёзные performance claims.

### 5.4. Operating-model gap

Persisted report path уже есть, но пока почти нет product-level operational model для:

- project scoping;
- report grouping;
- discipline segmentation;
- async job lifecycle;
- tenant isolation.

Это уже не архитектурный, а product-operations gap.

## 6. Что показал rebaseline как инженерное качество

Во время повторной проверки был найден и сразу закрыт один реальный infrastructure defect: `IfcClashDetector` создавал временную директорию на каждый запуск без cleanup. Это был типичный production bug класса resource leak. Исправление узкое, проверяемое и показательное:

- реальный bug был найден из репозитория, а не из абстрактной теории;
- bug исправлен без ломки API;
- добавлен regression test.

Это хороший индикатор зрелости repo: сейчас там уже есть смысл не только обсуждать roadmap, но и запускать systematic hardening tranches.

## 7. Приоритетные рекомендации

### R1. Сделать review shell spatially actionable

Следующий главный tranche должен быть не про «ещё один parser», а про **пространственную навигацию по findings**.

Минимальный sound path:

1. 2D problem-zone overlay для drawing evidence;
2. richer issue and clash navigation поверх уже добавленного `web-ifc + Three.js` rail;
3. one-report smoke path, который проверяет полный UI flow поверх persisted report;
4. integration coverage for the new report-scoped IFC source surface.

Причина: backend kernel уже достаточно зрелый, чтобы bottleneck сместился из validation в review ergonomics.

### R2. Довести optional adapters до operational clarity

Нужно не столько срочно добавлять новые adapters, сколько сделать уже существующие capability boundaries прозрачными:

- `.[clash]` и `.[docling]` должны быть явно видны в active docs и ops surfaces;
- для optional runtime paths нужны integration tests и smoke variants, а не только interface-level existence.

### R3. Усилить multimodal evidence path, а не заменять его магией

Путь с heavier VLM имеет смысл, но только **поверх текущего typed contract**, а не вместо него. Правильная эволюция:

- сохранить `DrawingAnnotation` и `ProblemZone` как product truth;
- добавлять более сильный extraction engine за существующим port;
- не переносить доверие в opaque model output.

### R4. Перейти от report storage к operating model

После spatial review следующая осмысленная ступень — сделать отчёты operationally useful:

- project metadata;
- queryable indices;
- async long-running jobs;
- benchmark pack и regression rail.

### R5. Не торопиться с тяжёлой platformization

Сейчас нет оснований тащить в `AeroBIM` event sourcing, knowledge graph runtime, agentic orchestration или fat plugin architecture. На этой фазе они размоют фокус и увеличат surface area быстрее, чем реальную полезность.

## 8. Академическое заключение

С инженерной точки зрения `AeroBIM` уже прошёл самую сложную раннюю фазу: он не развалился в хаотичный набор adapters и не ушёл в viewer-first или LLM-first имитацию продукта. У него уже есть корректный standards baseline, typed domain contracts, реальный persistence/export path и начальный spatial review shell.

Значит, дальнейшая работа должна строиться не вокруг «ещё одной общей архитектурной идеи», а вокруг последовательного перехода:

**kernel -> spatial review -> operational scale -> authoring roundtrip**.

Именно такой порядок даёт наибольшую product leverage при минимальном риске сломать текущую архитектурную дисциплину.