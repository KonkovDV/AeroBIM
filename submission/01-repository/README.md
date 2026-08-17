---
title: "Поле «Репозиторий» — карта кода и сборки"
status: active
version: "1.0.0"
last_updated: "2026-08-17"
claim_boundary: >
  Repository map only. No accuracy or SLA claims. Checkpoint NO_GO;
  RT-001/002/003 OPEN.
---

# Репозиторий

**Ссылка для формы:** https://github.com/KonkovDV/AeroBIM — публичный, MIT, доступ по ссылке без регистрации.

## Структура

| Путь | Содержимое |
|---|---|
| [`../../backend/`](../../backend/) | Python 3.12 · FastAPI · IfcOpenShell · IfcTester · слои domain/application/infrastructure/presentation |
| [`../../frontend/`](../../frontend/) | React · 3D-просмотр IFC (web-ifc) · 2D-наложение · панель замечаний |
| [`../../samples/`](../../samples/) | Фикстуры, нормо-паки, каталог типовых ошибок, приложения ТЗ |
| [`../../docs/`](../../docs/) | Документация, матрицы соответствия, доказательства |
| [`../../audit/`](../../audit/) | Claims Lock, реестр блокеров, реестр исключений линта |
| [`../../scripts/`](../../scripts/) | Гейты честности: `lint_claims.py`, `check_docs_metadata_integrity.py` |
| [`../../governance/`](../../governance/) | Политики репозитория |

## Сборка и запуск

```bash
git clone https://github.com/KonkovDV/AeroBIM
cd AeroBIM/backend
pip install -e ".[dev,raster]"
python -m aerobim.tools.run_demo_ifc_acceptance_gate
```

Опционально: `.[clash]` для IfcClash. Контейнерный контур — [`../../docker-compose.yml`](../../docker-compose.yml). Требования к сборке: [`../../docs/tz/TZ_BUILD_AND_QUALITY_2026.md`](../../docs/tz/TZ_BUILD_AND_QUALITY_2026.md).

## Архитектура

Каноническая: [`../../docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md`](../../docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md). Требования ТЗ к архитектуре: [`../../docs/tz/TZ_ARCHITECTURE_REQUIREMENTS_2026.md`](../../docs/tz/TZ_ARCHITECTURE_REQUIREMENTS_2026.md).

Четыре контура: `INGESTION → DETERMINISTIC_VALIDATION → AI_ADVISORY → EVIDENCE_REPORTING`. Технический статус `summary.passed` ставят **только** детерминированные движки — ADR-001: [`../../docs/architecture/ADR-001-verdict-ownership-2026.md`](../../docs/architecture/ADR-001-verdict-ownership-2026.md). Языковые и визуальные модели только подсказывают и статус не меняют.

## Качество и воспроизводимость

| Что | Где |
|---|---|
| CI | [`../../.github/workflows/`](../../.github/workflows/) · бейдж в [`../../README.md`](../../README.md) |
| Сообщество GitHub | [`../../LICENSE`](../../LICENSE) · [`../../SECURITY.md`](../../SECURITY.md) · [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md) · [`../../CODE_OF_CONDUCT.md`](../../CODE_OF_CONDUCT.md) · [`../../SUPPORT.md`](../../SUPPORT.md) |
| Пины прогонов | [`../../docs/evidence/runtime-baseline-latest.json`](../../docs/evidence/runtime-baseline-latest.json) (CI pin = `commit_sha` / `tests_passed` / `tests_collected` в этом JSON, `attested_by=ci`; локальный pytest ≠ pin) |
| Воспроизводимость | [`../../docs/REPRODUCIBILITY-2026.md`](../../docs/REPRODUCIBILITY-2026.md) |
| Известные дефекты | [`../../KNOWN_BUGS.md`](../../KNOWN_BUGS.md) |
| Безопасность | [`../../SECURITY.md`](../../SECURITY.md) |
| Лицензии зависимостей | [`../../docs/license-policy-2026.md`](../../docs/license-policy-2026.md) |

Ядро PDF — `pypdfium2` + `pdfminer.six`; AGPL-компоненты вынесены в необязательный набор (LIC-001 Option B).

## Гейты честности в дереве

```bash
python scripts/lint_claims.py                    # запрещённые формулировки
python scripts/lint_claims.py --matrix-guard     # заблокированные строки матрицы ТЗ
python scripts/check_docs_metadata_integrity.py  # версии и даты документов
```

Эти проверки запрещают в публичных текстах заявления, не подкреплённые доказательствами, — включая наши собственные. После гигиенических коммитов CI pin может отставать от HEAD до следующего прогона CI (N-43).
