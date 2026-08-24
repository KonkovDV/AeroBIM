---
title: "Поле «Репозиторий» — карта кода и сборки"
status: active
version: "1.0.4"
last_updated: "2026-08-18"
claim_boundary: >
  Repository map only. No accuracy or SLA claims. Checkpoint NO_GO;
  RT-001/002/003 OPEN.
---

# Репозиторий

**Ссылка для формы:** https://github.com/KonkovDV/AeroBIM — публичный, доступ по ссылке без регистрации.

**Формула стадии (дословно; источник — [карточка речи для жюри](../../docs/demo/KT2_JURY_FAQ_2026_08_12.md)):** Мы на стадии доработки. Одна команда показывает находку с доказательствами на учебном комплекте. Валидация эффективности и внедрение ещё не начались. `NO_GO` сохраняется, пока нет независимого размеченного корпуса, двух разметчиков, профиля приёмки (публичные IDS экспертизы — измерение; подпись Самолёта — внедрение) и подтверждения импорта в СОД.

Ядро репозитория распространяется по MIT. Лицензии сторонних зависимостей указаны отдельно: IfcOpenShell и IfcTester — LGPL-3.0+; web-ifc — MPL-2.0; AGPL-компоненты (PyMuPDF) вынесены в необязательный extra и не входят в основной runtime-контур. Политика: [`../../docs/license-policy-2026.md`](../../docs/license-policy-2026.md). Это не юридическое заключение.

## Структура

| Путь | Содержимое |
|---|---|
| [`../../backend/`](../../backend/) | Python 3.12 · FastAPI · проверка IFC / IDS |
| [`../../frontend/`](../../frontend/) | Просмотр IFC в 3D, наложение на чертёж, панель замечаний |
| [`../../samples/`](../../samples/) | Учебные комплекты. Это не выгрузка заказчика и не комплект Самолёта |
| [`../../docs/`](../../docs/) | Документация и доказательства |
| [`../../audit/reports/CRITICAL_BLOCKERS.md`](../../audit/reports/CRITICAL_BLOCKERS.md) | Блокеры RT-001/002/003 |

## Сборка и запуск

```bash
git clone https://github.com/KonkovDV/AeroBIM
cd AeroBIM/backend
pip install -e ".[dev,raster]"
python -m aerobim.tools.run_demo_ifc_acceptance_gate
```

Опционально: `.[clash]` для коллизий. Требования к сборке: [`../../docs/tz/TZ_BUILD_AND_QUALITY_2026.md`](../../docs/tz/TZ_BUILD_AND_QUALITY_2026.md).

## Архитектура

Каноническая: [`../../docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md`](../../docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md). Требования ТЗ к архитектуре: [`../../docs/tz/TZ_ARCHITECTURE_REQUIREMENTS_2026.md`](../../docs/tz/TZ_ARCHITECTURE_REQUIREMENTS_2026.md).

Четыре контура: загрузка → детерминированная проверка → советующий контур → отчёт с доказательствами. Технический статус `summary.passed` ставят **только** детерминированные движки — ADR-001: [`../../docs/architecture/ADR-001-verdict-ownership-2026.md`](../../docs/architecture/ADR-001-verdict-ownership-2026.md). Языковые и визуальные модели только подсказывают и статус не меняют. Интеграцию с Tangl / 10D не заявляем: возможна только file/API-граница.

## Качество и воспроизводимость

| Что | Где |
|---|---|
| CI | бейдж в [`../../README.md`](../../README.md) |
| Пины прогонов | [`../../docs/evidence/runtime-baseline-latest.json`](../../docs/evidence/runtime-baseline-latest.json) (CI pin = `commit_sha` / `tests_passed` / `tests_collected` в этом JSON, `attested_by=ci`; локальный pytest ≠ pin) |
| Лицензия | [`../../LICENSE`](../../LICENSE) · [`../../docs/license-policy-2026.md`](../../docs/license-policy-2026.md) |

Презентация для формы: [`aerobim_kt2.pptx`](../03-presentation/aerobim_kt2.pptx) + [`aerobim_kt2.pdf`](../03-presentation/aerobim_kt2.pdf). Видео не записываем.

После правок документации CI pin может отставать от HEAD до следующего прогона CI.
