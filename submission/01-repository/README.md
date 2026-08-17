---
title: "Поле «Репозиторий» — карта кода и сборки"
status: active
version: "1.0.1"
last_updated: "2026-08-17"
claim_boundary: >
  Repository map only. No accuracy or SLA claims. Checkpoint NO_GO;
  RT-001/002/003 OPEN.
---

# Репозиторий

**Ссылка для формы:** https://github.com/KonkovDV/AeroBIM — публичный, доступ по ссылке без регистрации.

**Формула стадии (дословно, SSOT [`../../docs/demo/KT2_JURY_FAQ_2026_08_12.md`](../../docs/demo/KT2_JURY_FAQ_2026_08_12.md)):** Мы на стадии доработки. Одна команда показывает находку с доказательствами на учебном комплекте. Валидация эффективности и внедрение ещё не начались. `NO_GO` сохраняется, пока нет корпуса Самолёта, двух разметчиков, подписанного профиля приёмки и подтверждения импорта в СОД.

Ядро репозитория распространяется по MIT. Лицензии сторонних зависимостей указаны отдельно: IfcOpenShell и IfcTester — LGPL-3.0+; web-ifc — MPL-2.0; AGPL-компоненты (PyMuPDF) вынесены в необязательный extra и не входят в основной runtime-контур. Политика: [`../../docs/license-policy-2026.md`](../../docs/license-policy-2026.md). Это не юридическое заключение.

## Структура

| Путь | Содержимое |
|---|---|
| [`../../backend/`](../../backend/) | Python 3.12 · FastAPI · IfcOpenShell · IfcTester · слои domain/application/infrastructure/presentation |
| [`../../frontend/`](../../frontend/) | React · 3D-просмотр IFC (web-ifc) · 2D-наложение · панель замечаний |
| [`../../samples/`](../../samples/) | Учебные комплекты (fixture): IFC, IDS, чертежи, нормо-паки. Это не выгрузка Renga заказчика и не комплект Самолёта |
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

Четыре контура: загрузка → детерминированная проверка → советующий контур → отчёт с доказательствами. Технический статус `summary.passed` ставят **только** детерминированные движки — ADR-001: [`../../docs/architecture/ADR-001-verdict-ownership-2026.md`](../../docs/architecture/ADR-001-verdict-ownership-2026.md). Языковые и визуальные модели только подсказывают и статус не меняют. Интеграцию с Tangl / 10D не заявляем: возможна только file/API-граница.

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

Ядро PDF — `pypdfium2` + `pdfminer.six`; набор `pdf-agpl` (PyMuPDF) для показа не нужен.

## Гейты честности в дереве

```bash
python scripts/lint_claims.py                    # запрещённые формулировки
python scripts/lint_claims.py --matrix-guard     # заблокированные строки матрицы ТЗ
python scripts/check_docs_metadata_integrity.py  # версии и даты документов
```

Эти проверки запрещают в публичных текстах заявления, не подкреплённые доказательствами, — включая наши собственные. После гигиенических коммитов CI pin может отставать от HEAD до следующего прогона CI (N-43).
