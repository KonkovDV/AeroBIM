---
title: "Task 0 — deep repository audit (no-customer-data scenario)"
date: 2026-08-05
head: "95822a6"
claim_boundary: "Engineering inventory only. Checkpoint NO_GO. Not product accuracy."
ports_delta: "0 (audit only)"
adapters_delta: "0"
tokens_delta: "0"
loc_delta: "+0/-0 (report file only if committed later)"
---

# Задача 0 — глубокий аудит репозитория

**Посылка:** приложения заказчика могут не прийти. Три блокера (RT-001/002/003) кодом не закрываются.  
**Метод:** живой подсчёт LOC + три параллельных read-only аудита (архитектура / capabilities / tests+dead+RT).  
**Правило шага:** не чинить. Этот документ — опора для задач 1–7.

Живой inventory vs README.ru «48 / 67 / 58»:

| Метрика | README claim | Live @ `95822a6` |
|---|---:|---:|
| Public domain `Protocol` ports | 48 | **46** (−2; +3 private duck-types = 49 class hits) |
| Adapter modules (`infrastructure/adapters/*.py` excl. `__init__`) | 67 | **71** (+4) |
| DI tokens (`Tokens` attrs) | 58 | **58** |

---

## 0.1 Карта фактической архитектуры

### Слои `backend/src/aerobim/`

| Слой | Модули `.py` | LOC | Назначение |
|---|---:|---:|---|
| `tools/` | 68 | 15 581 | CLI / eval (вне Clean Architecture cake) |
| `domain/` | 79 | 14 779 | модели, Protocol ports, honesty |
| `infrastructure/` | 79 | 14 060 | adapters 71 + di/auth/security |
| `application/` | 32 | 6 353 | use cases + services |
| `presentation/` | 16 | 2 380 | FastAPI HTTP |
| `core/` | 14 | 2 169 | config / DI tokens / security |
| `(root)` | 2 | 28 | `main.py` |
| **Итого** | **290** | **55 350** | = runtime-baseline src LOC |

### Protocol-порты — сводка

| Корзина | n |
|---|---:|
| Public domain Protocol | 46 |
| Private duck-types (`_GuidLookup`, `_HitlEventLike`, `_ReportLike`) | 3 |
| Application Protocol (`IdsAssistDraftPort`) | 1 |
| Кандидаты на устранение (1 адаптер + 1 typed consumer) | **10** |
| Порты с 0 адаптеров | 1 (`GuidLookup`) |
| Порты / токены без typed consumer на analyze-пути | см. DI ниже |

**Elimination candidates (1+1):**  
`SectionDiffAnalyzer`, `RemarkGenerator`, `DocumentSignatureAuditor`, `PackageInventoryLoader`, `ExternalEvidenceVerifier`, `BsiValidationService`, `StructuredLogger`, `NormRulePackVersionStore`, `IfcSpatialIndexProvider`, (+ weak) `DrawingAnalyzerPort`.

**Alias / orphan TZ ports (DI есть, analyze не использует):**  
`RequirementInterpreterPort`, `CadEntityLoaderPort`, `DrawingAnalyzerPort`, `NormRetrieverPort`≈`NormCorpusRetriever`, `IfcModelDiff`.

### DI-токены вне рабочего пути analyze/report/export (11)

`ADVISORY_VLM_PIPELINE`, `AGENTIC_REVIEW_ORCHESTRATOR`, `APPLY_NORM_RULE_HITL_EVENT_USE_CASE`, `CAD_ENTITY_LOADER`, `COMPILE_REQUIREMENTS_TO_IDS_USE_CASE`, `DRAWING_ANALYZER_PORT`, `HYBRID_MODEL_ROUTER`, `IFC_MODEL_DIFF`, `NORM_RULE_PACK_VERSION_STORE`, `ODA_CAD_MODEL_INGESTOR`, `REQUIREMENT_INTERPRETER`.

### Нарушения направления зависимостей

| Severity | Где | Что |
|---|---|---|
| **HARD** | `application/services/analyze_orchestrators.py` | import `infrastructure.adapters.ifc_space_inventory` |
| **HARD** | `application/services/customer_intake.py` | import `aerobim.tools.validate_customer_intake_gate` |
| Soft | `presentation/http/*` | прямые импорты exporters / OpenRebar / OIDC stubs |

Domain → Infrastructure: **не найдено**.

---

## 0.2 Инвентаризация возможностей vs заявления

SSOT таблицы: README Key Capabilities (39 строк). Полная построчная карта — в рабочем аудите агента; ниже — **расхождения** и критичный контур для задачи 1.

### Поведение analyze при отсутствии входов (факт)

| Вход отсутствует | Факт |
|---|---|
| `ifc_path` нет в body | HTTP **422** |
| `ifc_path` есть, файла нет | HTTP **404** (`FileNotFoundError`) |
| `ids_path` нет | Capability **SKIPPED** (honest) |
| `ids_path` запрошен, валидатор мёртв | Capability **FAILED** (fail-closed) |
| расчёты нет | **SKIPPED** |
| нет requirements **и** нет IDS | HTTP **400** |
| только PDF (без IFC в схеме) | **не проходит** до «частичного прогона» как first-class — схема требует IFC |

**Следствие для задачи 1:** сейчас комплект «только PDF» либо не принимается (422), либо не читается как честный частичный прогон с `summary.outcome ≠ pass`. Это главный инженерный пробел окна «данных не будет».

### Расхождения (оба направления)

| ID | Заявлено | Факт | Направление |
|---|---|---|---|
| M1 | Extraction integrity `Available` | Часто `NOT_VERIFIED`/`SKIPPED` без PDF/producer | overclaim статуса |
| M2 | IFC/IDS evidence `fixture` | Также open corpus (BSI n=290, buildingsmart IFC, IFC-Bench) | underclaim evidence |
| M3 | BCF ZIP `fixture (T1)` | Contract/evidence ladder = integration | underclaim |
| M4 | OIDC BFF `NOT_IMPLEMENTED` | Phase-2 stubs отвечают 501/400 | soft — stubs ≠ product |
| M5 | Calc *correctness* `Not implemented` | `calculation_match` сверка **есть** | не путать с correctness |
| — | MEP `NOT_VERIFIED` | ENG_PARTIAL scaffold работает, `geometry_verified=False` | **MATCH** (честно) |
| — | DWG native Missing | Fail-closed; DXF/PDF derived отдельно | **MATCH** |

Остальные строки Available@fixture / Optional / Blocked — **MATCH** при чтении preface README.

---

## 0.3 Тесты

| Метрика | Значение |
|---|---|
| Test files / functions | ~236 / **~1872** |
| Domain/behavior (heur.) | ~70% |
| Serialization/schema/export | ~18% |
| DI/wiring/profile | ~12% |
| Mock-primary assertions | **5** тестов (низкий mock-theatre) |
| Модули без dedicated import | **~38** |

### Fail-closed по профилям

| Профиль | Качество негативных тестов | Разрыв |
|---|---|---|
| `development` | хорошее | — |
| `fixture` | слабо как **отдельный** профиль (= soft twin development) | parity matrix отсутствует |
| `samolet_pilot` | сильное | — |
| `production` | сильное | intake gate в основном завязан на pilot |

Высокоценные unit-дыры: `package_ingestion` (norm fail-closed), `postgres_audit_store`, `cross_document_contradictions`, pymupdf producer.

---

## 0.4 Мёртвый и дублирующий код

| Класс | n | Комментарий |
|---|---:|---|
| True orphans domain/app/adapters | **0** | после нормализации импортов |
| «Orphans» = CLI `python -m` | 12 | не мёртвые |
| Tools ни в CI, ни в docs | **22** | discoverability; часть с unit-тестами |
| Дубли адаптеров PDF/CAD/MEP | intentional multi-backend | не удалять как «дубли» без решения лицензии/контура |

---

## 0.5 Пути, зависящие от данных заказчика

| Блокер | Где | При отсутствии сегодня | Open/synthetic без ослабления честности? |
|---|---|---|---|
| **RT-001** corpus | `PrecisionClaim`, `evaluate_detection_precision`, intake keys | `publishable=False`; pilot intake blocked | **Да** — fixture/open_bench; **нет** — flip intake / product % |
| **RT-002** норм-пак | `load_norm_packs`, eligibility APPROVED, HITL version store | нет path → SKIPPED; broken → FAILED; draft ≠ customer_approved | **Да** — draft/template advisory; **нет** — forge `customer_approved` |
| **RT-003** federated MEP | Unconfigured providers, `mep_intake`, hard `require_mep` | NOT_VERIFIED; блокирует pass на hard | **Да** — ENG_FIXTURE + claim_boundary; **нет** — VERIFIED без memo |

**SSOT intake:** `validate_customer_intake_gate.INTAKE_GATE_KEYS` связывает все три под `samolet_pilot`.

---

## Находки по приоритету (не чинить на шаге 0)

| P | ID | Находка | Связь с планом |
|---|---|---|---|
| P0 | A1 | Частичный прогон без IFC **не first-class**; риск прочитать SKIPPED как «всё чисто» | **Задача 1** |
| P0 | A2 | README inventory **48/67/58** устарел (46/71/58) | Задача 7 / hygiene |
| P0 | A3 | 11 DI-токенов вне analyze-пути + 10 elimination ports — абсурдный рост без сдвига блокеров | Бюджет сложности; удаление > абстракция |
| P0 | A4 | RT-001/002/003 fail-closed корректны; substitutes есть | Задачи 2–3 на open/synthetic |
| P1 | A5 | Extraction integrity status soft-overclaim | README honesty (не код) |
| P1 | A6 | `fixture` profile почти не отделён от `development` | Задача 1/7 негативы |
| P1 | A7 | 22 tools без CI/docs | Гигиена; не раздувать порты |
| P1 | A8 | 2 HARD layer violations (app→infra, app→tools) | Ремонт при касании файлов |
| P2 | A9 | OIDC stubs vs NOT_IMPLEMENTED | формулировка README |
| P2 | A10 | Exp B 25 п.п. «полнота» | **Частично закрыто Task 3** (`681b651`): ≈8,3 п.п. подтверждены; ≈17 п.п. остались условно |

---

## Дельта этого шага

| | |
|---|---|
| Порты / адаптеры / токены | **+0 / +0 / +0** |
| Строки кода продукта | **+0** (аудит only; файл отчёта при коммите — docs) |
| Что закрывает | База решений для задач 1–7 без ожидания корпуса |
| ТРЕБУЕТСЯ ОТ ВЛАДЕЛЬЦА | Ничего для продолжения задачи 1. Корпус по-прежнему желателен, но **не** в плане. |

---

## СТОП

Дальше по промту — **задача 1** (честный частичный прогон) только после явного «дальше» / «задача 1».
