# AeroBIM

[English version](README.md)

[![CI](https://github.com/KonkovDV/AeroBIM/actions/workflows/ci.yml/badge.svg)](https://github.com/KonkovDV/AeroBIM/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**AeroBIM** — открытый ассистент критериев приёмки для openBIM-комплектов: помогает эксперту найти расхождения между BIM-моделью, чертежами, ТЗ и правилами **до** стройки.

## Задача с примером

На листе PDF в ведомости площадей — одно число, в IFC у стены с тем же GUID — другое. Файлы по отдельности «зелёные»; ошибка видна только при сопоставлении. AeroBIM поднимает находку с provenance до листа и до GUID, оставляет вердикт эксперту и не подписывает Shared→Published.

## Что уже работает

Project-package analyze; IFC / IDS / cross-doc; детерминированный Shared-gate `summary.passed` (fail-closed); provenance; структурный BCF ZIP; HITL; Docker offline-bundle; CI. Карта и таблица возможностей — в разделе **Техническая глубина**. Метрики LOC/тестов — [runtime baseline](docs/evidence/runtime-baseline-latest.json).

## Где применимо

Проверка комплекта до стройки: экспертиза / ГИП / контроль качества документации; стык модели, чертежей и требований. Не замена СОД и не полевой журнал дефектов. Контур «Самолёта» и пилотная рамка — [`docs/docs.md`](docs/docs.md) · [`docs/samolet.md`](docs/samolet.md).

Материалы для жюри / трекера (без коммерческой кухни): [`docs/docs.md`](docs/docs.md) · [`docs/ENGINEERING_STATUS_2026_08.md`](docs/ENGINEERING_STATUS_2026_08.md) · критерии мышления жюри МИК (не подача «Новатор» 2026): [`docs/partners/NOVATOR_JURY_PACK_2026_08.md`](docs/partners/NOVATOR_JURY_PACK_2026_08.md).

## Статус готовности

> **Checkpoint: `NO_GO`** — внутренний статус готовности к *подписанию у заказчика*, **не** оценка «система не работает».  
> По-русски: код и fixtures есть; **нет** утверждённого корпуса заказчика, норм-пакета и federated MEP-scope — без них нельзя честно снять checkpoint.  
> Открыты: **RT-001** (точность на customer corpus), **RT-002** (норм-пак), **RT-003** (federated MEP) — [`audit/reports/CRITICAL_BLOCKERS.md`](audit/reports/CRITICAL_BLOCKERS.md).  
> Запрещено до доказательств: точность >90%, DWG-ready, MEP delivered, CDE-ready BCF, корректность расчётов.  
> SSOT: [Claims Lock](audit/reports/CLAIMS_LOCK_2026_07_17.md) · [eng status авг 2026](docs/ENGINEERING_STATUS_2026_08.md) · [ADR-001](docs/architecture/ADR-001-verdict-ownership-2026.md).  
> Инженерная готовность выросла (WP-01…08 и др.) **без** закрытия customer-блокеров — Fixture GO ≠ Checkpoint GO.

AeroBIM выполняет детерминированную проверку в логике Shared-gate (рамка ISO 19650: доказательства для *Shared*, не контрактная авторизация *Published*). Независимый импорт в CDE и customer accuracy — **вне утверждений**, пока нет доказательств. Архитектура: [`docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md`](docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md).

## Техническая глубина

### Проблема (развёрнуто)

Одна и та же величина живёт в модели, на листе PDF, в ТЗ и в таблице площадей. Файлы по отдельности выглядят корректно; ошибка всплывает при сопоставлении — часто уже на площадке. Система сопоставляет IFC / IDS, чертежи и тексты требований; показывает источники; формирует проект замечания; оставляет решение эксперту.

## Карта статуса (честно)

| Корзина | Смысл |
|---|---|
| **Работает** | Доказано на fixtures / репозитории |
| **Экспериментально** | Код есть; не customer-proven |
| **Доступно (eng)** | Инженерно готово; не customer GO |
| **План** | Отложено (Wave 2+) |
| **Нужен заказчик** | RT-001/002/003 — checkpoint **NO_GO** |
| **Не заявляется** | Запрещённые формулировки до dual evidence |

**Работает:** analyze project-package; IFC/IDS/cross-doc; Shared-gate `summary.passed` ([ADR-001](docs/architecture/ADR-001-verdict-ownership-2026.md)); fail-closed pilot/production; ACL 404; SSRF; provenance; BCF ZIP 2.1/3.0 structural; HITL; CLI `export_evidence_bundle`; **annotation claimed-GUID presence** (P2-04); **core PDF через pypdfium2/pdfminer** (LIC-001 Option B); **HybridRouteGate pre-gate** (WP-02); **envelope подписи** (WP-03 ENG_PARTIAL); **norm pack v2** (WP-04); **completeness inventory** (WP-05); **open-corpora profiles** (WP-06, только regression/timing); **протокол измерения качества** (WP-07, Wilson; interim 0.60); Docker offline-bundle smoke; счётчики pytest / vitest — SSOT в [runtime baseline](docs/evidence/runtime-baseline-latest.json).

**Экспериментально:** OpenCDE BCF API push; optional clash/OCR; IFC KG scaffold; MEP federated ENG_FIXTURE graph + AABB broadphase (capability остаётся `NOT_VERIFIED`).

**Доступно (eng):** `PackageOutcome` на `summary.outcome`; run manifest + reproducibility hash; **Hybrid AI + WP-02 `HybridRouteGate` advisory pre-gate** на Analyze (verdict-neutral, OFF==ON, **никогда** не ставит `summary.passed`); masking ≠ anonymity; Checkpoint **NO_GO**.

**План:** расширение Stage-3 полей finding; profiling-driven performance; customer-gated RT-001/002/003.

**Нужен заказчик:** RT-001 corpus · RT-002 нормы · RT-003 MEP ([CRITICAL_BLOCKERS](audit/reports/CRITICAL_BLOCKERS.md)).

**Не заявляется:** точность >90%; SLA ≤30 мин на customer; native DWG; MEP delivered; корректность расчётов; CDE-ready BCF; bare-metal offline без Docker; AABB/connects = verified geometric clash. См. [capability-claim-matrix](docs/capability-claim-matrix-2026.md) · [PROJECT_STATUS_AUDIT](docs/PROJECT_STATUS_AUDIT_2026.md) · [ENGINEERING_STATUS_2026_08](docs/ENGINEERING_STATUS_2026_08.md) · [pilot-protocol](docs/pilot-protocol-samolet-2026.md).

## Основные возможности

Статусы ниже — уровень **репозиторий / fixture**, если не указано иное.

| Возможность | Статус | Уровень доказательств | Примечание |
|---|---|---|---|
| Проверка свойств/величин IFC (IfcOpenShell) | Доступно | fixture | IFC2x3 / IFC4 / IFC4x3 |
| IDS 1.0 (IfcTester) | Доступно | fixture | Fail-closed при запросе без валидатора |
| Междокументные противоречия | Доступно | fixture | Таксономия `ConflictKind` (подмножество) |
| Аннотации чертежа ↔ IFC | Доступно | fixture | Claimed GUID → `ifc_guid` только после presence в spatial index (P2-04); не human-adjudicated |
| Допуски ISO 12006-3 (ε) | Доступно | fixture | — |
| Извлечение требований (regex) | Доступно | fixture | Не LLM-контур подписания |
| Бенчмарк извлечения RU AEC | Доступно | fixture | macro_f1 ≠ product accuracy |
| ISO 19650-lite метаданные | Доступно | fixture | Не продукт CDE |
| Коллизии (IfcClash) | Optional extra | optional-extra | `.[clash]`; при `require_clash` SKIPPED→FAILED |
| Честность capabilities | Доступно | fixture | FAILED блокирует `passed`; `/v1/system/capabilities` |
| Provenance finding | Доступно | fixture | Persist reject без `finding_id`/`evidence_refs` |
| Tenant/object ACL | Доступно | fixture | Principal + `tenant_id` отчёта |
| Экспорт BCF 2.1/3.0 ZIP | Доступно (T0/T1) | fixture | Структурный ZIP **AVAILABLE**; **CDE import NOT_VERIFIED (T2)** |
| OpenCDE BCF API push | Foundation | experimental | Не заменяет T2 |
| Детерминированный PDF (pypdfium2 + pdfminer) | Доступно | core | LIC-001 Option B; `AEROBIM_PDF_BACKEND=pdfium` |
| Опциональный PyMuPDF | Optional extra | `pdf-agpl` | AGPL/Artifex; **не** в runtime lock/Docker |
| OCR (RapidOCR) | Optional extra | optional-extra | `.[raster]`; EI OCR-aware PARTIAL |
| Extraction integrity | Доступно | fixture | Text-layer + optional OCR disagreement; не product visual integrity |
| Vitest review-shell | Зелёный в CI | release-readiness | **29** passed (`frontend` CI job) |
| DWG native | Missing / Failed | — | Fail-closed; never OK; PDF/IFC = только derived input |
| DXF (CadModelIngestor) | Partial / Not verified | fixture | Optional ezdxf; ≠ поддержка DWG |
| CV human-level | Missing | — | OCR degrade ≠ VLM |
| MEP system-aware clash | Not verified / blocked | fixture_only | ENG_PARTIAL: edge_kinds + AABB; всегда `geometry_verified=False`; RT-003 OPEN |
| Offline Docker image-track | Доступно | eng | `offline_bundle` smoke; bare-metal **DEFERRED** |
| Корректность расчётов | Not implemented | — | сверка источников, не расчётный решатель |
| Hybrid AI + advisory pre-gate (WP-02) | Доступно (eng) | fixture | Gate до advisory observations; OFF==ON для `summary.passed`; Checkpoint NO_GO |
| Envelope подписи (WP-03) | ENG_PARTIAL | fixture | Hash/roles; trust_chain NOT_VERIFIED — никогда «УКЭП проверена» |
| Norm pack v2 (WP-04) | Доступно (eng) | fixture | RASE + journal; RT-002 OPEN |
| Completeness inventory (WP-05) | Доступно (eng) | fixture | Soft opt-in; не native DWG; не PP-87 |
| Open corpora (WP-06) | Доступно (eng) | fixture/open | Fixture n=7 + BSI IDS n=290 (CC BY-ND); CI smoke — не product accuracy |
| Quality protocol (WP-07) | Доступно (eng) | protocol | Wilson P/R + planner; interim 0.60; никогда >90% |
| OIDC BFF Phase 2 (POST-05) | NOT_IMPLEMENTED | design+stub | login/callback/logout + CSRF; без production session |
| BCF T2 CDE import | NOT_VERIFIED | template | Checklist готов; нужен live CDE evidence |
| Точность >90% / утверждённые нормы | Blocked | customer | См. Claims Lock |

## Совместимость с IFC

| Релиз IFC | Схема | Поддержка | Примечание |
|---|---|---|---|
| IFC2x3 | ISO 16739:2005 | Основной | Наиболее распространён в эксплуатации |
| IFC4 (ADD2) | ISO 16739-1:2018 | Основной | Нормализация имён Pset и единиц |
| IFC4x3 | ISO 16739-1:2024 | Основной | То же ядро проверки |

Подробнее: [docs/ifc-compatibility-matrix.md](docs/ifc-compatibility-matrix.md).

## BCF: лестница доказательств

| Уровень | Статус | Примечание |
|---|---|---|
| BCF 2.1 ZIP | Стабильный default | `/export/bcf` |
| BCF 3.0 ZIP | Экспериментально | `?version=3` |
| T1 структура + dual consumers | Доказано | [`audit/evidence/bcf-structural-handoff-2026-07-25.json`](audit/evidence/bcf-structural-handoff-2026-07-25.json) |
| OpenCDE API push | Foundation | Не заменяет T2 |
| T2 импорт в CDE | **НЕ ДОКАЗАНО** | [`audit/evidence/cde-import-proof/STATUS.json`](audit/evidence/cde-import-proof/STATUS.json) |

Запрещено до T2: «BCF готов к CDE».

## Быстрый старт

```bash
git clone https://github.com/KonkovDV/AeroBIM.git
cd AeroBIM/backend

python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

pip install -e ".[dev,raster]"
# pip install -e ".[clash]"
# pip install -e ".[docling]"
# pip install -e ".[enterprise]"
# pip install -e ".[pdf-agpl]"   # optional legacy PyMuPDF only

pytest tests -q
python -m aerobim.tools.evaluate_extraction --min-macro-f1 0.70
python -m aerobim.tools.seed_smoke_report
python -m aerobim.main
# http://127.0.0.1:8080/health
```

## Проверки перед push

```bash
cd AeroBIM/backend
python -m ruff format --check src tests
python -m ruff check src tests
python -m mypy src
pytest tests -q
```

## Бенчмарки и доказательства

```bash
cd backend
python -m aerobim.tools.benchmark_project_package --iterations 1 --warmup-iterations 0
python -m aerobim.tools.measure_package_sla --corpus-kind fixture
python -m aerobim.tools.verify_bcf_structural_handoff
python -m aerobim.tools.export_runtime_baseline
python -m aerobim.tools.export_evidence_bundle \
  --pack ../samples/benchmarks/project-package-techlab-demo.json \
  --output ../artifacts/evidence-bundle/techlab-demo

# P2-04 wall-guid presence demo (fixture GO pin)
python -m aerobim.tools.export_evidence_bundle \
  --pack ../samples/benchmarks/project-package-wall-guid-demo.json \
  --output ../artifacts/evidence-bundle/checkpoint2-wall-guid
```

| Тема | Документ |
|---|---|
| Claims lock | [audit/reports/CLAIMS_LOCK_2026_07_17.md](audit/reports/CLAIMS_LOCK_2026_07_17.md) |
| Eng freeze 2026-07-31 | [audit/reports/CLAIMS_LOCK_2026_07_31.md](audit/reports/CLAIMS_LOCK_2026_07_31.md) |
| Блокеры / NO_GO | [audit/reports/CRITICAL_BLOCKERS.md](audit/reports/CRITICAL_BLOCKERS.md) |
| Eng-статус авг 2026 | [docs/ENGINEERING_STATUS_2026_08.md](docs/ENGINEERING_STATUS_2026_08.md) |
| Граница утверждений | [docs/pilot-claim-boundary-2026.md](docs/pilot-claim-boundary-2026.md) |
| Capability × claim | [docs/capability-claim-matrix-2026.md](docs/capability-claim-matrix-2026.md) |
| License policy (LIC-001) | [docs/license-policy-2026.md](docs/license-policy-2026.md) |
| Offline (Docker) | [docs/offline-deployment-2026.md](docs/offline-deployment-2026.md) |
| MEP gap | [docs/roadmap/MEP_SYSTEM_CLASH_GAP_2026_07.md](docs/roadmap/MEP_SYSTEM_CLASH_GAP_2026_07.md) |
| P2-02 geometry honesty | [docs/roadmap/P2_02_GEOMETRY_HONESTY_PLAN_2026_08.md](docs/roadmap/P2_02_GEOMETRY_HONESTY_PLAN_2026_08.md) |
| Checkpoint #2 pin | [docs/evidence/checkpoint2-evidence-bundle-latest.json](docs/evidence/checkpoint2-evidence-bundle-latest.json) |

Граница утверждений: [docs/pilot-claim-boundary-2026.md](docs/pilot-claim-boundary-2026.md) · [docs/capability-claim-matrix-2026.md](docs/capability-claim-matrix-2026.md) · [docs/pilot-protocol-samolet-2026.md](docs/pilot-protocol-samolet-2026.md).  
SSOT запрещённых формулировок: [audit/reports/CLAIMS_LOCK_2026_07_17.md](audit/reports/CLAIMS_LOCK_2026_07_17.md).  
Воспроизводимость: [docs/REPRODUCIBILITY-2026.md](docs/REPRODUCIBILITY-2026.md).

## Документация (пакет для жюри Техлаба)

На GitHub — **только** код и материалы для жюри Task 07 (+ curated eng status / Red Team summaries в `docs/quality/`). Служебные runbook’и, phase RT dumps и archive не публикуются.

| Нужно | Документ |
|------|----------|
| Старт | [`docs/TIER0_INDEX.md`](docs/TIER0_INDEX.md) · [`docs/README.md`](docs/README.md) |
| Eng-статус (авг 2026) | [`docs/ENGINEERING_STATUS_2026_08.md`](docs/ENGINEERING_STATUS_2026_08.md) |
| P0 Red Team rollup | [`docs/quality/RED_TEAM_P0_ROLLUP_2026_08_02.md`](docs/quality/RED_TEAM_P0_ROLLUP_2026_08_02.md) |
| Жюри (RU) | [`docs/docs.md`](docs/docs.md) |
| Стратегия × Самолёт | [`docs/samolet.md`](docs/samolet.md) |
| ТЗ Task 07 | [`docs/tz/README.md`](docs/tz/README.md) |
| Блокеры / NO_GO | [`audit/reports/CRITICAL_BLOCKERS.md`](audit/reports/CRITICAL_BLOCKERS.md) |
| Граница утверждений | [`docs/pilot-claim-boundary-2026.md`](docs/pilot-claim-boundary-2026.md) |
| Quality protocol (WP-07) | [`docs/pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md`](docs/pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md) |
| Open corpora (WP-06) | [`samples/benchmarks/open-corpora/README.md`](samples/benchmarks/open-corpora/README.md) |
| Архитектура | [`docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md`](docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md) |
| Hybrid AI (дизайн + финальный отчёт) | [`audit/reports/HYBRID_AI_FINAL_REPORT_2026_07_28.md`](audit/reports/HYBRID_AI_FINAL_REPORT_2026_07_28.md) |

## API (основное)

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/v1/system/capabilities` | Статическая honesty-поверхность |
| `GET` | `/health` | Readiness |
| `POST` | `/v1/analyze/project-package` | Мультимодальный анализ |
| `GET` | `/v1/reports/{id}/export/bcf` | Экспорт BCF ZIP |

Ключевые env (фрагмент): `AEROBIM_PDF_BACKEND=pdfium` (default), `AEROBIM_MEP_AABB_FILTER=true` (optional AABB; всё ещё `geometry_verified=False`). Advisory LLM (**только development**, opt-in): `AEROBIM_LLM_ADVISORY_ENABLED` (+ устаревший алиас `AEROBIM_LLM_LOCAL_ENABLED`) + pinned `AEROBIM_LLM_MODEL_REVISION` **или** unversioned `gpt://…/model` без `/latest` + `AEROBIM_LLM_BUDGET_LEDGER` + лимиты `MAX_TOKENS_PER_RUN` / `MAX_TOKENS_PER_DAY`. На профилях `samolet_pilot` / `production` внешний advisory egress **запрещён** fail-closed. Полная таблица — [README.md](README.md) Configuration. Живой inventory: **46 Protocol ports / 71 adapter modules / 59 DI tokens** (CI сверяет с `architecture_inventory` в runtime baseline, не руками).

<!-- AEROBIM_DOCUMENTED_ENV:BEGIN -->
AEROBIM_ALLOW_ANONYMOUS_DEV
AEROBIM_API_BEARER_TOKEN
AEROBIM_CLASH_AFFECTS_PASS
AEROBIM_CORS_ORIGINS
AEROBIM_CROSS_DOC_SEVERITY
AEROBIM_DB_URL
AEROBIM_DEBUG
AEROBIM_ENV
AEROBIM_HOST
AEROBIM_HYBRID_PROVIDER_CONFIG
AEROBIM_LLM_429_RETRIES
AEROBIM_LLM_ADVISORY_ENABLED
AEROBIM_LLM_ADVISORY_MAX_ISSUES
AEROBIM_LLM_ALLOWED_HOSTS
AEROBIM_LLM_API_KEY
AEROBIM_LLM_AUTH_SCHEME
AEROBIM_LLM_BASE_URL
AEROBIM_LLM_BUDGET_LEDGER
AEROBIM_LLM_BUDGET_TZ
AEROBIM_LLM_DATA_LOGGING_ENABLED
AEROBIM_LLM_FOLDER_ID
AEROBIM_LLM_LOCAL_ENABLED
AEROBIM_LLM_MAX_COMPLETION_TOKENS
AEROBIM_LLM_MAX_CONCURRENT
AEROBIM_LLM_MAX_TOKENS_PER_CALL
AEROBIM_LLM_MAX_TOKENS_PER_DAY
AEROBIM_LLM_MAX_TOKENS_PER_RUN
AEROBIM_LLM_MODEL
AEROBIM_LLM_MODEL_REVISION
AEROBIM_LLM_MODEL_SHA256
AEROBIM_LLM_PROVIDER
AEROBIM_LLM_RESPONSE_FORMAT_MODE
AEROBIM_LLM_SEND_SEED
AEROBIM_MAX_IFC_BYTES
AEROBIM_MEP_AABB_FILTER
AEROBIM_MEP_FEDERATED_SCOPE_PATH
AEROBIM_PDF_BACKEND
AEROBIM_PORT
AEROBIM_REPORT_TTL_DAYS
AEROBIM_REQUIRE_CLASH
AEROBIM_REQUIRE_MEP_SYSTEM_CLASH
AEROBIM_S3_ACCESS_KEY_ID
AEROBIM_S3_BUCKET
AEROBIM_S3_ENDPOINT_URL
AEROBIM_S3_PREFIX
AEROBIM_S3_REGION
AEROBIM_S3_SECRET_ACCESS_KEY
AEROBIM_SIGNOFF_PROFILE
AEROBIM_STORAGE_DIR
<!-- AEROBIM_DOCUMENTED_ENV:END -->

## Git-коммиты

```bash
git config core.hooksPath .githooks
powershell -ExecutionPolicy Bypass -File scripts/git_commit.ps1 -Message "docs: ..."
```

<!-- AEROBIM_RUNTIME_BASELINE:BEGIN -->
<!-- regenerated by: python -m aerobim.tools.export_runtime_baseline -->
Backend src ~55902 LOC; tests ~39284 LOC; 1882+ test functions; extraction macro_f1=0.8600000000000001 (fixture corpus; not product accuracy)
<!-- AEROBIM_RUNTIME_BASELINE:END -->

## Стек

- **Python 3.12+**, **FastAPI**, **Uvicorn**
- **IfcOpenShell** / **IfcTester** / **IfcClash** (buildingSMART)
- **web-ifc** + **Three.js** для browser IFC review
- **pypdfium2** + **pdfminer.six** для core PDF (LIC-001 Option B); опциональный **PyMuPDF** только через `pdf-agpl`
- **RapidOCR** при `.[raster]` (EI OCR-aware PARTIAL)
- **Docling** (optional)
- 5-слойная Clean Architecture, constructor DI, Protocol ports

## Лицензия

MIT для **кода AeroBIM**. Сторонние компоненты сохраняют свои лицензии:

- **pypdfium2** / **pdfminer.six** / **Pillow** — production PDF (permissive; см. inventory)
- **PyMuPDF** — dual AGPL-3.0 / Artifex commercial; **только optional `pdf-agpl`** (нет в runtime lock / Docker после LIC-001 Option B)
- **IfcOpenShell / IfcTester** — LGPL-3.0+
- **web-ifc** — MPL-2.0

Реестр: [`audit/dependency_license_inventory.json`](audit/dependency_license_inventory.json) · политика: [`docs/license-policy-2026.md`](docs/license-policy-2026.md).  
**Не юридическое заключение.** Не заявлять «весь продукт — MIT» без disclosure сторонних компонентов.
