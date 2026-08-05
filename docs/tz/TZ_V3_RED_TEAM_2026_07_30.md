---
title: "Red Team-аудит и ТЗ v3 — Самолёт ТехЛаб 2026, задача 07"
status: draft-for-jury-defense
version: "3.0.0-rc1"
date: "2026-07-30"
repo_snapshot: "main @ 98c67011871189c92ca0efa12079ea950c5a3ba5 (2026-07-29)"
claim_boundary: "Checkpoint NO_GO до закрытия RT-001/002/003 customer evidence. Fixture ≠ product."
---

# RED TEAM-АУДИТ И ТЗ v3 «САМОЛЁТ ТЕХЛАБ 2026, ЗАДАЧА 07»

> Принцип документа: реализованным считается только то, что доказано тестом,
> runtime-артефактом или воспроизводимым benchmark-паком. Всё остальное —
> `partial` / `experimental` / `planned` / `missing` / `not verified` / `needs customer`.

---

## 1. EXECUTIVE SUMMARY

**Вердикт чекпоинта: `NO_GO`** — не из-за инженерии, а из-за трёх открытых
customer-блокеров (RT-001 корпус точности, RT-002 утверждённый нормопак,
RT-003 federated MEP scope). Инженерная готовность высокая и растёт:
1536 тестовых функций (baseline JSON, commit `bea10ce`), 41 760 LOC src /
31 323 LOC tests backend, 29 vitest frontend, все quality-гейты PASS.

Что изменилось к 29.07 и реально доказано кодом/тестами:

1. **P2 deterministic 2D geometry core** (`domain/geometry.py`, 245 строк) —
   честный детерминированный слой измерений поверх уже извлечённых примитивов.
   Статусы OK/INCOMPLETE/UNIT_UNKNOWN/INVALID; bowtie → INVALID; коллинеарный/
   near-zero контур → INCOMPLETE; NaN/inf в `segments_intersect` → громкий
   `ValueError`, а не тихое `False`. **Это НЕ DWG/DXF-парсер** и его нельзя
   так подавать.
2. **Coverage** — live read-only endpoint `GET /v1/reports/{id}/coverage`
   (`coverage_from_report` + `derive_report_scope`), verdict-neutral,
   ACL-scoped, `CHECKED_OK` только при processing evidence; off-sheet finding
   блокирует `CHECKED_OK` листа. Coverage — доказательство покрытия проверки,
   не корректности документации, и **не персистится в отчёт**.
3. **Revision diff** (`domain/revision_diff.py`) — delimiter-proof ключ через
   `json.dumps`, verdict-neutral, `no_longer_reported` ≠ «исправлено».
4. **Drawing quality / region assessment** — `region_quality.py` +
   `region_classifier.py` + `drawing_region_assessment.py`: NaN/inf-сигналы
   нормализуются, отсутствие сигналов → REVIEW_REQUIRED, BAD/UNKNOWN ≠ OK.

Главные Red Team-находки этого прохода (детали в §4):

- **[F-01, MEDIUM]** Claims Lock (2026-07-17/19) отстаёт от кода: coverage,
  revision diff, geometry core в нём вообще не упомянуты — ни как разрешённые,
  ни как ограниченные формулировки. Риск неконтролируемого claims drift.
  (Утверждение исходного промта, что Claims Lock называет coverage «не wired»,
  **не подтвердилось**: слово «coverage» в CLAIMS_LOCK отсутствует.)
- **[F-02, HIGH]** Fixture-SLA-артефакт формально честный
  (`claim_level=fixture_only`), но измерен на паке **1096 байт** за 0.0096 мин —
  любая попытка показать его жюри как «≤30 минут» мгновенно уничтожается
  вопросом о размере пака.
- **[F-03, MEDIUM]** В `CONTOUR_PORTS` 11 имён без Protocol-объявления в
  `ports.py` (частично объявлены в других модулях, частично reserved) —
  архитектурный документ обгоняет код; требуется классификация
  declared→customer-proven (см. атаку A7).
- **[F-04, ОТОЗВАНО после верификации]** Не подтвердилось: `ports.py`
  содержит 29 Protocol, но README «20 domain ports» описывает **wired
  live-набор** («all wired in a single composition root»), что согласуется
  с «~19 live-ports» в TZ-доках — не занижение. `stub_ifc_knowledge_graph.py`
  **существует** (`infrastructure/adapters/`, tracked STUB-IFC-KG-001) —
  KNOWN_BUGS корректен. Находка отозвана: была основана на ошибке одного
  поискового прогона.

Три честных конкурентных преимущества: (1) детерминированный fail-closed
вердикт с ADR-001 и доказуемой verdict-neutrality всего AI-контура;
(2) evidence-инфраструктура (claims lock, публикационные гейты κ/α,
BCF-лестница T0–T4, coverage/provenance) — ни один из четырёх конкурентов
публично такого не показывает; (3) открытый openBIM-стек (IFC 2x3/4/4x3 + IDS
1.0 + BCF 2.1/3.0) без vendor lock-in.

Три честные слабости: (1) нет native DWG и human-level CV — peer-класс
«DWG/CV-first» атакует именно здесь; (2) нет ни одной customer-метрики —
peer-класс «field-pilot traction» давит трекшном; (3) MEP system-aware clash
не поставлен (RT-003). Имена участников задачи №7 в публичном репо не
публикуем (Claims Lock / kitchen → `.local`).

---

## 2. СРЕЗ АКТУАЛЬНОГО РЕПОЗИТОРИЯ (main @ `98c6701`, 29.07.2026)

### 2.1. Числа (SSOT: `docs/evidence/runtime-baseline-latest.json`, commit `bea10ce`)

| Метрика | Значение | Комментарий |
|---|---|---|
| Backend test functions | **1536** | tests_collected=1536 |
| Backend src LOC | 41 760 | |
| Backend test LOC | 31 323 | |
| Frontend vitest | 29 passed | CI job `frontend` |
| extraction macro_f1 | 0.86 | **fixture corpus; НЕ product accuracy** |
| Гейты ruff/mypy/pytest/vitest | PASS | build=UNKNOWN |

### 2.2. Архитектура (проверено по коду)

- Слои: `core → domain → application → infrastructure → presentation`;
  правила зависимостей соблюдаются (domain не импортирует infrastructure).
- Порты: **29 Protocol в `domain/ports.py`** + реэкспорт `MepSystemGraphProvider`
  из `domain/mep.py`; отдельные порты в `domain/tz_architecture_ports.py`
  (`SystemClashPort`) и `application/services/ids_assist_boundary.py`
  (`IdsAssistDraftPort`).
- `CONTOUR_PORTS` (`domain/architecture.py` L139–183): 4 контура,
  35 имён (INGESTION 10, DETERMINISTIC_VALIDATION 11, AI_ADVISORY 9,
  EVIDENCE_REPORTING 5).
- Вердикт: `SignOffCapabilityPolicy` (`application/services/capability_policy.py`,
  SSOT) — 12 pass-blocking capability-полей; `summary_passed()` = 0 ошибок И нет
  FAILED И нет required-not-OK И calculation_match/quantity ≠ NOT_VERIFIED.
  Профили samolet_pilot/production жёсткие: ослабляющие overrides игнорируются
  (RT D03). Физический writer — EvidenceAssembler (ADR-001).
- `PackageOutcome` (`domain/package_outcome.py`): PASS / PASS_WITH_WARNINGS /
  REVIEW_REQUIRED / BLOCKED / FAILED; `summary_passed_from_outcome` — единый
  источник.
- HTTP-поверхность: 25 маршрутов, 21/21 `/v1/*` под bearer + public `/health`;
  `GET /v1/auth/bff` → **501** (POST-05 OIDC BFF: DESIGNED / NOT_IMPLEMENTED).
- HITL: review-events append-only; сервер — SSOT для `previous_state`;
  actor из principal; **не могут менять `summary.passed`**.
- Hybrid AI foundation: `domain/hybrid/*` (5 уровней PUBLIC<INTERNAL<
  CONFIDENTIAL<RESTRICTED<SECRET, unknown→CONFIDENTIAL) + `HybridRouteGate`;
  зарегистрирован в DI, но **сознательно не потребляется** verdict use case
  (OFF==ON); дефолтный роутер local-only; отсутствующий конфиг → RuntimeError.
- Security: `outbound_url.py` (SSRF, DNS-pin), `zip_limits.py` (ZipBomb/traversal
  inspect на upload), `path_jail.py`, `xml_limits.py`, ACL cross-tenant → 404,
  OIDC-валидатор fail-closed, hashed locks `--require-hashes`, SHA-pinned Actions.

### 2.3. Статусы возможностей (классификация по принципу доказанности)

| Возможность | Статус | Evidence class | Модуль | Для customer sign-off? |
|---|---|---|---|---|
| IFC property/quantity (2x3/4/4x3) | available | fixture+tests | `IfcOpenShellValidator` | да (Shared-gate) |
| IDS 1.0 | available | fixture+tests | `IfcTesterIdsValidator` | да |
| Cross-doc contradiction + severity policy | available | fixture+tests | `ConflictKind` | да |
| Drawing ↔ IFC cross-validation | available | fixture | drawing adapters | да, с OCR-оговорками |
| ISO 12006-3 ε-band tolerance | available | fixture | quantity algebra | да |
| Narrative → requirements (regex) | available | fixture, F1-gate ≥0.70 | `StructuredRequirementExtractor` | да, как assist |
| HTML/JSON export | available | tests | exports.py | да |
| BCF 2.1 ZIP | available (T1) | artifact 2026-07-25 + XSD | bcf builder | да, structural only |
| BCF 3.0 ZIP | experimental (T1) | тот же артефакт | `?version=3` | ограниченно |
| BCF API push | foundation | experimental | `UnconfiguredBcfApiClient` default | нет |
| CDE import (T2) | **NOT_VERIFIED** | `cde-import-proof/STATUS.json`, present_files=[] | — | нет |
| Browser IFC viewer + 2D overlay | available | fixture + vitest | frontend | да, для review |
| HITL review-events/KPI | available | tests | reports.py | да |
| Object ACL (404) | available | tests | context.py | да |
| SSRF guard | available | tests | `outbound_url.py` | да |
| OpenRebar provenance digest | available (сверка) | fixture | `OpenRebarEvidenceVerifier` | сверка, НЕ корректность |
| Coverage endpoint | available | 16+ tests | `check_coverage.py` | evidence, не вердикт |
| Revision diff | available | tests | `revision_diff.py` | evidence, не вердикт |
| 2D geometry core | available | regression tests (bowtie/collinear/NaN) | `geometry.py` | measurement layer, не ingestion |
| Region quality/type assessment | available | tests | `region_quality.py`, `region_classifier.py` | advisory, не CV |
| Capability honesty API | available | schema 1.3.0 | `/v1/system/capabilities` | да |
| Evidence bundle CLI | available | tool | `export_evidence_bundle` | да |
| Native DWG | **missing** | fail-closed, never OK | `OdaCadModelIngestor` @sota-stub | нет |
| DXF | partial | optional `[cad]`, fixture | `EzdxfCadModelIngestor` (DI default) | нет (≠ DWG) |
| Human-level CV / VLM literacy | **missing** | `cv_human_level=missing` | — | нет |
| MEP system-aware clash | **not verified / blocked** | `UnconfiguredMepSystemGraphProvider` default | `domain/mep.py` | нет (RT-003) |
| Independent calc correctness | **not implemented** | — | — | нет |
| Full OIDC BFF | designed / not implemented | `GET /v1/auth/bff` → 501 | POST-05 | нет |
| Customer accuracy >90% | **blocked** | нет корпуса | `PrecisionClaim` gate | нет (RT-001) |
| Customer SLA ≤30 мин | **blocked** | только fixture 1096 B | `measure_package_sla` | нет |
| Hybrid AI routing | available (eng), not wired | 80–97 tests | `domain/hybrid/*` | нет (advisory scaffold) |

---

## 3. СПИСОК ИЗМЕНЕНИЙ ПОСЛЕ 20.07 (проверено по git log и коду)

| Commit | Изменение | Проверка |
|---|---|---|
| `f2615e7` (21.07) | Волны F–L: precision gates, SLA claim gate 1.3.0, BCF ladder T0–T4, revision compare, threat model, open-core ADR | CRITICAL_BLOCKERS обновлён |
| ~25.07 | BCF structural handoff v2 (2.1+3.0, XSD passed, dual-consumer) | `bcf-structural-handoff-2026-07-25.json` |
| 28.07 | Hybrid AI foundation P0/P1 + Red Team hyperdeep (0 новых эксплуатируемых дефектов; OIDC assert→raise) + VLM cache tenant isolation fix | HYBRID_AI_* и RED_TEAM_* отчёты |
| `bdf7561`/`b21ca15` (29.07) | Coverage: derive_report_scope, processing-evidence-only scope, off-sheet fix (RT HIGH×2 + MEDIUM×2) | `check_coverage.py` + тесты |
| `a77493f` (29.07) | **P2 geometry core** (no new dependency) | `domain/geometry.py` |
| `7580908` (29.07) | Geometry RT fixes: bowtie→INVALID, collinear→INCOMPLETE, NaN→ValueError | regression tests |
| `98c6701` (29.07, HEAD) | Закрыты 2 cross-cutting findings: (1) drawing finding приписывался requirement source вместо sheet id; (2) документационный drift про coverage wiring | код+docs |
| — | Baseline 1510 → 1517 → 1520 → **1536** test functions | runtime-baseline-latest.json |

Разделение, требуемое ТЗ v3 (закреплено): coverage как **live read-only
endpoint** (есть), как **persisted report field** (НЕТ — не персистится), как
**evidence of checked scope** (есть), и **verdict** (coverage его не меняет).

---

## 4. RED TEAM ATTACKS A1–A14

Формат: Объект → Заявление → Доказано → Severity → Риск для КТ#2/КТ#3 →
Контрмера → Требование ТЗ → Критерий приёмки → Остаточный риск.

### A1. Claims drift — «документы обещают больше, чем код»

- **Объект:** README.md, README.ru.md, docs/*, audit/reports/*.
- **Заявление проекта:** статусы «честные», Claims Lock — SSOT формулировок.
- **Что доказано:** проверены маркеры «>90%», DWG-ready, MEP-ready, CDE-ready,
  production-ready, human-level CV — в README все они в разделе
  **«Not claimed»** / Forbidden. Дрейфа «в плюс» не найдено. Найден дрейф
  **«в минус»**: Claims Lock (17.07) не содержит формулировок про coverage,
  revision diff и geometry core (появились 29.07) — новые фичи живут вне
  контролируемого словаря. PROJECT_STATUS_AUDIT содержит устаревший
  снимок (581+ tests, 22 808 LOC) рядом с актуальным baseline 1536.
- **Severity:** MEDIUM.
- **Провал КТ#2/КТ#3:** жюри цитирует устаревший документ против свежего:
  «у вас документы противоречат друг другу — где ещё?».
- **Контрмера:** регламент «фича мержится только с обновлением Claims Lock»;
  один SSOT-снимок числовых метрик (runtime baseline), прочие документы —
  ссылки, не копии чисел.
- **Требование ТЗ:** ТР-401.
- **Критерий приёмки:** CI-гейт: grep запрещённых формулировок + проверка, что
  каждая capability из `/v1/system/capabilities` имеет строку в Claims Lock.
- **Остаточный риск:** LOW.

### A2. Fixture masquerading as customer evidence

- **Объект:** `docs/benchmark-evidence-2026.md`, `audit/evidence/samolet-sla-*.json`,
  `PrecisionClaim`.
- **Заявление:** все бенчмарки маркированы corpus_kind.
- **Что доказано:** corpus_kind везде `fixture`/`synthetic`, customer
  отсутствует; `PrecisionClaim.publishable` требует customer + ≥2 adjudicators
  и блокирует raw-проценты (`render_value` → «withheld»); SLA-артефакт несёт
  `claim_level=fixture_only`, machine fingerprint, cold/warm. Механика честная.
  НО: fixture-пак SLA — **1096 байт**, 1 итерация, 0.0096 мин — как evidence
  масштаба он ничего не доказывает.
- **Severity:** HIGH (риск неверной интерпретации на защите).
- **Провал КТ#2:** «покажите ваш ≤30 минут» → показан пак размером с одну
  страницу текста → доверие ко всем остальным метрикам падает.
- **Контрмера:** снять fixture-SLA из любых слайдов; собрать representative-пак
  (IFC ≥50 МБ, PDF ≥100 страниц, ≥5 источников) и измерить на нём ДО получения
  customer-пака, с манифестом.
- **Требование ТЗ:** ТР-501, ТР-502.
- **Критерий приёмки:** SLA-артефакт schema ≥1.3.0 c package manifest (hash,
  files, IFC bytes, PDF pages, drawings, calc count), cold+warm, stage timings.
- **Остаточный риск:** MEDIUM до customer-пака.

### A3. Geometry false confidence

- **Объект:** `domain/geometry.py` (commits `a77493f`, `7580908`).
- **Заявление:** недостоверное измерение никогда не читается как «0 нарушений».
- **Что доказано (по коду):** bowtie → INVALID («shoelace area undefined»);
  <3 вершин / открытый контур → INCOMPLETE; near-zero area (≤tol²) →
  INCOMPLETE; unit=None → UNIT_UNKNOWN («value not trustworthy»);
  NaN/inf координаты в измерениях → INVALID, в `segments_intersect` →
  `ValueError` (громко, не тихое False-«no clash»); regression-тесты bowtie/
  collinear/non-finite есть. `is_trustworthy()` истинно только при OK.
- **Не закрыто:** (1) self-touching контур — коллинеарное касание считается
  пересечением ⇒ кольцо станет INVALID (консервативно), но явного теста нет;
  (2) `coordinate_system` — поле есть в `GeometryDocument`, но mismatch двух
  документов в разных СК не детектируется; (3) length/area при unit=None
  возвращают численное значение со статусом UNIT_UNKNOWN — потребитель обязан
  проверять статус, а не value (API-ловушка).
- **Severity:** MEDIUM.
- **Провал КТ#2:** демонстрация «площадь помещения» на чертеже в неизвестной
  СК даёт число, которое эксперт примет за метры.
- **Контрмера:** `compare_measurements`-хелпер, отказывающийся сравнивать при
  разных unit/coordinate_system; тест self-touching; правило «никогда не читать
  Measurement.value без is_trustworthy()».
- **Требование ТЗ:** ТР-211…ТР-214.
- **Критерий приёмки:** property-тесты: любой не-OK статус ⇒ значение не
  участвует ни в одном finding с severity выше INFO.
- **Остаточный риск:** LOW после контрмер; core verdict-neutral.

### A4. Coverage false confidence

- **Объект:** `domain/check_coverage.py`, `GET /v1/reports/{id}/coverage`.
- **Заявление:** CHECKED_OK только при processing evidence; off-sheet finding
  блокирует чистый лист; coverage не меняет вердикт.
- **Что доказано:** `coverage_from_report` verdict-neutral (не читает/не пишет
  summary.passed); CHECKED_OK требует explicit per-source scope И все
  family-capabilities OK; FAILED family → INSUFFICIENT_DATA; off-sheet drawing
  finding подавляет per-sheet DRAWING scope (fix `98c6701`); endpoint
  ACL-scoped, derive on-the-fly, в отчёт не пишется. 16+ тестов.
- **Осталось атаковать:** (1) coverage не персистится — evidence bundle не
  содержит замороженную карту покрытия на момент вердикта: при апгрейде
  алгоритма историческая карта «поедет»; (2) пустой источник (0 требований) —
  проверить, что пустота маркируется NOT_CHECKED, а не CHECKED_OK.
- **Severity:** MEDIUM.
- **Провал КТ#3:** заказчик сохранил отчёт, через месяц coverage у того же
  отчёта другой → «ваши доказательства нестабильны».
- **Контрмера:** снапшот coverage в evidence bundle (файл, не поле отчёта) с
  версией алгоритма; тест на empty-source.
- **Требование ТЗ:** ТР-221…ТР-224.
- **Критерий приёмки:** bundle содержит `check-coverage.json` c
  `algorithm_version` и hash отчёта; повторный derive на том же коде
  бит-в-бит совпадает.
- **Остаточный риск:** LOW.

### A5. Drawing quality

- **Объект:** `region_quality.py`, `region_classifier.py`,
  `drawing_region_assessment.py`, OCR-путь.
- **Заявление:** BAD и UNKNOWN ≠ NO VIOLATIONS.
- **Что доказано:** NaN/inf сигналы нормализуются в None (иначе NaN-сравнения
  «проваливали» бы регион в READABLE — прямой комментарий в коде); нет
  сигналов → REVIEW_REQUIRED; READABLE требует позитивного dpi-evidence;
  zero-yield OCR при requested → FAILED capability; classifier tie → UNKNOWN
  (word-boundary matching). Всё verdict-neutral.
- **Осталось:** чертёж со штампом поверх текста и рукописные правки — нет
  специализированных фикстур; «synthetic drawing evidence» не является
  human-level CV (проект сам декларирует `cv_human_level=missing`).
- **Severity:** MEDIUM.
- **Провал КТ#2:** живой чертёж Самолёта с печатью поверх размеров → OCR
  отдаёт мусор → нужно показать REVIEW_REQUIRED, а не PASS.
- **Контрмера:** 3 adversarial-фикстуры (штамп, рукопись, скан 60 dpi) в
  regression-набор; демонстрация anti-bad-scan routing на защите.
- **Требование ТЗ:** ТР-231…ТР-233.
- **Критерий приёмки:** на adversarial-фикстурах итог листа ∈ {REVIEW_REQUIRED,
  INSUFFICIENT_DATA}, никогда CHECKED_OK/PASS.
- **Остаточный риск:** MEDIUM — реальное разнообразие плохих сканов больше
  фикстурного набора; закрывается только customer-корпусом (RT-001).

### A6. Revision integrity

- **Объект:** `domain/revision_diff.py`, идентичность документов.
- **Заявление:** delimiter-proof key; отсутствующая revision не ведёт к
  silent merge; diff verdict-neutral.
- **Что доказано:** `_finding_key` = `fid:` либо `json.dumps`-композит
  (rule_id, category, element_guid, target_ref, source_id) — `|` внутри поля
  не сдвигает границы; `no_longer_reported` документированно НЕ означает
  «resolved»; `compare_report_revisions` не читает summary.passed; ключи
  сортированы (воспроизводимость).
- **Осталось:** (1) одинаковый filename при разных hash — diff работает на
  уровне отчётов, а не файлов; прямого intake-теста «две версии одного листа
  в одном пакете» не найдено; (2) old_revision=None/None — diff выполнится,
  ярлык «сравнение неатрибутированных ревизий» остаётся на потребителе.
- **Severity:** MEDIUM.
- **Провал КТ#3:** пакет с двумя ревизиями одного листа — если обе прошли как
  независимые источники, отчёт «раздвоится».
- **Контрмера:** intake-правило: дубль (same container id, разные hash) →
  WARNING + требование явной revision; в diff-ответ `revision_confidence`
  (both/partial/none).
- **Требование ТЗ:** ТР-241…ТР-243.
- **Критерий приёмки:** тест: пакет с двумя версиями листа без revision-меток
  не даёт silent merge и порождает явный finding.
- **Остаточный риск:** LOW.

### A7. Port fantasy — CONTOUR_PORTS vs реальность

- **Объект:** `domain/architecture.py` vs `domain/ports.py` vs DI vs тесты.
- **Заявление README:** «20 domain ports → 30 адаптеров → 28 DI-токенов».
- **Что доказано:** в `ports.py` — 29 Protocol + 1 реэкспорт (README «20 domain ports» = wired live-набор, а не все declared Protocol —
  не занижение). В `CONTOUR_PORTS` 35 имён, из них **11 нет в ports.py**:
  `DocumentIdentity` (dataclass, не порт), `SystemClashPort` (в
  `tz_architecture_ports.py`, DI default `UnconfiguredSystemClash`),
  `IdsAssistDraftPort` (в application-boundary, НЕ wired в bootstrap),
  `DrawingAnalyzerPort`, `CadEntityLoaderPort`, `AdvisoryTextAssist`
  («reserved»), `RequirementInterpreterPort`, `NormRetrieverPort`,
  `ComplianceAgentOrchestrator`, `AgenticReviewOrchestrator`,
  `IfcKnowledgeGraphPort`. Обратно: 6 портов ports.py не входят ни в один
  контур (ObjectStore, JobStore и др. — инфраструктурные; нигде не объяснено).
- **Классификация:**

| Порт | declared | implemented | DI-wired | runtime-probed | tested | customer-proven |
|---|---|---|---|---|---|---|
| IfcValidator, IdsValidator, ClashDetector, NormRulePackLoader, SectionDiffAnalyzer, QuantityConsistencyChecker, LoadEvidenceVerifier, LogicConsistencyAnalyzer, DrawingRegionDetector, MultimodalDrawingPipeline, RemarkGenerator, AuditReportStore, ReviewEventStore, ObjectStore, JobStore, NormRulePackVersionStore, ExternalEvidenceVerifier | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| CadModelIngestor (DXF) | ✓ | ✓ (ezdxf) | ✓ | ✓ (never OK for DWG) | ✓ | ✗ |
| SystemClashPort | ✓ (tz_ports) | scaffold (`IfcSystemAwareClash`) | ✓ (Unconfigured default) | ✓ (NOT_VERIFIED) | ✓ | ✗ |
| MepSystemGraphProvider | ✓ | Unconfigured/Synthetic | ✓ (fail-closed) | ✓ (NOT_VERIFIED) | ✓ | ✗ |
| BcfApiClient | ✓ | ✓ | ✓ (Unconfigured default) | experimental | ✓ | ✗ |
| IdsAssistDraftPort | ✓ (app boundary) | stub | **✗ не wired** | ✗ | ✓ (boundary) | ✗ |
| AdvisoryTextAssist, RequirementInterpreterPort, NormRetrieverPort, ComplianceAgentOrchestrator, AgenticReviewOrchestrator, DrawingAnalyzerPort, CadEntityLoaderPort | имя в CONTOUR_PORTS | ✗ | ✗ | ✗ | ✗ | ✗ |
| IfcKnowledgeGraphPort | имя в CONTOUR_PORTS | `RelationalIfcKnowledgeGraph` | ✓ | advisory | ✓ | ✗ |

- **Severity:** MEDIUM (код честный; риск — в презентации архитектуры).
- **Провал КТ#2:** «покажите адаптер AgenticReviewOrchestrator» — его нет,
  а имя в архитектурном SSOT есть.
- **Контрмера:** машинно-читаемый `RESERVED_PORTS`; тест синхронизации
  CONTOUR_PORTS ↔ ports.py ↔ Tokens; README-число портов генерируется (различать 20 wired vs 29 declared).
- **Требование ТЗ:** ТР-301…ТР-303.
- **Критерий приёмки:** CI-тест падает при имени порта без классификации
  declared/reserved/implemented.
- **Остаточный риск:** LOW.

### A8. MEP false claim

- **Объект:** `domain/mep.py`, DI, `/v1/system/capabilities`.
- **Заявление:** MEP system-aware clash НЕ заявлен как delivered.
- **Что доказано:** DI default — `ScopedMepSystemGraphProvider` с fallback
  `UnconfiguredMepSystemGraphProvider` (RuntimeError MEP-CLASH-001);
  `SyntheticMepSystemGraphProvider` — @sota-stub, unit-tests only,
  `synthetic=True` never product OK; analyze probe держит
  `mep_system_clash=NOT_VERIFIED` даже при существующих узлах; ERROR
  (`AEROBIM-MEP-FORBIDDEN`) только при geometry_verified И не-synthetic
  матрице, иначе деградация в WARNING; unclassified pair → NOT_VERIFIED;
  в pilot/production `require_mep_system_clash=true` ⇒ NOT_VERIFIED
  **блокирует** pass. Co-presence ≠ connection — закреплено в Claims Lock.
- **Severity:** LOW (механика fail-closed выдерживает атаку).
- **Провал КТ#2:** только если презентер словами скажет «MEP есть». Система
  защищена от собственного маркетинга.
- **Контрмера:** в демо показывать NOT_VERIFIED-статус как фичу честности;
  заготовленный ответ про RT-003 dependency.
- **Требование ТЗ:** ТР-311, ТР-312.
- **Критерий приёмки:** e2e-тест: пакет с MEP-моделями под profile=samolet_pilot
  даёт passed=false с blocked=mep_system_clash.
- **Остаточный риск:** LOW.

### A9. Normative hallucination

- **Объект:** norm packs (`JsonNormRulePackLoader`, `NormRulePackVersionStore`,
  `norm_applicability.py`), RT-002.
- **Заявление:** только synthetic/draft packs; approval-объект обязателен для
  customer-pack.
- **Что доказано:** `verify_version_integrity` в порте; rule-events API
  (`proposed_by` привязан к principal — RTATOM H05/I07); требования к
  customer-pack зафиксированы (approved_by, approval_date, edition,
  effective_date, scope_reference, pack_hash, per-rule clause; «approval_ref
  alone rejected»); blank/degenerate applicability context → UNKNOWN
  (advisory, verdict-neutral).
- **Осталось:** ни одного утверждённого пака (RT-002 OPEN); нет CI-теста, что
  synthetic-pack физически не может получить claim_label=approved.
- **Severity:** HIGH (customer-blocker КТ#2).
- **Провал КТ#2:** без нормопака «проверка на соответствие нормам» остаётся
  демонстрацией на синтетике.
- **Контрмера:** intake-гейт: pack без полного approval-объекта не получает
  `claim_label` выше draft; запрос к заказчику — 10–20 приоритетных
  СП/ГОСТ-правил (§13, вопрос 2).
- **Требование ТЗ:** ТР-321…ТР-324.
- **Критерий приёмки:** тест: pack c approval_status=approved без
  hash/owner/date → reject.
- **Остаточный риск:** HIGH до подписи заказчика (вне контроля команды).

### A10. AI verdict contamination

- **Объект:** AdvisoryOrchestrator, hybrid gate, OCR, IDS draft, remark
  composer vs `summary.passed`.
- **Заявление:** только детерминированный контур пишет вердикт (ADR-001).
- **Что доказано:** вердикт = `SignOffCapabilityPolicy.summary_passed` от
  error_count + capabilities; advisory-стадия исполняется ПОСЛЕ deterministic,
  её выход не входит в аргументы политики; hybrid gate/VLM/model router
  «DELIBERATELY NOT consumed by AnalyzeProjectPackageUseCase» (bootstrap,
  OFF==ON); review-events append-only; `StubIdsAssistDraftAdapter` не wired.
  OCR влияет на вердикт только через honesty-канал: zero-yield при requested →
  capability FAILED → passed=false (fail-closed — корректное направление).
- **Severity:** LOW.
- **Провал КТ#2:** маловероятен; наоборот — сильная сторона на защите.
- **Контрмера:** мутационный тест «advisory ON/OFF не меняет passed» в
  обязательном CI-наборе; DivergenceRecord (engine ≻ LLM) — в P3.
- **Требование ТЗ:** ТР-331, ТР-332.
- **Критерий приёмки:** OFF==ON тест на каждом PR, затрагивающем advisory.
- **Остаточный риск:** LOW.

### A11. Security and OIDC

- **Объект:** auth, ACL, storage, upload, экспорт.
- **Заявление:** fail-closed периметр; RTATOM A1/A2.5/A3 закрыты.
- **Что доказано:** bearer на 21/21 `/v1/*`; cross-tenant → 404; SSRF-guard с
  DNS-pin (`resolve_and_pin_outbound_url`); path jail + re-jail на
  FileResponse; ZIP: `inspect_zip_path` на upload (bomb/traversal), reject
  `..`/absolute members; XML-caps (`xml_limits`); IFC cap 256 MiB; preview
  MIME allowlist; hashed locks + pinned pip/uv; VITE bearer в build по
  умолчанию НЕ зашивается (закомментирован, legacy-only); anonymous только
  dev+flag; OIDC-валидатор отказывает при частичной конфигурации.
- **Не закрыто:** **POST-05 full OIDC BFF — DESIGNED / NOT_IMPLEMENTED**
  (`GET /v1/auth/bff` → 501): браузерный клиент пока предполагает bearer, что
  для корпоративного пилота может быть неприемлемо; PII в штампах чертежей —
  маскирование есть в hybrid-контуре, но контур не wired, drawing preview
  отдаёт растр как есть (PII-экспозиция внутри tenant — назвать явно).
- **Severity:** MEDIUM (BFF), LOW (остальное).
- **Провал КТ#3:** ИБ-служба заказчика блокирует пилот из-за
  bearer-в-браузере.
- **Контрмера:** POST-05 BFF до КТ#3 либо письменные компенсирующие меры
  (короткоживущие токены, reverse-proxy auth).
- **Требование ТЗ:** ТР-341…ТР-344.
- **Критерий приёмки:** e2e: браузерная сессия без токена в JS-доступном
  хранилище; чеклист OWASP ASVS L2 подписан.
- **Остаточный риск:** MEDIUM до BFF.

### A12. BCF interoperability

- **Объект:** BCF ladder T0–T4.
- **Заявление:** T0 AVAILABLE, T1 evidenced, T2 NOT_VERIFIED.
- **Что доказано:** артефакт 2026-07-25: BCF 2.1 и 3.0, по 2 topics/markups/
  viewpoints, xsd_status=passed, sha256 обоих ZIP, `claim_level=
  structural_only`; `cde-import-proof/STATUS.json`: required=[import-log.txt,
  screenshot.png, hashes.json], **present_files=[]**, claim_allowed=false;
  OpenCDE push — foundation, default `UnconfiguredBcfApiClient`. «CDE-ready» /
  «CDE interoperable» запрещены Claims Lock — соблюдено.
- **Severity:** LOW (механика), HIGH (зависимость от заказчика для T2).
- **Провал КТ#3:** приёмка потребует импорт в реальный СОД Самолёта.
- **Контрмера:** week-1 пилота: совместный импорт в CDE заказчика, лог +
  скриншот + hashes → T2; round-trip (T3) — после.
- **Требование ТЗ:** ТР-351, ТР-352.
- **Критерий приёмки:** папка cde-import-proof заполнена тремя артефактами,
  подписана спонсором пилота.
- **Остаточный риск:** зависит от CDE заказчика (вне контроля).

### A13. SLA

- **Объект:** `measure_package_sla`, SLA-артефакты, stage budgets 5+18+2+5 мин.
- **Заявление:** ≤30 мин — только на согласованном эталонном пакете.
- **Что доказано:** schema с refuse-without-evidence для `customer_measurable`;
  артефакт честно маркирован fixture_only; machine fingerprint есть; timeout
  budgets по стадиям есть. **Слабость — сам пак:** 1096 байт, 1 итерация,
  cold-only (warm=null). Экстраполяции на реальный пакет (IFC сотни МБ +
  сотни листов PDF + OCR) не существует.
- **Severity:** HIGH.
- **Провал КТ#2:** см. A2; при включённых extras (clash, OCR, docling) время
  может вырасти на порядок — профилирование не опубликовано.
- **Контрмера:** до КТ#2 прогнать representative-пак в трёх конфигурациях:
  core / +raster / +clash+docling, cold и warm, опубликовать stage timings;
  «package definition» согласовать письменно.
- **Требование ТЗ:** ТР-361…ТР-363.
- **Критерий приёмки:** SLA-артефакт на паке с манифестом ≥ согласованного
  размера; таймаут = деградация в BLOCKED, не silent partial PASS.
- **Остаточный риск:** MEDIUM до customer-пака.

### A14. Human accountability

- **Объект:** HITL-цепочка, review-events, KPI, alert fatigue.
- **Заявление:** эксперт остаётся подотчётным; автоматика сокращает объём, не
  ответственность.
- **Что доказано:** решение принимает эксперт (система выдаёт Shared-gate,
  не contractual sign-off — ADR-001); advisory виден в отчёте с provenance;
  remark редактируется в review-shell; finding закрывается review-event'ом с
  валидируемым переходом (`assert_hitl_transition`, server-SSOT
  previous_state); actor — из аутентифицированного principal; HITL НЕ может
  изменить verdict; KPI (triage/acceptance) считаются по событиям. Против
  false negative: coverage явно показывает NOT_CHECKED-зоны.
- **Не закрыто:** anti-alert-fatigue: приоритизация есть
  (`compute_issue_priority`, профиль samolet), но нет измеренного FP-rate по
  дисциплинам (нужен корпус) и нет UI-агрегации повторяющихся замечаний.
- **Severity:** MEDIUM.
- **Провал КТ#3:** эксперты утонут в повторах WARNING → KPI пилота провалится.
- **Контрмера:** дедупликация findings по (rule_id, sheet); недельный FP-лог;
  порог confirmed-rate ≥60% как KPI-гипотеза.
- **Требование ТЗ:** ТР-371…ТР-373.
- **Критерий приёмки:** review-KPI отчёт за 2 недели пилота, FP-rate по
  дисциплинам, время triage на finding.
- **Остаточный риск:** MEDIUM до пилота.

---

## 5. АУДИТ ИСХОДНОГО ТЗ (v2, `docs/tz/TZ_SAMOLET_TECHLAB_TASK_07_V2_2026.md`)

Сопоставление с TZ_COMPLIANCE_MATRIX (v1.2.0) и текущим кодом:

| Раздел исходного ТЗ | Статус в v2 | Правка для v3 |
|---|---|---|
| §1 Термины (OCR/CV/NLP/BIM) | покрыт | [УТОЧНЕНО] добавить: coverage evidence, revision diff, geometry core, PackageOutcome, Shared-gate, DivergenceRecord, corpus_kind |
| §2 Концепция (ассистент, не замена) | покрыт | [УТОЧНЕНО] закрепить формулу спонсора: «не заменить инженера, а не пропустить очевидную ошибку» + ADR-001 |
| §3.1 Графический анализ | частично | [УТОЧНЕНО] честная лестница: OCR baseline (есть) → region quality/type (есть) → detector priors (есть) → VLM advisory (P2/P3); human-level CV [СНЯТО: противоречит коду — `cv_human_level=missing`] |
| §3.2 Compliance | частично | [УТОЧНЕНО] IDS + synthetic packs есть; «полное покрытие СП/ГОСТ» [СНЯТО: противоречит коду, RT-002] |
| §3.3 Детект ошибок | покрыт | [УТОЧНЕНО] отделить cross-doc / quantity ε-band / generic clash (есть) от MEP system-aware (RT-003) и calc correctness [СНЯТО] |
| §3.4 Поддержка эксперта | покрыт | [НОВОЕ] HITL state machine, review-KPI, приоритизация — доказаны тестами |
| §4 Функциональность | частично | [НОВОЕ] coverage endpoint, revision diff, geometry core, PackageOutcome; [СНЯТО] «upload DWG» как native |
| §5 Источники данных | покрыт | [УТОЧНЕНО] матрица зависимостей от заказчика (§9 v3) |
| §6 Критерии оценки | слабо | [ПЕРЕФОРМУЛИРОВАНО] §6.9 v3 — измеримые метрики вместо «точность >90%» |
| §7 Приложения | покрыт | ссылки на audit/evidence |
| §8 Фазы MVP/P0–P4 | покрыт | [УТОЧНЕНО] geometry core перенесён из P2-plan в P1-done |

Ключевые снятия (противоречат фактическому коду):
- [СНЯТО] любые намёки на native DWG анализ (honesty `dwg_dxf` never OK);
- [СНЯТО] «независимая проверка корректности расчётов» (только сверка);
- [СНЯТО] «система выставляет окончательный вердикт» (Shared-gate, не Published);
- [СНЯТО] MEP system-aware как поставляемая функция (RT-003 OPEN).

---

## 6. ТЗ v3 (полная редакция)

### 6.1. Термины и определения

| Термин | Определение |
|---|---|
| Пакет документации | Согласованный набор: ПД/РД (PDF), BIM (IFC 2x3/4/4x3), ТЗ/спецификации, расчёты, IDS, нормопак |
| Shared-gate | Автоматический детерминированный вердикт `summary.passed` в смысле ISO 19650 Shared (НЕ Published/договорная пригодность) |
| Capability honesty | Явный статус подсистемы: ok/skipped/failed/missing/not_verified/not_implemented; FAILED блокирует pass |
| PackageOutcome | pass / pass_with_warnings / review_required / blocked / failed |
| Coverage evidence | Verdict-neutral карта «что реально проверено»: CHECKED_OK / NOT_CHECKED / INSUFFICIENT_DATA / FINDINGS_PRESENT |
| Revision diff | Verdict-neutral дельта findings между двумя ревизиями отчёта |
| Geometry core | Детерминированные измерения (площадь/длина/пересечения) над УЖЕ извлечёнными примитивами; не парсер DWG/DXF |
| corpus_kind | synthetic / fixture / customer — класс происхождения данных любой метрики |
| DivergenceRecord | Запись расхождения advisory-AI с детерминированным движком (движок главнее) |
| HITL | Human-in-the-loop: эксперт подтверждает/отклоняет findings; события аудируются |
| Сверка (calculation match) | Сопоставление переданных результатов расчётов с источниками; НЕ проверка корректности расчёта |

### 6.2. Актуальность

Экспертиза ПД/РД — узкое место девелопмента: ручная проверка комплекта
занимает дни, очевидные ошибки доходят до стройки. Задача 07 (приз — платный
пилот 2 000 000 ₽, Moscow Innovation Cluster TechLab) требует reviewer-assist
MVP. Мировой каркас 2026: IFC + IDS 1.0 + BCF 2.1/3.0, гибридные ИИ-контуры
(«облако думает, контур охраняет»), обязательная доказуемость метрик
(frozen corpus, adjudication, κ/α).

### 6.3. Концепция

Детерминированный ассистент приёмочных критериев с AI-advisory-обвязкой.
Автоматика сокращает объём ручной проверки; ответственность остаётся на
эксперте. Ни один AI-компонент не имеет права выставлять или менять вердикт.

### 6.4. Целевые задачи

1. Кросс-проверка ПД/РД ↔ BIM ↔ ТЗ ↔ расчёты ↔ нормативные правила.
2. Обнаружение: противоречий между документами, ошибок величин/площадей
   (ε-band), геометрических коллизий (generic), логических пропусков,
   отсутствующих элементов (IDS), недостоверной геометрии.
3. Подсветка проблемных зон (2D overlay + IFC viewer) и приоритизация.
4. Отчёты для координации: HTML/JSON/BCF ZIP + evidence bundle.
5. Доказуемость: provenance каждого finding, coverage карта, revision diff.

### 6.5. Функциональность (сводно; статусы — §2.3)

MVP-ядро (доказано): IFC/IDS/cross-doc/quantity/clash-optional; honesty API;
fail-closed профили; отчёты + BCF T1; browser review; HITL; ACL/SSRF/jail;
coverage; revision diff; geometry core; region quality.
Advisory (не в вердикте): remark templates RU/EN, IFC KG advisory, hybrid
routing foundation. Planned: VLM advisory, LLM remarks, IDS-assist, norm
retrieval, DXF продуктово / DWG при лицензии, MEP system-aware, CDE T2+.

### 6.6. Источники данных и ограничения

Вход: PDF (детерминированный текст PyMuPDF; растр — RapidOCR optional),
IFC ≤256 MiB, IDS XML, DXF (optional ezdxf), XLSX/DOCX (optional docling),
OpenRebar result.json (сверка). Native DWG не принимается (derived PDF/IFC с
provenance). Customer-данные — только внутри контура пилота (NDA), в
публичный репозиторий не попадают.

### 6.7. Требования (ТР-xxx)

Нумерация: ТР-1xx архитектура, ТР-2xx детерминированные ядра, ТР-3xx порты и
advisory, ТР-4xx честность/claims, ТР-5xx метрики/SLA, ТР-6xx безопасность,
ТР-7xx HITL, ТР-8xx гибридный контур. Формат: формулировка · статус ·
модуль/источник · фаза · критерий приёмки · поведение при сбое · риск.

**ТР-101 [УТОЧНЕНО].** Пять слоёв core→domain→application→infrastructure→
presentation; domain не импортирует infrastructure; DI — единый composition
root. — реализовано · `bootstrap.py` · MVP · арх-тест в CI · сборка падает ·
LOW.

**ТР-102 [УТОЧНЕНО].** Четыре контура INGESTION→DETERMINISTIC_VALIDATION→
AI_ADVISORY→EVIDENCE_REPORTING; только детерминированный контур определяет
`summary.passed`; физический writer — EvidenceAssembler (ADR-001). —
реализовано · `capability_policy.py` · MVP · OFF==ON мутационный тест ·
advisory-исключение не меняет вердикт · LOW.

**ТР-103 [НОВОЕ].** Новый порт поставляется вместе с адаптером, DI-токеном,
wiring и тестом; имена без реализации — в машинно-читаемом `RESERVED_PORTS`.
— частично (11 имён без реализации в CONTOUR_PORTS, атака A7) ·
`architecture.py` · P1 · CI-тест синхронизации CONTOUR_PORTS↔ports.py↔Tokens
· CI red · LOW.

**ТР-104 [НОВОЕ].** `PackageOutcome` — единственный источник `summary.passed`
(`summary_passed_from_outcome`). — реализовано · `package_outcome.py` · MVP ·
grep-тест прямых записей passed · LOW.

**ТР-201 [УТОЧНЕНО].** IFC property/quantity валидация IFC2x3/4/4x3 единым
ядром; расхождения Pset между релизами — ValidationIssue, не silent skip. —
реализовано (fixture) · MVP · фикстуры трёх релизов зелёные · capability
FAILED → pass=false · LOW.

**ТР-202.** IDS 1.0 через IfcTester; неверная конфигурация requested-пути —
fail-closed. — реализовано · MVP.

**ТР-203.** Cross-doc противоречия с ConflictKind и конфигурируемой severity.
— реализовано · MVP.

**ТР-204.** Quantity ε-band (ISO 12006-3), SI-нормализация. — реализовано ·
MVP.

**ТР-211 [НОВОЕ].** Geometry: любое измерение несёт статус OK/INCOMPLETE/
UNIT_UNKNOWN/INVALID; недоверенное значение не участвует в findings severity
выше INFO. — core реализован; правило потребления — P1 · `geometry.py` ·
property-тест · INVALID/INCOMPLETE → REVIEW_REQUIRED, не «0 нарушений» · LOW.

**ТР-212 [НОВОЕ].** NaN/inf: измерения → INVALID; предикаты пересечения →
громкий ValueError; тихое False запрещено. — реализовано + regression ·
P1-done.

**ТР-213 [НОВОЕ].** Bowtie/вырожденный контур не дают доверенной площади;
открытый контур — не площадь. — реализовано + regression · P1-done.

**ТР-214 [НОВОЕ].** Сравнение измерений — только при совпадающих unit и
coordinate_system. — planned · P2 · `compare_measurements` + тесты · отказ
сравнения → UNKNOWN-исход · MEDIUM до реализации.

**ТР-221 [НОВОЕ].** Coverage: CHECKED_OK только при processing evidence
источника/листа; off-sheet finding блокирует чистый статус листа; FAILED
family → INSUFFICIENT_DATA. — реализовано (16+ тестов) · P1-done ·
derive-ошибка → 5xx, отчёт не мутирует.

**ТР-222 [НОВОЕ].** Coverage verdict-neutral: не читает и не пишет
`summary.passed`. — реализовано · контракт + тест.

**ТР-223 [НОВОЕ].** Снапшот coverage в evidence bundle с algorithm_version и
hash отчёта. — planned · P1 · повторный derive бит-в-бит совпадает · MEDIUM.

**ТР-224 [НОВОЕ].** Пустой источник не получает CHECKED_OK. — дотестировать ·
P1.

**ТР-231 [НОВОЕ].** Region quality: NaN/inf сигналы → UNKNOWN-ветка; нет
сигналов → REVIEW_REQUIRED; READABLE требует позитивного evidence. —
реализовано · P1-done.

**ТР-232 [НОВОЕ].** BAD/UNKNOWN качество ≠ «нарушений нет»; пустой OCR при
requested → capability FAILED. — реализовано · MVP/P1.

**ТР-233 [НОВОЕ].** Adversarial-фикстуры (штамп поверх текста, рукопись,
низкий DPI) в regression-наборе. — planned · P1→КТ#2 · итог листа ∈
{REVIEW_REQUIRED, INSUFFICIENT_DATA} · MEDIUM.

**ТР-241 [НОВОЕ].** Revision diff: delimiter-proof key; verdict-neutral;
`no_longer_reported` ≠ resolved. — реализовано · P1-done.

**ТР-242 [НОВОЕ].** Дубликат листа (same container, разные hash) без явной
revision → WARNING; silent merge запрещён. — planned · P1 · intake-тест.

**ТР-243 [НОВОЕ].** Diff-ответ содержит revision_confidence
(both/partial/none). — planned · P2.

**ТР-301.** Классификация каждого порта: declared/implemented/DI-wired/
runtime-probed/tested/customer-proven; публикуется в приложении. — выполнено
вручную (A7); автоматизация · P1.

**ТР-302.** README-числа портов/адаптеров/токенов генерируются, не пишутся
руками (различать: 20 wired live-портов vs 29 declared Protocol). — planned · P1.

**ТР-303.** Capability не считается готовой из-за имени в CONTOUR_PORTS или
architecture-документе. — норма закреплена · постоянная.

**ТР-311.** MEP: DI-default fail-closed (Unconfigured → NOT_VERIFIED);
synthetic-граф никогда не даёт product OK; ERROR только при geometry_verified
и не-synthetic матрице. — реализовано · `mep.py` · MVP.

**ТР-312.** Под samolet_pilot/production MEP NOT_VERIFIED блокирует pass. —
реализовано · e2e-тест приёмки.

**ТР-321.** Customer-нормопак: полный approval-объект (approved_by,
approval_date, edition, effective_date, scope_reference, jurisdiction,
pack_hash, owner, per-rule clause, immutable version, границы применения). —
контракт готов; данных нет (RT-002) · needs customer.

**ТР-322.** Synthetic/draft pack не может получить claim_label approved. —
дотестировать · P1 · reject-тест.

**ТР-323.** Rule provenance: clause + applicability на каждом правиле;
blank/degenerate context → UNKNOWN, не ERROR. — реализовано (advisory) ·
P1-done.

**ТР-324.** Hash-integrity пака проверяется при загрузке
(`verify_version_integrity`). — реализовано.

**ТР-331.** LLM/VLM/OCR/RAG/агенты/remark composer не могут: выставлять
PASS/FAILED, отменять deterministic finding, менять capability state или
sign-off. — реализовано (архитектурно + OFF==ON) · постоянная.

**ТР-332 [НОВОЕ].** Расхождение advisory с движком → DivergenceRecord
(WARNING, движок главнее). — planned (design в TARGET_HYBRID) · P3.

**ТР-401.** Claims Lock — живой регистр: мерж фичи требует строку в Lock;
CI-grep запрещённых формулировок. — частично (Lock отстаёт от 29.07) ·
немедленно · Lock v2 с coverage/revision/geometry.

**ТР-402.** Все публичные числа — из одного генерируемого baseline;
устаревшие снимки помечаются superseded. — частично · P1.

**ТР-501.** Метрики точности публикуются только при corpus_kind=customer,
≥2 adjudicators, agreement-артефакт, held-out split, FN tracked
(`precision_claim_publishable_with_agreement`). **Enforced runtime gate:
κ≥0.60, α≥0.67. Методическая цель κ>0.80 — НЕ enforced gate** (не
смешивать). — гейт реализован; корпуса нет · needs customer.

**ТР-502.** SLA-заявление ≤30 мин — только с манифестом пака (hash, files,
IFC bytes, PDF pages, drawings, calc count), machine fingerprint,
Python/lock, cold+warm, stage timings, optional extras. — schema есть;
representative-пак нужен · до КТ#2.

**ТР-503.** Метрики разделяются: detection / extraction / ranking / remark
quality; per-discipline, per-error-class. — harness частично · P4.

**ТР-601.** Fail-closed периметр: bearer/OIDC на всех /v1/*, cross-tenant →
404, SSRF DNS-pin, path jail, ZIP/XML caps, IFC 256 MiB, preview MIME
allowlist, hashed locks. — реализовано · MVP.

**ТР-602.** Full OIDC BFF (POST-05): браузер без bearer в JS-хранилище. —
DESIGNED / NOT_IMPLEMENTED (`/v1/auth/bff` → 501) · до КТ#3 · MEDIUM.

**ТР-603.** Retention TTL; audit fail-closed при коррупции JSONL под
pilot/production. — реализовано.

**ТР-604 [НОВОЕ].** PII в штампах чертежей: внутриконтурное хранение; выход
в облако — только через маскирование (§6.8); masking ≠ anonymity. —
политика фиксируется этим ТЗ · P1 (док), P3 (техника).

**ТР-701.** HITL state machine: сервер — SSOT previous_state; actor из
principal; идемпотентность; события не меняют вердикт. — реализовано · MVP.

**ТР-702.** Review-KPI: triage-время, acceptance-rate, FP-rate по
дисциплинам; недельный лог в пилоте. — endpoint есть; FP-rate — needs
customer · пилот.

**ТР-703 [НОВОЕ].** Anti-alert-fatigue: дедупликация findings (rule_id ×
sheet) с агрегированной карточкой. — planned · P2.

### 6.8. Гибридный ИИ-контур («облако думает, контур охраняет»)

Целевая цепочка (foundation в `domain/hybrid/*`; честный статус: НЕ wired в
вердикт и живой egress):

Шлюз → Гардрейл → Regex + локальная LLM 4–8B → Маскировщик ПД → Роутер →
облачная/локальная модель → демаскирование внутри контура → аудит-лог.

Матрица маршрутизации (policy engine, 5 уровней, unknown→CONFIDENTIAL,
fail-closed):

| Тип задачи | Чувствительность | Маршрут |
|---|---|---|
| Код/R&D | низкая | фронтирная модель |
| Тексты без ПД | средняя | РФ-облако или локальная модель |
| ПД/сметы/клиентские данные | высокая | маскирование + разрешённый провайдер |
| Полный критичный комплект | максимальная | локально / air-gapped |
| Нормативный текст | по лицензии | утверждённый norm corpus |
| Расчётные документы | высокая | локальная сверка; advisory отдельно |

**ТР-801.** Словарь маскирования — только внутри контура; облако получает
только маскированный текст; демаскирование — только локально. —
privacy_guard реализован (masked=None → may_call_external=False); live
egress отсутствует · P3.

**ТР-802.** Каждый AI-вызов логируется: provider, model, timestamp, request
class, sensitivity, masked/unmasked, source hash, response hash; секреты в
лог не попадают. — audit_event реализован (secret-safe) · P3-live.

**ТР-803.** Vendor-agnostic provider adapter: смена модели не трогает
application/domain. — ModelRouter + ProviderRegistry реализованы; дефолт
local-only · P3.

**ТР-804.** Air-gapped профиль обязателен; локальная модель не получает
sign-off authority; полный IFC/PDF/DWG не уходит наружу без явного policy
decision. — политика в коде (fail-closed default) · P3.

**ТР-805 [НОВОЕ].** Воронка пользы: Доступ → Adoption → Частота →
Сэкономленное время → Деньги; «пользуются» ≠ «помогает» — KPI считают
подтверждённые findings и сэкономленные часы, не логины. — протокол · пилот.

### 6.9. Критерии оценивания (вместо лозунгов)

**Accuracy:** precision/recall/F1 per-discipline и per-error-class на frozen
customer corpus; ≥2 adjudicators; agreement-артефакт (Cohen κ, Krippendorff
α); enforced gate κ≥0.60, α≥0.67; методическая цель κ>0.80 (НЕ enforced);
adjudication protocol; report hash + machine fingerprint; publication gate.
Разведено: enforced code gate (0.60/0.67) ≠ methodological target (0.80) ≠
publication threshold (полный набор условий гейта).

**Geometry:** finite coordinates, known units, complete primitives, closed
contour, no self-intersection, non-degenerate area; INVALID/INCOMPLETE/
UNIT_UNKNOWN никогда не читаются как «ноль нарушений» (no silent zero).

**Coverage:** CHECKED_OK ⇔ источник реально обработан + processing evidence
+ scope не конфликтует с findings + off-sheet учтён + лист без false clean +
coverage не меняет verdict.

**SLA:** ≤30 минут только на согласованном эталонном пакете; evidence:
package hash/manifest, files, IFC size, PDF pages, drawings, calc count,
machine, Python, dependency lock, cold/warm, extras, stage timings, timeout
behaviour.

**Remarks:** RU/EN; factual grounding; ссылка на источник/лист/правило/
evidence; severity; expert acceptance; запрещены галлюцинированные пункты
норм и неподтверждённые юридические заявления.

**BCF:** valid ZIP → structural → dual-consumer → independent CDE import →
round-trip → API push; до T2 запрещены «CDE-ready» и «CDE interoperable».

### 6.10. Фазность MVP и границы поставки

| Фаза | Содержимое | Статус |
|---|---|---|
| MVP | IFC, IDS, cross-doc, generic clash, OCR baseline, template remarks, HTML/JSON, BCF ZIP, browser review, provenance, capability honesty, fail-closed профили | done (fixture) |
| P0 | multipart upload, remarks panel, RU/EN, HITL events, ACL, review shell | done |
| P1 | norm packs, section pairing, coverage evidence, revision diff, drawing quality gate, region assessment, deterministic geometry core, precision harness | ядро done; хвосты: ТР-223/224/233/242/322/402 |
| P2 | DXF/CAD adapter продуктово, licensed DWG (при legal-одобрении), deeper OCR, region detector, VLM advisory, quantity/space measurement, geometry-to-source binding | planned |
| P3 | LLM remarks, IDS-assist, norm retrieval, RASE, hybrid routing live, MCP/tool orchestration, HITL promotion | planned (foundation есть) |
| P4 | customer corpus, accuracy publication, system-aware MEP, space efficiency, CDE import proof, adoption/money KPI | needs customer |

P2/P3/P4 не объявляются готовыми на основании
TARGET_HYBRID_ARCHITECTURE_TZ_2026.md — это design proposal.

### 6.11. Требования к коду и сборке

Python 3.12+/FastAPI; ruff format+check, mypy strict, pytest (1536+ функций),
vitest; hashed locks `--require-hashes`; SHA-pinned Actions; локальный
quality gate до пуша; single-author commit policy; Docker + compose
production.

### 6.12. Образ финального решения

Backend API (25 маршрутов) + browser review shell (IFC viewer + 2D overlay +
remarks + HITL) + CLI evidence-инструменты (bundle, SLA, coverage export,
benchmark rails) + артефакты честности (Claims Lock, BCF ladder, матрицы).

### 6.13. Требования к презентации

Показывать: живой analyze на representative-паке; coverage карту с
NOT_CHECKED-зонами; NOT_VERIFIED MEP как фичу честности; импорт BCF ZIP в два
consumer'а; NO_GO-чекпоинт как зрелость Red Team-процесса. Не показывать:
fixture-SLA как «30 минут»; fixture-F1 как «точность продукта».

### 6.14. Требования к сопроводительной документации

Tier-0 индекс; ТЗ v3 (этот документ); Claims Lock v2; матрицы §7–§10; pilot
protocol; REPRODUCIBILITY; ADR-001/002; threat model; KNOWN_BUGS
(проверено 2026-07-30: `stub_ifc_knowledge_graph.py` присутствует, STUB-IFC-KG-001 корректен).

---

## 7. КОНКУРЕНТНАЯ МАТРИЦА

Оговорка: данные о конкурентах — из их публичных заявлений; их числа НЕ
проверены независимо и на веру не принимаются (симметрично нашему принципу).

| Возможность | AeroBIM | Peer A (zone/OCR) | Peer B (DWG/CV) | Peer C (RF cloud stack) | Peer D (field pilots) | Доказательство AeroBIM | Риск заявления peer |
|---|---|---|---|---|---|---|---|
| DWG | нет (честно MISSING) | заявляет | заявляет (сильно) | заявляет | n/a | honesty never OK | лицензия CAD-stack (ODA/Teigha) |
| DXF | partial (ezdxf optional) | ? | заявляет | ? | n/a | фикстуры TEXT/MTEXT | unit ambiguity |
| Vector PDF | текст детерминир. (PyMuPDF) | заявляет | заявляет | заявляет | ? | tests | качество извлечения геометрии |
| IFC | ядро 2x3/4/4x3 | ? | слабо | заявляет | нет | fixtures + tests | глубина валидации |
| IDS 1.0 | да | нет данных | нет данных | нет данных | нет | IfcTester | — |
| BCF | 2.1/3.0 ZIP T1 | нет данных | нет | нет данных | нет | XSD-артефакт 25.07 | CDE-совместимость не доказана ни у кого |
| Norm packs | synthetic + approval-контракт | происхождение norm logic? | ? | ? | сильно (СП/ГОСТ/СанПиН/ПУЭ) | schema + intake gate | provenance/versioning их базы |
| Geometry детерминир. | core P2 (статусы доверия) | ? | сильно (площади/проходы/коридоры/коллизии) | ? | n/a | geometry.py + regression | self-intersection/unit handling? |
| VLM/CV | missing (честно) | сильно заявляет | заявляет | заявляет | n/a | `cv_human_level=missing` | доказательность CV-метрик |
| OCR | baseline optional | сильно | ? | заявляет (сканы) | ? | RapidOCR + fail-closed | качество на плохих сканах |
| MEP | NOT_VERIFIED (RT-003) | ? | коллизии заявляет | ? | n/a | fail-closed probe | co-presence ≠ connection |
| Расчёты | сверка (не корректность) | ? | ? | заявляет | сметы/ВОР/ССР | OpenRebar digest | ответственность за LLM-вывод |
| Provenance | обязателен (persist reject) | ? | журнал проверки | ? | ? | tests | — |
| Deterministic verdict | да (ADR-001) | неясно | LLM-involved? | неясно | закрытый контур | OFF==ON тест | LLM в вердикте — риск |
| Customer data | контур/air-gapped design | ? | ? | Yandex Cloud | закрытый контур | hybrid fail-closed | 152-ФЗ аудита публично нет ни у кого |
| On-prem / air-gapped | local-only default | ? | ? | облако | вероятно да | ModelRouter config | — |
| Reproducibility | FAIR, frozen tag, hashes | нет | нет | нет | нет | REPRODUCIBILITY-2026 | их метрики извне невоспроизводимы |
| Customer metrics | НЕТ (честно) | «2 дня → 30 минут» | «>90%» | live prototype | пилоты/договоры | — | принимать на веру нельзя |
| CDE | not verified | ? | нет | ? | ? | STATUS.json пуст | «CDE-ready» без import-proof |
| HITL | state machine + KPI | ? | ? | ? | ? | tests | модель ответственности |

Geometry core — честный конкурентный P2-ответ peer-классу «DWG/CV-first»: детерминированные
измерения со статусами доверия. **Но это не DWG/DXF ingestion** — парсер
остаётся отдельным адаптером за портом (P2, лицензия).

**Три честных преимущества AeroBIM:** (1) детерминированный fail-closed
вердикт (ADR-001, OFF==ON-доказательство); (2) evidence-инфраструктура
(Claims Lock, κ/α-гейты, BCF-лестница, coverage, provenance) — уникальна
среди четырёх конкурентов; (3) открытый openBIM-стек + воспроизводимость
(FAIR, frozen tags, hashed locks).

**Три честные слабости:** (1) нет DWG и human-level CV (ось peer «DWG/CV-first»);
(2) ноль customer-метрик и трекшна (ось peer «field-pilot traction»);
(3) MEP system-aware не поставлен.

**Закрыть до КТ#2:** representative-пак SLA с манифестом (ТР-502);
Claims Lock v2 + синхронизация документов (ТР-401/402); adversarial drawing
фикстуры + демо anti-bad-scan (ТР-233).

**Честно оставить в pilot/P2+:** DXF/DWG продуктовый ingestion (P2, legal);
VLM advisory и LLM remarks (P3, за DeterminismGate); system-aware MEP +
space efficiency (P4, RT-003).

---

## 8. CLAIMS LOCK v2 (проект — на замену CLAIMS_LOCK_2026_07_17)

### Запрещено до доказательств

- «точность >90%» / любые проценты product accuracy (RT-001);
- «native DWG» / «DWG-ready» / `dwg_supported` / «анализирует DWG»;
- «MEP delivered» / «system-aware MEP clash» как возможность (RT-003);
- «независимая проверка корректности расчётов»;
- «CDE-ready BCF» / «CDE interoperable» (до T2: log+screenshot+hashes);
- «полное покрытие СП/ГОСТ» (RT-002);
- «customer SLA ≤30 минут» (только fixture_only до customer-пака);
- «human-level CV» / «система читает чертежи как инженер»;
- «production-ready» / «внешний академический аудит»;
- «автономная экспертиза» / «юридически значимый sign-off»;
- «zero data leakage» / «полное соответствие 152-ФЗ» без юр. аудита;
- **[НОВОЕ]** «geometry core анализирует DWG/DXF» — он работает только над
  извлечёнными примитивами;
- **[НОВОЕ]** «coverage подтверждает корректность документации» — только
  покрытие проверки; **[НОВОЕ]** «coverage влияет на вердикт» — ложь в обе
  стороны (не влияет и не должен);
- **[НОВОЕ]** «revision diff показывает исправленные замечания» —
  `no_longer_reported` ≠ resolved;
- **[НОВОЕ]** «маскирование = анонимизация» / «hybrid-контур делает облако
  безопасным для клиентских данных».

### Разрешено (с указателями на evidence)

- «deterministic acceptance assistant (Shared-gate, ADR-001)»;
- «fixture-proven» + pack + commit SHA; «customer evidence pending»;
- «advisory-only AI, verdict-neutral (OFF==ON)»;
- «generic IFC clash при установленном ifcclash»;
- «calculation match / сверка (не корректность)»;
- «BCF ZIP structural export (T1); CDE import not verified»;
- «OCR baseline; деградация fail-closed»;
- **[НОВОЕ]** «deterministic 2D geometry core over extracted primitives со
  статусами доверия OK/INCOMPLETE/UNIT_UNKNOWN/INVALID»;
- **[НОВОЕ]** «coverage evidence: карта CHECKED_OK/NOT_CHECKED по processing
  evidence, verdict-neutral, read-only endpoint»;
- **[НОВОЕ]** «revision diff: verdict-neutral дельта findings,
  delimiter-proof keys»;
- «expert remains accountable»; «checkpoint NO_GO — признак зрелого Red Team
  процесса».

---

## 9. МАТРИЦА ЗАВИСИМОСТЕЙ ОТ ЗАКАЗЧИКА

| ID | Что нужно от Самолёта | Блокирует | Без этого невозможно | Срок |
|---|---|---|---|---|
| D-01 | Размеченный корпус документов + NDA | RT-001 | product accuracy, per-discipline метрики | Week 1 пилота |
| D-02 | ≥2 независимых adjudicator'а со стороны заказчика | RT-001 | publishable precision (κ/α гейт) | Week 1–2 |
| D-03 | Утверждённый нормопак (approval-объект + hash) | RT-002 | нормативная проверка как claim | Week 1–3 |
| D-04 | Federated IFC + подписанный scope memo + clearance matrix | RT-003 | system-aware MEP | Iteration 2 |
| D-05 | Доступ к CDE-песочнице + совместный импорт BCF | BCF T2 | «CDE interoperable» | Week 1 |
| D-06 | Согласованный эталонный пакет для SLA | SLA claim | «≤30 минут» как договорная метрика | Week 1 |
| D-07 | История типовых ошибок QA | R14 | наполненный error catalog | Iteration 2 |
| D-08 | Интерпретация «коллизии» (3D vs логические) | R5 | правильный default clash-политики | Week 1 |
| D-09 | Требования ИБ (OIDC-провайдер, retention, локализация) | POST-05 | production-профиль аутентификации | до КТ#3 |
| D-10 | Спонсор пилота — владелец CDE import proof | T2/T4 | подписанные артефакты приёмки | постоянный |

---

## 10. МАТРИЦА ТРАССИРУЕМОСТИ (R задачи 07 → ТР → код → evidence)

| R (task page) | ТР | Модуль | Evidence | Статус |
|---|---|---|---|---|
| R1 2D drawings | ТР-231…233 | drawing adapters, region_* | fixtures + tests | fixture |
| R2 BIM | ТР-201/202 | IfcOpenShell/IfcTester | pytest | fixture |
| R3 ТЗ+расчёты | ТР-203/204 | extractor, quantity | F1-gate ≥0.70 | fixture |
| R4 нормы | ТР-321…324 | norm packs | schema+intake | needs customer (RT-002) |
| R5 коллизии | ТР-311/312 | IfcClash generic | opt-in `.[clash]` | fixture / MEP blocked |
| R6 размеры/площади | ТР-204, ТР-211…214 | quantity + geometry.py | regression | fixture |
| R7 логика/пропуски | ТР-202/203 | IDS + operators | pytest | fixture |
| R8 подсветка | — (P0 done) | problem_zone, overlay | live smoke | fixture |
| R9 приоритизация | ТР-703 | review_priority.py | tests | fixture |
| R10 комментарии | ТР-702 | TemplateRemarkGenerator RU/EN | tests | fixture |
| R11 ускорение ревью | ТР-805 | KPI protocol | пилот | needs customer |
| R12 подотчётность | ТР-701 | HITL machine | tests | done |
| R13 MVP+визуализация | — | API+frontend | vitest 29 | done |
| R14 каталог ошибок | D-07 | map_typical_errors | scaffold ≥20 | partial |
| R15 SLA ≤30 мин | ТР-502 | measure_package_sla | fixture-only | needs customer |

---

## 11. ПЛАН ДО КТ#2 (инженерно управляемое)

1. **Claims Lock v2** (§8) + CI-grep гейт — закрывает F-01 (ТР-401).
2. **Representative-пак SLA**: собрать пак реалистичного размера, прогнать
   core/+raster/+clash, cold+warm, опубликовать манифест и stage timings
   (ТР-502) — закрывает F-02.
3. **RESERVED_PORTS + тест синхронизации** портов/токенов; README-числа из
   генератора (ТР-103/302) — закрывает F-03 (F-04 отозвана после верификации).
4. **Coverage snapshot в evidence bundle** + empty-source тест (ТР-223/224).
5. **Adversarial drawing фикстуры** (штамп/рукопись/низкий DPI) + демо
   anti-bad-scan (ТР-233).
6. **Intake-тест дубликатов ревизий** (ТР-242) и reject-тест synthetic
   pack≠approved (ТР-322).
7. Демо-сценарий защиты: живой analyze → coverage → BCF → HITL →
   NOT_VERIFIED MEP как честность.

## 12. ПЛАН ДО КТ#3 (зависит от заказчика — см. §9)

1. Интейк корпуса (D-01) → frozen split → dual adjudication → κ/α артефакт →
   первый publishable precision-отчёт (RT-001).
2. Нормопак с approval-объектом (D-03) → RT-002 закрыт.
3. CDE import proof: log + screenshot + hashes (D-05) → BCF T2.
4. SLA на согласованном пакете заказчика (D-06) → customer_measurable.
5. POST-05 OIDC BFF либо письменные компенсирующие меры (D-09, ТР-602).
6. MEP: federated IFC + memo + matrix (D-04) → снятие RT-003 (или честный
   перенос в P4).
7. KPI пилота: FP-rate, triage-время, подтверждённые findings, сэкономленные
   часы (воронка пользы, ТР-805).

---

## 13. КРИТИЧНЫЕ ВОПРОСЫ К ЗАКАЗЧИКУ (≤10)

1. Какой состав эталонного пакета для SLA ≤30 мин (число файлов, размер IFC,
   страниц PDF, дисциплины) вы готовы согласовать письменно?
2. Какие 10–20 нормативных правил (СП/ГОСТ, разделы) приоритетны для пилота,
   и кто со стороны Самолёта утвердит нормопак (ФИО, роль, дата)?
3. Кто два независимых adjudicator'а для разметки корпуса и готовы ли вы к
   протоколу κ/α (двойная разметка + арбитраж)?
4. Какой CDE используется (Exon/Tangl/BIM 360/иной) и можно ли получить
   песочницу для импорта BCF на Week 1?
5. «Коллизии» в вашей формулировке — это 3D-геометрия (IfcClash), логические
   расхождения документов, или оба класса? Что важнее для пилота?
6. Доля документации, доступной в IFC vs только DWG/PDF-сканы? Готовы ли вы
   поставлять DWG→PDF/IFC экспорт как derived input?
7. Требования ИБ: допустим ли облачный контур с маскированием для
   не-критичных текстов, или пилот строго on-prem/air-gapped?
8. Какой OIDC-провайдер и модель доступа экспертов (SSO, роли) — нужен ли
   полный BFF к началу пилота?
9. Кто владелец решения по finding'ам (главный эксперт/ГИП) и какой ваш
   текущий базовый показатель времени проверки комплекта (для KPI-дельты)?
10. Передадите ли историю типовых ошибок QA (R14) и в каком формате?

---

## 14. ФИНАЛЬНЫЙ VERDICT

**Checkpoint: `NO_GO`**

Причины:
1. **RT-001 OPEN** — нет customer-корпуса: ни одна метрика точности не
   является product accuracy (все fixture, macro_f1=0.86 непереносим).
2. **RT-002 OPEN** — нет утверждённого заказчиком нормопака: нормативная
   проверка остаётся демонстрацией на синтетике.
3. **RT-003 OPEN** — MEP system-aware clash не runtime capability
   (Unconfigured → NOT_VERIFIED; wiring ≠ capability).

**Что реально готово:** детерминированное ядро IFC/IDS/cross-doc/quantity +
fail-closed профили + honesty API + coverage/revision diff/geometry core +
HITL + ACL/SSRF/jail + BCF T1 + 1536 тестов, зелёный CI.

**Что можно показывать:** живой analyze на фикстурах с явными статусами;
coverage карту; BCF ZIP + dual-consumer; NOT_VERIFIED как механизм честности;
Red Team процесс (RTATOM волны, hyperdeep) как дифференциатор зрелости.

**Что нельзя обещать:** >90%, DWG, MEP delivered, CDE-ready, независимую
корректность расчётов, customer SLA ≤30 мин, human-level CV,
production-ready, юридически значимый sign-off.

**Что блокирует GO:** исключительно customer evidence (D-01…D-06) — это
управляется контрактацией пилота, а не кодом.

**Что сделать первым:** (1) Claims Lock v2 + CI-гейт формулировок;
(2) representative-пак SLA с манифестом вместо 1096-байтового;
(3) выслать заказчику список из §13 — все три блокера начинаются с его
данных.

Публичный NO_GO при отсутствии customer evidence — признак зрелого Red
Team-подхода, а не слабости проекта. Формулировка не смягчается.
