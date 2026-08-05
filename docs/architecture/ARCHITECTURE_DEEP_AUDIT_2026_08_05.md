---
title: "Task 0 — deep repository audit (full)"
date: 2026-08-05
head: "fa08f20"
claim_boundary: "Engineering inventory only. Checkpoint NO_GO. Not product accuracy."
ports_delta: "+0"
adapters_delta: "+0"
tokens_delta: "+0"
brief: "ARCHITECTURE_REVIEW_BRIEF_2026_08.md"
prior: "../quality/TASK0_DEEP_REPO_AUDIT_2026_08_05.md"
---

# Задача 0 — полный аудит репозитория (стоп)

**Посылка:** приложения заказчика могут не прийти. RT-001/002/003 кодом не закрываются.  
**Назначение:** основа задач 1–9 + материал к IT-ментору 11.08.  
**Правило шага:** не чинить продукт. Документы аудита только.

Живой inventory @ `fa08f20`:

| Метрика | Live |
|---|---:|
| Public domain Protocol | **46** |
| Private duck-type Protocol | 3 |
| Adapter modules | **71** |
| DI tokens | **59** |
| Modules / LOC `aerobim/` | **290 / 55 351** |

---

## 0.1 Карта архитектуры

### Слои

| Слой | Модули | LOC |
|---|---:|---:|
| `tools/` | 68 | 15 582 |
| `domain/` | 79 | 14 779 |
| `infrastructure/` | 79 | 14 060 |
| `application/` | 32 | 6 353 |
| `presentation/` | 16 | 2 380 |
| `core/` | 14 | 2 169 |
| `(root)` | 2 | 28 |
| **Итого** | **290** | **55 351** |

### Elimination candidates (1 impl + 1 typed consumer)

`SectionDiffAnalyzer`, `RemarkGenerator`, `DocumentSignatureAuditor`, `PackageInventoryLoader`, `ExternalEvidenceVerifier`, `BsiValidationService`, `StructuredLogger`, `NormRulePackVersionStore`, `IfcSpatialIndexProvider`, (+ weak) `DrawingAnalyzerPort`.

### DI вне analyze/report/export (11)

`ADVISORY_VLM_PIPELINE`, `AGENTIC_REVIEW_ORCHESTRATOR`, `APPLY_NORM_RULE_HITL_EVENT_USE_CASE`, `CAD_ENTITY_LOADER`, `COMPILE_REQUIREMENTS_TO_IDS_USE_CASE`, `DRAWING_ANALYZER_PORT`, `HYBRID_MODEL_ROUTER`, `IFC_MODEL_DIFF`, `NORM_RULE_PACK_VERSION_STORE`, `ODA_CAD_MODEL_INGESTOR`, `REQUIREMENT_INTERPRETER`.

### Нарушения зависимостей

| Sev | Где | Что |
|---|---|---|
| HARD | `application/services/analyze_orchestrators.py` | → `infrastructure.adapters.ifc_space_inventory` |
| HARD | `application/services/customer_intake.py` | → `aerobim.tools.validate_customer_intake_gate` |
| Soft | `presentation/http/*` | прямые exporters / OpenRebar / OIDC stubs |

Domain → Infrastructure: не найдено.

---

## 0.2 Capabilities vs заявления

SSOT: README Key Capabilities. Полная построчная карта — в prior Task0 agent pass; ниже **расхождения** и контур Task 2.

### Analyze без входов (факт)

| Вход | Поведение |
|---|---|
| нет `ifc_path` в body | HTTP **422** |
| файл IFC отсутствует | HTTP **404** |
| нет IDS | capability **SKIPPED** |
| IDS запрошен, валидатор мёртв | **FAILED** |
| нет расчётов | **SKIPPED** |
| нет requirements и IDS | HTTP **400** |
| только PDF | **не first-class** частичный прогон → вход Task 2 |

### Расхождения

| ID | Заявлено | Факт |
|---|---|---|
| M1 | Extraction integrity Available | Часто NOT_VERIFIED/SKIPPED |
| M2 | IFC/IDS evidence fixture | Также open corpus (BSI, buildingsmart) |
| M3 | BCF fixture (T1) | Contract/integration шире |
| M4 | OIDC NOT_IMPLEMENTED | Stubs 501/400 работают |
| M5 | Calc correctness Not implemented | `calculation_match` сверка **есть** (не путать) |

MEP NOT_VERIFIED + ENG_PARTIAL scaffold — **MATCH**. DWG native Missing — **MATCH**.

---

## 0.3 Тесты

| Метрика | Значение |
|---|---|
| ~test functions | **~1876** (baseline) |
| Domain/behavior (heur.) | ~70% |
| Schema/export | ~18% |
| DI/wiring | ~12% |
| Mock-primary | ~5 тестов |
| Модули без dedicated import | ~38 |

Fail-closed: `development` / `samolet_pilot` / `production` — сильные; `fixture` почти = soft twin development (разрыв).

---

## 0.4 Мёртвый / дубли

| Класс | n |
|---|---:|
| Orphans domain/app/adapters | **0** |
| CLI `python -m` «orphans» | 12 |
| Tools ни CI ни docs | ~22 |
| PDF/CAD multi-backend | intentional (лицензия), не мёртвые дубли |

---

## 0.5 Зависимость от данных заказчика

| Блокер | При отсутствии | Open substitute без ослабления? |
|---|---|---|
| RT-001 | `publishable=False`; intake blocks pilot | Да — open_bench / coverage; **нет** — flip % |
| RT-002 | SKIPPED / FAILED; draft ≠ approved | Да — draft advisory; **нет** — forge approved |
| RT-003 | NOT_VERIFIED; hard profile blocks pass | Да — ENG_FIXTURE + claim_boundary; **нет** — VERIFIED без memo |

---

## Связь с уже сделанным в окне

| Пункт промта | Статус на `fa08f20` |
|---|---|
| Task 3 полнота 25п.п. | **Частично:** 2/6 строк → ≈8,3% КР; AR/VK в Exp B закоммичены |
| Task 8 env CI gate | **Сделано** (`documented_env_vars` + маркеры EN/RU) |
| Exp B AR/VK | **В SSOT** `EXPERIMENT_B_…` (не только КР) |
| Task 2 partial package | **Не сделано** (главный пробел для Exp A) |

---

## Приоритет находок (не чинить здесь)

| P | ID | Находка | Дальше |
|---|---|---|---|
| P0 | A1 | PDF-only / no-IFC не first-class | **Задача 2** |
| P0 | A3 | 10 elim ports + 11 idle DI | **Задача 1** (ментор) → опц. удаление |
| P0 | A4 | RT fail-closed OK | Задачи 3–5 на open |
| P1 | A6 | `fixture` ≈ `development` | Task 2/8 негативы |
| P1 | A8 | 2 HARD layer imports | при касании файлов |

---

## Дельта этого шага

| | |
|---|---|
| Порты / адаптеры / токены | **+0 / +0 / +0** |
| Код продукта | **+0** |
| Docs | brief + этот полный аудит |

**ТРЕБУЕТСЯ ОТ ВЛАДЕЛЬЦА:** ничего для старта задачи 1 (подготовка к 11.08). Корпус по-прежнему желателен, но **не** в плане.

## СТОП

Дальше по промту — **задача 7** (weekly-report с воронкой) или **задача 1** (ментор-пакет) — по явному «дальше».
