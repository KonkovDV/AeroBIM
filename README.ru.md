# AeroBIM

[English version](README.md)

[![CI](https://github.com/KonkovDV/AeroBIM/actions/workflows/ci.yml/badge.svg)](https://github.com/KonkovDV/AeroBIM/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Открытый **ассистент критериев приёмки** для openBIM-комплектов (IFC + IDS + междокументные доказательства).

AeroBIM выполняет детерминированную проверку в логике Shared-gate (рамка ISO 19650: доказательства для состояния *Shared*, не контрактная авторизация *Published*). Сводка объединяет IFC, IDS, чертежи и тексты расчётов с явной честностью capabilities, provenance findings и экспортом BCF **ZIP**. Независимый импорт в CDE и customer accuracy остаются **вне утверждений**, пока нет доказательств.

> **Checkpoint:** статус Samolet TechLab Task 07 — **`NO_GO`**, пока нет customer corpus, утверждённого нормативного пакета и federated MEP-скоупа ([RT-001/002/003](audit/reports/CRITICAL_BLOCKERS.md)). SSOT формулировок: [`audit/reports/CLAIMS_LOCK_2026_07_17.md`](audit/reports/CLAIMS_LOCK_2026_07_17.md) · карта docs: [`docs/TIER0_INDEX.md`](docs/TIER0_INDEX.md) · жюри: [`docs/docs.md`](docs/docs.md) · стратегия: [`docs/samolet.md`](docs/samolet.md).

## Карта статуса (честно)

| Корзина | Смысл |
|---|---|
| **Работает** | Доказано на fixtures / репозитории |
| **Экспериментально** | Код есть; не customer-proven |
| **План** | Отложено (Wave 2+) |
| **Нужен заказчик** | RT-001/002/003 — checkpoint **NO_GO** |
| **Не заявляется** | Запрещённые формулировки до dual evidence |

**Работает:** analyze project-package; IFC/IDS/cross-doc; Shared-gate `summary.passed` ([ADR-001](docs/architecture/ADR-001-verdict-ownership-2026.md)); fail-closed pilot/production; ACL 404; SSRF; provenance; BCF ZIP 2.1/3.0 structural; HITL; CLI `export_evidence_bundle`; счётчики pytest / vitest — SSOT в [runtime baseline](docs/evidence/runtime-baseline-latest.json) (`frontend.tests_passed` при записи; иначе см. baseline/CI).

**Экспериментально:** OpenCDE BCF API push; optional clash/OCR; IFC KG scaffold.

**План:** enum пакетного исхода; расширение Stage-3 полей finding.

**Нужен заказчик:** RT-001 corpus · RT-002 нормы · RT-003 MEP ([CRITICAL_BLOCKERS](audit/reports/CRITICAL_BLOCKERS.md)).

**Не заявляется:** точность >90%; SLA ≤30 мин на customer; native DWG; MEP delivered; корректность расчётов; CDE-ready BCF. См. [capability-claim-matrix](docs/capability-claim-matrix-2026.md) · [PROJECT_STATUS_AUDIT](docs/PROJECT_STATUS_AUDIT_2026.md) · [pilot-protocol](docs/pilot-protocol-samolet-2026.md).

## Основные возможности

Статусы ниже — уровень **репозиторий / fixture**, если не указано иное.

| Возможность | Статус | Уровень доказательств | Примечание |
|---|---|---|---|
| Проверка свойств/величин IFC (IfcOpenShell) | Доступно | fixture | IFC2x3 / IFC4 / IFC4x3 |
| IDS 1.0 (IfcTester) | Доступно | fixture | Fail-closed при запросе без валидатора |
| Междокументные противоречия | Доступно | fixture | Таксономия `ConflictKind` (подмножество) |
| Аннотации чертежа ↔ IFC | Доступно | fixture | OCR-путь опционален |
| Допуски ISO 12006-3 (ε) | Доступно | fixture | — |
| Извлечение требований (regex) | Доступно | fixture | Не LLM-контур подписания |
| Бенчмарк извлечения RU AEC | Доступно | fixture | macro_f1 ≠ product accuracy |
| ISO 19650-lite метаданные | Доступно | fixture | Не продукт CDE |
| Коллизии (IfcClash) | Optional extra | optional-extra | `.[clash]`; при `require_clash` SKIPPED→FAILED |
| Честность capabilities | Доступно | fixture | FAILED блокирует `passed`; `/v1/system/capabilities` |
| Provenance finding | Доступно | fixture | Persist reject без `finding_id`/`evidence_refs` |
| Tenant/object ACL | Доступно | fixture | Principal + `tenant_id` отчёта |
| Экспорт BCF 2.1/3.0 ZIP | Доступно (T0/T1) | fixture | Структурный ZIP **AVAILABLE**; **CDE import NOT_VERIFIED (T2)** — лестница T0–T4 |
| OpenCDE BCF API push | Foundation | experimental | Не заменяет T2 |
| Vitest review-shell | Зелёный локально | release-readiness | **25** passed; не в main CI |
| DWG native | Missing / Failed | — | Без ODA fail-closed; never OK |
| DXF (CadModelIngestor) | Not verified | — | Optional ezdxf; honesty never OK |
| CV human-level | Missing | — | OCR degrade ≠ VLM |
| MEP system-aware clash | Not verified | — | DI-wired Unconfigured; не delivered |
| Корректность расчётов | Not implemented | — | OpenRebar = **сверка**, не верификация |
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
| T1 структура + dual consumers | Доказано | [`audit/evidence/bcf-structural-handoff-2026-07-18.json`](audit/evidence/bcf-structural-handoff-2026-07-18.json) |
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

## Бенчмарки и воспроизводимость

```bash
cd backend
python -m aerobim.tools.benchmark_project_package --iterations 1 --warmup-iterations 0
python -m aerobim.tools.measure_package_sla --corpus-kind fixture
python -m aerobim.tools.verify_bcf_structural_handoff
python -m aerobim.tools.export_runtime_baseline
python -m aerobim.tools.export_evidence_bundle \
  --pack ../samples/benchmarks/project-package-techlab-demo.json \
  --output ../artifacts/evidence-bundle/techlab-demo
```

Граница утверждений: [docs/pilot-claim-boundary-2026.md](docs/pilot-claim-boundary-2026.md) · [docs/capability-claim-matrix-2026.md](docs/capability-claim-matrix-2026.md) · [docs/pilot-protocol-samolet-2026.md](docs/pilot-protocol-samolet-2026.md).  
SSOT запрещённых формулировок: [audit/reports/CLAIMS_LOCK_2026_07_17.md](audit/reports/CLAIMS_LOCK_2026_07_17.md).  
Воспроизводимость: [docs/REPRODUCIBILITY-2026.md](docs/REPRODUCIBILITY-2026.md).

## Документация (пакет для жюри Техлаба)

На GitHub — **только** код и материалы для жюри Task 07. Служебные runbook’и, archive и Red Team dumps не публикуются.

| Нужно | Документ |
|------|----------|
| Старт | [`docs/TIER0_INDEX.md`](docs/TIER0_INDEX.md) · [`docs/README.md`](docs/README.md) |
| Жюри (RU) | [`docs/docs.md`](docs/docs.md) |
| Стратегия × Самолёт | [`docs/samolet.md`](docs/samolet.md) |
| ТЗ Task 07 | [`docs/tz/README.md`](docs/tz/README.md) |
| Блокеры / NO_GO | [`audit/reports/CRITICAL_BLOCKERS.md`](audit/reports/CRITICAL_BLOCKERS.md) |
| Граница утверждений | [`docs/pilot-claim-boundary-2026.md`](docs/pilot-claim-boundary-2026.md) |
| Архитектура | [`docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md`](docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md) |

## API (основное)

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/v1/system/capabilities` | Статическая honesty-поверхность |
| `GET` | `/health` | Readiness |
| `POST` | `/v1/analyze/project-package` | Мультимодальный анализ |
| `GET` | `/v1/reports/{id}/export/bcf` | Экспорт BCF ZIP |

## Git-коммиты

```bash
git config core.hooksPath .githooks
powershell -ExecutionPolicy Bypass -File scripts/git_commit.ps1 -Message "docs: ..."
```

<!-- AEROBIM_RUNTIME_BASELINE:BEGIN -->
<!-- regenerated by: python -m aerobim.tools.export_runtime_baseline -->
Backend src ~28875 LOC; tests ~19934 LOC; 781+ test functions; extraction macro_f1=0.8600000000000001 (fixture corpus; not product accuracy)
<!-- AEROBIM_RUNTIME_BASELINE:END -->

## Лицензия

MIT — см. [LICENSE](LICENSE).
