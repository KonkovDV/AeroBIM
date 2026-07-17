---
title: "ТЗ Самолет × ТехЛаб 2026 — Задача 07 (редакция v2.0)"
status: active
version: "2.0.0"
last_updated: "2026-07-17"
language: ru
tags: [aerobim, tz, samolet, techlab, task-07]
claim_boundary: >
  Документ согласован с Claims Lock и CRITICAL_BLOCKERS.
  Checkpoint продукта NO_GO до RT-001/002/003. Не обещает >90%, MEP delivered,
  нативный DWG, корректность расчётов, CDE-ready BCF.
basis:
  - docs/tz/* (черновики TBD)
  - docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md
  - docs/architecture/RESEARCH_ALIGNMENT_AEC_AI_2025_2026_07.md
  - audit/reports/CLAIMS_LOCK_2026_07_17.md
---

# Техническое задание v2.0

**Конкурс:** Самолет × ТехЛаб 2026  
**Задача 07:** Система автоматизированной верификации проектной и рабочей документации  
**База реализации:** open-source AeroBIM ([KonkovDV/AeroBIM](https://github.com/KonkovDV/AeroBIM))  
**Дата редакции:** 2026-07-17  

**Маркировка изменений относительно v1:**  
`[НОВОЕ]` · `[УТОЧНЕНО]` · `[ПЕРЕФОРМУЛИРОВАНО: причина]`

---

# Часть 0. Аудит исходного ТЗ (Шаг 1)

| Раздел ТЗ v1 | Полнота | Проблемы | Что добавить в v2 |
|--------------|---------|----------|-------------------|
| Термины | Высокая | CV сформулирован как «как человек» без границ | Явные уровни L0–L4; CV/VLM = advisory |
| Актуальность | Высокая | — | Сохранить |
| Концепция | Высокая | Риск прочтения как «замена эксперта» | Жёсткий HITL + DeterminismGate |
| Целевые задачи | Средняя | «неэффективное пространство» без метрики; MEP без scope | Метрика только по согласованию; MEP = gap |
| Функциональность | Средняя | «DWG» без ODA/DXF; NLP без разделения regex/LLM | DXF/конвертация; LLM advisory |
| Источники данных | Высокая | — | NDA / gitignore customer |
| Критерии оценивания | Низкая | **«точность >90%» неизмерима** (нет корпуса, κ, протокола) — конфликт RT-001; SLA «на любой комплект» | Протокольные KPI (§9) |
| Приложения | Средняя | Типовые ошибки без customer_confirmed | Зависимости от заказчика (§11) |
| **Архитектура = TBD** | Пусто | Нет acceptance | §5 заполнен |
| **Код и сборка = TBD** | Пусто | Нет DoD | §6 заполнен |
| **Образ решения = TBD** | Пусто | — | §7 заполнен |
| **Презентация = TBD** | Пусто | Риск Claims Lock на слайдах | §8 заполнен |
| **Сопр. документация = TBD** | Пусто | — | §10 заполнен |

**Особые конфликты v1 ↔ Claims Lock:**

1. `[ПЕРЕФОРМУЛИРОВАНО: RT-001]` «точность >90%» → только после размеченного корпуса + κ/α + `PrecisionClaim.publishable`.  
2. `[ПЕРЕФОРМУЛИРОВАНО: honesty]` «анализ DWG» → DXF / конвертация / ODA с лицензией; нативный DWG = missing.  
3. `[ПЕРЕФОРМУЛИРОВАНО: OpenRebar]` «ошибки расчёта» → **сверка** результатов, не независимый solver.  
4. `[ПЕРЕФОРМУЛИРОВАНО: MEP-CLASH-001]` «пересечения инженерных систем» как system-aware → not verified до federated IFC + провайдера.

---

# Часть 1. ТЗ Задача 07 — редакция v2.0

## 1. Термины и определения `[УТОЧНЕНО]`

| Термин | Определение в рамках Задачи 07 | Граница честности |
|--------|--------------------------------|-------------------|
| **OCR** | Извлечение текста из растровых/сканированных чертежей и PDF | Baseline: RapidOCR/PyMuPDF; ≠ понимание чертежа |
| **Computer Vision (CV)** | Детекция регионов/символов на листе | Advisory; `cv_human_level=MISSING` до корпуса |
| **VLM** | Мультимодальная модель на **регионе** листа | Только после детектора регионов; не whole-sheet sign-off |
| **NLP** | Извлечение требований из ТЗ/норм; генерация текста замечаний | Sign-off: детерминированный regex/шаблоны; LLM — advisory + HITL |
| **BIM-модель** | IFC (геометрия + атрибуты), IFC2x3 / IFC4 / IFC4x3 | openBIM; не Revit-runtime |
| **IDS** | Information Delivery Specification 1.0 (buildingSMART) | Машиночитаемые требования к IFC |
| **BCF** | BIM Collaboration Format 2.1 (export); 3.0 experimental | Export ≠ доказанный CDE-import |
| **RASE** | Requirement / Applicability / Selection / Exception | Прозрачность нормы → замечание `[НОВОЕ]` |
| **DeterminismGate** | Шлюз: AI не может переписать `summary.passed` | Invariant AeroBIM `[НОВОЕ]` |
| **сверка расчёта** | Сопоставление ожидаемых/наблюдаемых величин | ≠ проверка корректности solver'ом |

**ТР-1.** Система позиционируется как **интеллектуальный ассистент эксперта**, не замена ГИП/эксперта.  
**Критерий приёмки:** в UI и отчёте явно указано «decision support / HITL»; Claims Lock не нарушен.

---

## 2. Актуальность `[УТОЧНЕНО]`

Ручная проверка ПД/РД трудозатратна, зависит от эксперта, подвержена пропускам коллизий и кросс-документных противоречий. Нужен **открытый** контур acceptance-criteria (ISO 19650 Shared-gate: evidence для Shared, не контрактный Published) с измеримыми KPI и честными границами возможностей.

---

## 3. Концепция решения `[УТОЧНЕНО]`

Программный модуль (MVP+) на базе AeroBIM:

1. Принимает пакет: IFC + IDS/нормы + ТЗ + расчёты + 2D (PDF/растр/структурированный; DXF — по фазе).  
2. Выполняет **детерминированную** валидацию (IFC/IDS/cross-doc/clash/OCR baseline).  
3. Формирует замечания с provenance (файл, GUID/зона, норма).  
4. Показывает результат в браузерном review (IFC + 2D overlay + панель).  
5. Экспортирует HTML/JSON/BCF 2.1.  
6. **AI (LLM/VLM)** — только advisory; при расхождении с движком — `DivergenceRecord`, вердикт движка сохраняется.

**ТР-2.** Только контур `DETERMINISTIC_VALIDATION` выставляет `summary.passed`.  
**Критерий:** архитектура-тест / Red Team: AI-путь не пишет `passed=true` в обход DeterminismGate.

---

## 4. Целевые задачи `[УТОЧНЕНО]`

### 4.1 Анализ графики

| ID | Требование | Фаза | Статус AeroBIM |
|----|------------|------|----------------|
| **ТР-3** | Извлечение атрибутов/геометрии BIM (IFC) | MVP | done |
| **ТР-4** | Текст/аннотации с векторных/структурированных 2D | MVP | partial |
| **ТР-5** | OCR сканов PDF/растр | MVP | partial |
| **ТР-6** | DXF (ezdxf) / DWG через конвертацию или ODA | P2 | missing / not_verified |
| **ТР-7** `[НОВОЕ]` | Детектор регионов → OCR/VLM на регионе (Blueprint arXiv:2602.13345; heuristic сейчас, YOLO — опция) | P2/I8a | partial |
| **ТР-7a** `[НОВОЕ]` | HITL unmatched/low-confidence регионов (`hitl_required`, event `drawing_region_escalated`) | I8c | done/partial |

**Критерий ТР-7/7a:** `drawing_regions` + HITL flags; `cv_human_level=MISSING` (AECV-Bench arXiv:2601.04819: OCR силён, подсчёт символов слаб).

### 4.2 Анализ соответствия

| ID | Требование | Фаза | Статус |
|----|------------|------|--------|
| **ТР-8** | Соответствие IDS / properties IFC | MVP | done |
| **ТР-9** | Соответствие ТЗ (извлечение требований) | MVP | done (детерминированное) |
| **ТР-10** | PD↔RD section pairing | P1 | partial (scaffold) |
| **ТР-11** | Norm packs (утверждённый заказчиком) | P1 | partial (synthetic); **RT-002** |
| **ТР-12** | Сверка расчётных величин (load/quantity match) | MVP | partial |
| **ТР-13** `[ПЕРЕФОРМУЛИРОВАНО: не solver]` | Независимая корректность расчёта | — | **not implemented** (вне MVP) |

### 4.3 Выявление ошибок

| ID | Требование | Фаза | Статус |
|----|------------|------|--------|
| **ТР-14** | Геометрические коллизии BIM (IfcClash) | MVP | partial (optional extra) |
| **ТР-15** `[УТОЧНЕНО]` | MEP system-aware clash | P1+ | **not_verified** (MEP-CLASH-001, RT-003) |
| **ТР-16** | Некорректные площади / количества | MVP | partial |
| **ТР-17** `[УТОЧНЕНО]` | Неэффективное использование пространства | P4 | missing — **только если KPI согласован с заказчиком** |
| **ТР-18** | Несогласованность разделов / отсутствующие элементы | MVP/P1 | partial |
| **ТР-19** | Расхождения размеров чертёж↔IFC | MVP | done/partial |

### 4.4 Поддержка эксперта

| ID | Требование | Фаза | Статус |
|----|------------|------|--------|
| **ТР-20** | Подсветка `problem_zone` / регионов | MVP | done |
| **ТР-21** | Генерация замечаний RU/EN (шаблоны) | MVP/P0 | done |
| **ТР-22** | Редактирование замечаний (HITL) | P0 | done |
| **ТР-23** | Приоритизация Critical/Warning/Info | MVP | done |
| **ТР-24** `[НОВОЕ]` | Provenance: finding_id, source_id, evidence_refs, norm_clause, RASE | MVP/I8b | partial/done |

---

## 5. Требования к архитектуре решения `[НОВОЕ]`  
*(закрывает TBD; SSOT: `TZ_ARCHITECTURE_REQUIREMENTS_2026.md`, `TARGET_HYBRID_*`)*

### 5.1 Слои (Clean Architecture)

**ТР-25.** Обязательные слои: `presentation` → `application` → `domain` ← `infrastructure`; `core` (DI, settings, path jail).  
**Критерий:** Domain не импортирует Infrastructure; Application не импортирует Infrastructure; только constructor injection через `container.resolve(TOKEN)`.

**ТР-26. Atomic Delivery.** Новый domain port = Protocol + adapter + DI token + wiring + тест в одном PR.  
**Критерий:** architecture / port-parity проверки зелёные.

### 5.2 Четыре контура `[НОВОЕ]`

| Контур | Назначение | Влияет на `summary.passed`? |
|--------|------------|----------------------------|
| INGESTION | Загрузка, CAD/Office/OCR ingest | Нет (подготовка) |
| DETERMINISTIC_VALIDATION | IFC/IDS/cross-doc/clash/match | **Да** |
| AI_ADVISORY | LLM/VLM/агент/GraphRAG query | **Нет** (DeterminismGate) |
| EVIDENCE_REPORTING | Отчёт, BCF, HITL events | Нет (фиксация) |

**ТР-27.** DeterminismGate: при противоречии advisory vs engine — `DivergenceRecord`, engine wins.  
**Критерий:** тест на divergence; advisory не флипает pass.

### 5.3 Пайплайн валидации (7 стадий)

**ТР-28.** Порядок:

1. Schema/SPF pre-gate  
2. IDS document audit  
3. IFC + IDS validation  
4. Cross-doc / section / norms  
5. Clash / spatial (capability-gated)  
6. Drawings / OCR / region detector  
7. Remarks + report + BCF  

**Критерий:** при `require_clash` / обязательном OCR skipped→FAILED → `passed=false`.

### 5.4 Capability honesty `[НОВОЕ]`

**ТР-29.** Каждый опциональный модуль отдаёт `ok | skipped | failed | missing | not_verified | not_implemented`.  
**ТР-30.** Endpoint `GET /v1/system/capabilities` отражает honesty-поля (dwg_dxf, cv_human_level, mep_system_clash, calculation_correctness).  
**Критерий:** forbidden OK states не появляются в runtime (`enforce_honesty_capabilities`).

### 5.5 Research-aligned advisory ports `[НОВОЕ]`

| Порт | Research | Фаза | Статус |
|------|----------|------|--------|
| `DrawingRegionDetector` + `MultimodalDrawingPipeline` | Blueprint §D.1 | P2/I8a | partial |
| RASE на findings / IDS draft | ACC §D.2 | I8b | partial |
| `RequirementToIdsCompiler` + HITL promote | ACC §D.2 | P1/P3 | partial |
| Semantic alignment + HITL escalate regions | §D.4 / I8c | P2 | partial/missing |
| `IfcKnowledgeGraphPort` (NL→graph query) | IfcLLM §D.3 | I9 | **advisory scaffold** (port+DI+fixture QA; GraphRAG not shipped) |
| `MepSystemGraphProvider` | — | P1+ | not_verified |

**ТР-31.** LLM/VLM/GraphRAG — **только advisory + HITL**; запрещены как единственный источник sign-off.  
**Критерий:** зафиксировано в Claims Lock и архитектуре.

### 5.6 Безопасность и персистентность

**ТР-32.** Fail-closed auth (Bearer/OIDC вне dev), tenant/object ACL, path jail, лимит IFC (256 MiB).  
**ТР-33.** FS по умолчанию; S3/Postgres/Redis — enterprise extras.  
**Критерий:** негативные тесты jail/auth; SETTINGS env-matrix.

### 5.7 Non-goals архитектуры `[НОВОЕ]`

Не является: полноценным CDE; Revit-runtime; автономной сертификацией; обучением ML в sign-off-пути; «полным покрытием всех СП/ГОСТ».

---

## 6. Требования к коду и сборке `[НОВОЕ]`  
*(SSOT: `TZ_BUILD_AND_QUALITY_2026.md`)*

**ТР-34.** Backend: Python **3.12+**; Frontend: Node **20+**, Vite.  
**ТР-35.** Качество PR: `ruff format --check`, `ruff check`, `mypy src`, `pytest`.  
**ТР-36.** Extraction gate: `evaluate_extraction --min-macro-f1 0.70` (fixture corpus).  
**ТР-37.** Detection harness: `evaluate_detection_precision` с порогами пилота (≥0.6 interim); publishable — только с agreement.  
**ТР-38.** Frontend: vitest; не заявлять «всегда в CI», если не wired.  
**ТР-39.** Docker-compose + OpenAPI (`docs/openapi.json`) + semver / RELEASE_POLICY.  
**ТР-40.** Воспроизводимость: frozen tags, REPRODUCIBILITY-2026, CITATION.cff.  
**ТР-41.** SECURITY.md процесс; лицензии зависимостей совместимы с MIT.  
**ТР-42.** Anti-stub: фейковый I/O только с `@sota-stub` + запись в KNOWN_BUGS.

**Критерий DoD:** локальный quality gate зелёный; матрица соответствия обновлена при user-visible изменении.

---

## 7. Образ финального решения `[НОВОЕ]`  
*(SSOT: `TZ_SOLUTION_IMAGE_AND_PRESENTATION_2026.md`)*

### 7.1 End-to-end сценарий (конкурсный MVP+)

1. **Загрузка** пакета: IFC, PDF/растр, DOCX (Docling optional), DXF (фаза); DWG — через согласованную конвертацию `[УТОЧНЕНО]`.  
2. **Автоанализ** на **согласованном** эталонном пакете: цель ≤30 мин (`measure_package_sla`).  
3. **Review:** IFC-viewer + 2D overlay + панель (фильтр / приоритет / редактор).  
4. **Severity triage:** Critical / Warning / Info.  
5. **Provenance:** deep-link файл / лист|регион / пункт нормы / evidence_refs `[НОВОЕ]`.  
6. **Экспорт:** HTML, JSON, BCF 2.1 ZIP.  
7. **Передача** проектировщику; эксперт несёт ответственность (HITL).

**ТР-43.** Demo-path воспроизводим по `docs/ops/demo-path-runbook-2026.md` (или актуальному ops runbook).  
**Критерий:** сценарий 8–12 мин без нарушения Claims Lock.

### 7.2 Что считается «готовым» для жюри vs roadmap

| Готово (можно показать) | Roadmap (сказать явно) |
|-------------------------|------------------------|
| IFC+IDS+cross-doc | Полный корпус СП/ГОСТ |
| Clash optional | MEP system-aware |
| OCR baseline + region priors | YOLO/VLM product CV |
| RU/EN templates + HITL edit | LLM remarks без HITL |
| SLA на согласованном пакете | Универсальный SLA |
| Protocol TP≥60% | Published >90% |

---

## 8. Требования к презентации `[НОВОЕ]`

**ТР-44.** Структура слайдов: проблема → концепция ассистента → архитектура (4 контура) → живое демо → метрики с границами → roadmap MVP–P4 → запрос к заказчику (корпус/нормы).  
**ТР-45.** Ни один слайд не нарушает Claims Lock (§12).  
**ТР-46.** Один язык на колоду (RU **или** EN).  
**ТР-47.** Каждая цифра метрики ссылается на `docs/evidence/` или команду воспроизведения.  
**Критерий:** чек-лист презентации пройден заказчиком/командой до защиты.

---

## 9. Критерии оценивания `[ПЕРЕФОРМУЛИРОВАНО: измеримость + RT-001]`

### 9.1 Точность обнаружения ошибок

| Уровень | Метрика | Порог | Условие |
|---------|---------|-------|---------|
| Пилот interim | TP/(TP+FP) на adjudicated findings | ≥ **0.60** | Dual-human labels |
| Publishable product | Precision / Recall / F1 | Целевая **>0.90** | Только после P4 + корпус заказчика |
| Согласованность разметки | Cohen’s κ (2 эксперта) | Инструментальный gate κ≥0.60; **целевой протокол κ>0.80** `[УТОЧНЕНО: research vs tooling]` | `measure_adjudicator_agreement` |
| При ≥3 разметчиках | Krippendorff’s α | α≥0.67 (tooling) | schema 1.1.0 |
| Ранжирование | nDCG (graded 0/1/2) | Согласовать на пилоте | Fixture-only до корпуса `[НОВОЕ]` |

**ТР-48.** Запрещено публиковать «точность >90%» без `PrecisionClaim.publishable=true` (customer + ≥2 adjudicators + agreement).  
**Критерий:** intake gate + evaluate_detection_precision --require-publishable.

### 9.2 SLA

**ТР-49.** ≤30 минут — на **согласованном эталонном пакете** (`measure_package_sla --corpus-kind customer|fixture`), не «на любом проекте».  
**Критерий:** отчёт SLA с claim_level.

### 9.3 Качество замечаний RU/EN

**ТР-50.** Kill-критерий: доля замечаний, принятых экспертом без правки или с минимальной правкой (лог HITL `edited_remark`).  
**Критерий:** шаблон adjudication + weekly rollup.

### 9.4 Прочие KPI `[НОВОЕ]`

- Покрытие каталога типовых ошибок: ≥20 паттернов; `customer_confirmed` — после заказчика.  
- FP-rate по дисциплинам.  
- Время до первой подтверждённой находки.  
- Снижение часов ручной проверки vs **baseline недели 1** пилота (данные заказчика).  
- Стабильность: CI pytest зелёный; capability honesty без silent OK.

### 9.5 Коллизии / несоответствия

**ТР-51.** Оценка коллизий и несоответствий — **тем же протоколом разметки**, не отдельной «магической» цифрой >90% без корпуса.

---

## 10. Требования к сопроводительной документации `[НОВОЕ]`  
*(SSOT: `TZ_ACCOMPANYING_DOCS_2026.md`)*

**ТР-52.** Обязательный пакет:

| Документ | Назначение |
|----------|------------|
| README RU/EN | Установка, extras, границы claims |
| docker-compose + ops runbook | Развёртывание |
| OpenAPI | Контракт API |
| Руководство эксперта (review-shell) | HITL сценарий |
| `TZ_COMPLIANCE_MATRIX_2026.md` | Трассируемость |
| Настоящее ТЗ v2.0 | Конкурсный SSOT |
| KPI + annotation protocol | Измерение |
| REPRODUCIBILITY-2026 | FAIR/CODE |
| SECURITY.md | Уязвимости |
| KNOWN_BUGS + capabilities honesty | Ограничения |
| Claims Lock / CRITICAL_BLOCKERS | NO_GO регистр |

**Критерий:** все пути существуют в репо или явно помечены customer-local/gitignored.

---

## 11. Фазность и границы MVP `[НОВОЕ]`

| Фаза | Содержание | Конкурс / пилот |
|------|------------|-----------------|
| **MVP** | IFC/IDS/cross-doc/clash opt/OCR baseline/template remarks/review/BCF export | **Конкурсный минимум** |
| **P0** | Upload, панель замечаний, EN | done |
| **P1** | Norm packs, section pairing, precision harness | scaffolds done; корпус — нет |
| **P2** | DXF/DWG thin, OCR deepen, region detector/CV advisory | I8a partial |
| **P3** | LLM remarks/IDS assist + HITL | stub/advisory |
| **P4** | Customer corpus → publishable precision; space-efficiency — optional | blocked RT-001 |

**ТР-53.** В конкурсном MVP **не входят** как done: нативный DWG, MEP system-aware, publishable >90%, CDE-import proof, полный СП/ГОСТ.

---

## 12. Политика заявлений (Claims Lock) `[НОВОЕ]`

До появления evidence **запрещено** утверждать:

- точность >90% / product accuracy %;  
- утверждённый заказчиком нормативный пакет (если его нет);  
- MEP clash как delivered;  
- «анализирует DWG/DXF» как полноценный CAD;  
- «проверяет корректность расчётов»;  
- production-ready / external academic audit;  
- BCF готов к CDE (без import evidence);  
- fixture SLA = customer комплект ≤30 мин;  
- green pass при silent skip обязательных capability.

**ТР-54.** Публичные тексты сверяются с `audit/reports/CLAIMS_LOCK_2026_07_17.md`.

---

## 13. Матрица зависимостей от заказчика `[НОВОЕ]`  
*(SSOT: `SAMOLET_TZ_REMAINING_TAILS_2026_07.md`)*

| # | Поставка заказчика | Разблокирует |
|---|-------------------|--------------|
| 1 | Согласованный комплект ПД/РД+IFC+ТЗ+расчёты+2D (NDA) | SLA, precision |
| 2 | Approved norm pack + `approval_ref` | RT-002 / vs norms |
| 3 | ≥20 typical errors `customer_confirmed` | Каталог KPI |
| 4 | ≥2 разметчика + labeled corpus | RT-001 / >90% path |
| 5 | Baseline часов ручной проверки | −% review time |
| 6 | CDE для BCF import week-1 | CDE claim |
| 7 | Signed scope memo (CV/ГОСТ/MEP границы) | Scope |

Без п.1–4 checkpoint остаётся **NO_GO**.

---

## 14. Протокол оценки качества `[НОВОЕ]`

**ТР-55.** Двойная слепая разметка → adjudication CSV → `labels.json` → `measure_adjudicator_agreement` → `evaluate_detection_precision --require-publishable --agreement-json`.  
**ТР-56.** Intake: `validate_customer_intake_gate` (evidence `{path,sha256}`).  
**Критерий:** runbook `docs/ops/intake-precision-runbook-2026.md`.

---

## 15. AI-безопасность и снижение галлюцинаций `[НОВОЕ]`  
*(Research §D.6)*

**ТР-57.** Severity triage обязателен.  
**ТР-58.** Provenance / deep-link на каждый AI/engine finding.  
**ТР-59.** HITL обязателен для advisory accept.  
**ТР-60.** DeterminismGate + DivergenceRecord.  
**ТР-61.** CoVe (перепроверка по нормам) — roadmap advisory, не sign-off.  
**ТР-62.** Региональный VLM-конвейер (не whole-sheet) — требование к P2/P3.

---

## 16. Риски и митигации `[НОВОЕ]`

| Риск | Митигация |
|------|-----------|
| Плохие сканы | OCR degrade; confidence; HITL |
| DWG / ODA лицензия | DXF first; ODA optional; honesty MISSING |
| Нет корпуса заказчика | NO_GO; harness ≠ product |
| LLM галлюцинации | DeterminismGate; advisory-only |
| MEP scope | Explicit gap; federated IFC + provider |
| Переобещание KPI | Claims Lock + intake gate |

---

## 17. Источники данных и ограничения `[УТОЧНЕНО]`

2D, BIM (IFC), ТЗ RU/EN, внутренние стандарты (norm packs).  
Ограничения: качество сканов, неструктурированность, малый labeled corpus, разные стили оформления, **NDA — customer файлы вне публичного git**.

---

## 18. Приложения `[УТОЧНЕНО]`

Примеры ПД/РД, стандартов, ТЗ, типовых ошибок, расчётов — в `samples/tz-appendix/` и/или customer NDA path.  
Каталог ≥20 синтетических паттернов в репо; подтверждение заказчиком = 0 до поставки.

---

## 19. Матрица трассируемости ТЗ v2.0 → AeroBIM `[НОВОЕ]`

| ТР | Модуль / порт | Статус | Фаза | Критерий приёмки | Источник |
|----|---------------|--------|------|------------------|----------|
| ТР-1 | Claim boundary, UI | done | MVP | Нет «замена эксперта» | Claims Lock |
| ТР-2 | DeterminismGate, contours | done | MVP | AI ≠ passed | TARGET § |
| ТР-3 | IfcOpenShell / IDS | done | MVP | Capabilities ok/failed | Matrix §3.1 |
| ТР-4–5 | DrawingAnalyzer / Raster | partial | MVP/P2 | Annotations / OCR | Matrix |
| ТР-6 | CadModelIngestor | missing/NV | P2 | Honesty dwg_dxf | TARGET G1 |
| ТР-7 | DrawingRegionDetector | partial | I8a | Regions + MISSING cv | Blueprint 2602.13345 |
| ТР-7a | drawing_region_hitl | partial | I8c | hitl_required + events | Research §4 |
| ТР-8–9 | IdsValidator, extractors | done | MVP | Report issues | Matrix |
| ТР-10 | SectionDiffAnalyzer | partial | P1 | Pairing capability | Track A1 |
| ТР-11 | NormRulePackLoader | partial | P1 | approval_ref | RT-002 |
| ТР-12 | LoadEvidenceVerifier | partial | MVP | LOAD-OK/match | I2 |
| ТР-13 | — | missing | — | Не в MVP | Claims Lock |
| ТР-14 | IfcClashDetector | partial | MVP | require_clash policy | Matrix |
| ТР-15 | MepSystemGraphProvider | not_verified | P1+ | RT-003 | MEP gap |
| ТР-16 | QuantityConsistency | partial | MVP | SI compare | I2 |
| ТР-17 | — | missing | P4 | KPI memo | Audit |
| ТР-18–19 | Cross-doc / drawing↔IFC | partial/done | MVP | ConflictKind | Matrix |
| ТР-20–23 | ProblemZone, remarks, UI | done | MVP/P0 | HITL events | P0 |
| ТР-24 | provenance + RASE | partial | I8b | rase_elements | Research §2 |
| ТР-25–26 | layers, DI, Atomic | done | MVP | Arch tests | TZ_ARCH |
| ТР-27 | DeterminismGate | done | MVP | DivergenceRecord | TARGET |
| ТР-28 | Analyze pipeline | done | MVP | 7 stages | TZ_ARCH |
| ТР-29–30 | ReportCapabilities API | done | MVP | /v1/system/capabilities | I6 |
| ТР-31 | AI advisory policy | done | MVP | Claims Lock | Research |
| ТР-32–33 | auth, jail, storage | done | MVP | Security tests | TZ_ARCH |
| ТР-34–42 | CI / quality | done | MVP | ruff/mypy/pytest | TZ_BUILD |
| ТР-43–47 | Demo / slides | partial | MVP | Runbook | TZ_SOLUTION |
| ТР-48–51 | KPI protocol | partial | P1/P4 | Intake + κ | Research §5 |
| ТР-52 | Docs pack | done | MVP | docs/tz index | TZ_ACCOMP |
| ТР-53 | Phase boundaries | done | — | This §11 | Waves |
| ТР-54 | Claims Lock | done | — | Audit report | CLAIMS_LOCK |
| ТР-55–56 | Eval protocol | done tooling | P1 | Runbook | I6 |
| ТР-57–62 | AI safety | partial | MVP–P3 | Gate+HITL | Research §6 |
| — | IfcKnowledgeGraphPort | **advisory scaffold** | I9 | Not GraphRAG/IfcLLM product | Research §3 · Claims Lock |

---

## 20. Заключение

Редакция **v2.0** делает TBD-разделы проверяемыми, привязывает требования к AeroBIM и research 2025–2026, и устраняет неизмеримые обещания v1. Продуктовый checkpoint остаётся **NO_GO** до RT-001/002/003; конкурсный MVP демонстрируется на детерминированном openBIM-контуре с честной таблицей gaps.

**Согласовано с:** `CLAIMS_LOCK_2026_07_17.md`, `CRITICAL_BLOCKERS.md`, `RESEARCH_ALIGNMENT_AEC_AI_2025_2026_07.md`, `EXECUTION_PLAN_HYPERDEEP_2026_07.md`.
