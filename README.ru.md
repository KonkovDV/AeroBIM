# AeroBIM

[English version](README.md)

[![CI](https://github.com/KonkovDV/AeroBIM/actions/workflows/ci.yml/badge.svg)](https://github.com/KonkovDV/AeroBIM/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> ## Checkpoint: `NO_GO`
>
> Samolet TechLab Task 07 **не** готов к customer sign-off. Открытые блокеры:
> **RT-001** (корпус точности), **RT-002** (утверждённый нормативный пакет), **RT-003** (federated MEP-скоуп) —
> см. [`audit/reports/CRITICAL_BLOCKERS.md`](audit/reports/CRITICAL_BLOCKERS.md).
> SSOT формулировок: [`audit/reports/CLAIMS_LOCK_2026_07_17.md`](audit/reports/CLAIMS_LOCK_2026_07_17.md) ·
> eng freeze: [`audit/reports/CLAIMS_LOCK_2026_07_31.md`](audit/reports/CLAIMS_LOCK_2026_07_31.md) ·
> verified vs planned: [`docs/pilot-claim-boundary-2026.md`](docs/pilot-claim-boundary-2026.md) ·
> **Eng-статус авг 2026:** [`docs/ENGINEERING_STATUS_2026_08.md`](docs/ENGINEERING_STATUS_2026_08.md) ·
> карта docs: [`docs/TIER0_INDEX.md`](docs/TIER0_INDEX.md) ·
> владение вердиктом: [`docs/architecture/ADR-001-verdict-ownership-2026.md`](docs/architecture/ADR-001-verdict-ownership-2026.md).
> Запрещено до доказательств: точность >90%, DWG-ready, MEP delivered, CDE-ready BCF, корректность расчётов.
>
> **Инженерная готовность выросла (2026-07 → 2026-08)** без закрытия customer-блокеров:
> LIC-001 Option B; P2-04 / P2-02 honesty; Docker offline; **P0 eng-пакет WP-01…08**
> (baseline, Hybrid advisory pre-gate, envelope подписи, norm pack v2, completeness,
> open-corpora n=7, quality protocol interim 0.60, sync README/baseline) —
> [`docs/ENGINEERING_STATUS_2026_08.md`](docs/ENGINEERING_STATUS_2026_08.md) ·
> Red Team [`docs/quality/RED_TEAM_P0_ROLLUP_2026_08_02.md`](docs/quality/RED_TEAM_P0_ROLLUP_2026_08_02.md).
> Fixture GO ≠ Checkpoint GO.

Открытый **ассистент критериев приёмки** для openBIM-комплектов (IFC + IDS + междокументные доказательства).

AeroBIM выполняет детерминированную проверку в логике Shared-gate (рамка ISO 19650: доказательства для состояния *Shared*, не контрактная авторизация *Published*). Сводка объединяет IFC, IDS, чертежи и тексты расчётов с явной честностью capabilities, provenance findings и экспортом BCF **ZIP**. Независимый импорт в CDE и customer accuracy остаются **вне утверждений**, пока нет доказательств. Архитектура: [`docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md`](docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md).

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

Ключевые env (фрагмент): `AEROBIM_PDF_BACKEND=pdfium` (default), `AEROBIM_MEP_AABB_FILTER=true` (optional AABB; всё ещё `geometry_verified=False`). Advisory LLM (opt-in): `AEROBIM_LLM_LOCAL_ENABLED` + unversioned `gpt://…/qwen3.6-35b-a3b` + `AEROBIM_LLM_BUDGET_LEDGER` + лимиты `MAX_TOKENS_PER_RUN=100000` / `MAX_TOKENS_PER_DAY=300000` (карта привязана → нет `TRIAL_EXPIRED`; `enable_thinking=false` обязателен для 5.1) — полная таблица в [README.md](README.md) Configuration. Живой inventory: **48 Protocol ports / 67 adapter modules / 58 DI tokens**.

## Git-коммиты

```bash
git config core.hooksPath .githooks
powershell -ExecutionPolicy Bypass -File scripts/git_commit.ps1 -Message "docs: ..."
```

<!-- AEROBIM_RUNTIME_BASELINE:BEGIN -->
<!-- regenerated by: python -m aerobim.tools.export_runtime_baseline -->
Backend src ~54757 LOC; tests ~38800 LOC; 1863+ test functions; extraction macro_f1=0.8600000000000001 (fixture corpus; not product accuracy)
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
