---
title: "Поле «Репозиторий» — карта кода и сборки"
status: active
version: "1.1.0"
last_updated: "2026-09-15"
claim_boundary: >
  Repository map only. No accuracy or SLA claims. Checkpoint GO; customer_go false;
  RT-001/002/003 OPEN.
---

# Репозиторий

**Ссылка для формы:** https://github.com/KonkovDV/AeroBIM — публичный, доступ по ссылке без регистрации.

Карта КТ#3: [`../README.md`](../README.md) · речь: [`../../docs/demo/KT3_JURY_FAQ_2026_08_25.md`](../../docs/demo/KT3_JURY_FAQ_2026_08_25.md) · замок демо-дня: [`../../docs/demo/DEMO_DAY_SPEECH_LOCK_2026_09.md`](../../docs/demo/DEMO_DAY_SPEECH_LOCK_2026_09.md). Checkpoint `GO`.

**Формула стадии (дословно; источник — [карточка речи для жюри](../../docs/demo/KT2_JURY_FAQ_2026_08_12.md)):** Мы на стадии доработки контура заказчика. Одна команда показывает находку с доказательствами на учебном комплекте. Валидация эффективности и внедрение у назначающей стороны ещё не начались. Checkpoint `GO` — регуляторно-измерительный MVP. `customer_go` остаётся false, пока нет независимого размеченного корпуса, двух разметчиков, подписанного профиля назначающей стороны и подтверждения импорта в СОД.

Ядро репозитория распространяется по MIT. Лицензии сторонних зависимостей указаны отдельно: IfcOpenShell и IfcTester — LGPL-3.0+; web-ifc — MPL-2.0; AGPL-компоненты (PyMuPDF) вынесены в необязательный extra `pdf-agpl` и не входят в основной runtime-контур и `requirements-lock.txt`. Политика: [`../../docs/license-policy-2026.md`](../../docs/license-policy-2026.md). Это не юридическое заключение.

Публичное дерево не называет назначающую сторону. Локальные шаблоны NDA и каталог `out/` в git не входят.

## Структура

| Путь | Содержимое |
|---|---|
| [`../../backend/`](../../backend/) | Python 3.12 · FastAPI · проверка IFC / IDS |
| [`../../frontend/`](../../frontend/) | Просмотр IFC в 3D, наложение на чертёж, панель замечаний |
| [`../../samples/`](../../samples/) | Учебные комплекты. Это не выгрузка заказчика и не комплект заказчика |
| [`../../docs/`](../../docs/) | Документация и доказательства |
| [`../../audit/reports/CRITICAL_BLOCKERS.md`](../../audit/reports/CRITICAL_BLOCKERS.md) | Блокеры RT-001/002/003 |

## Сборка и запуск

```bash
git clone https://github.com/KonkovDV/AeroBIM
cd AeroBIM/backend
pip install -e ".[dev,raster]"
python -m aerobim.tools.run_demo_ifc_acceptance_gate
```

Опционально: `.[clash]` для коллизий. Extra `pdf-agpl` — не default. Требования к сборке: [`../../docs/tz/TZ_BUILD_AND_QUALITY_2026.md`](../../docs/tz/TZ_BUILD_AND_QUALITY_2026.md).

Демо-день (тот же клон, учебный комплект):

```bash
python -m aerobim.tools.run_kt3_jury
```

## Архитектура

Каноническая: [`../../docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md`](../../docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md). Требования ТЗ к архитектуре: [`../../docs/tz/TZ_ARCHITECTURE_REQUIREMENTS_2026.md`](../../docs/tz/TZ_ARCHITECTURE_REQUIREMENTS_2026.md).

Четыре контура: загрузка → детерминированная проверка → советующий контур → отчёт с доказательствами. Технический статус `summary.passed` ставят **только** детерминированные движки — ADR-001: [`../../docs/architecture/ADR-001-verdict-ownership-2026.md`](../../docs/architecture/ADR-001-verdict-ownership-2026.md). Языковые и визуальные модели только подсказывают и статус не меняют. Интеграцию с Tangl / 10D не заявляем: возможна только file/API-граница.

Подстановки адаптеров (инвентарь кода, не смета вендора): [`../../docs/evidence/substitution-matrix-latest.json`](../../docs/evidence/substitution-matrix-latest.json) — 63 DI-токена, 58 живых / 1 in-memory / 4 отсутствуют.

Где лежат отчёты: [`../../docs/evidence/data-residency-inventory-latest.json`](../../docs/evidence/data-residency-inventory-latest.json). Задачи анализа — `BackgroundTasks` в процессе API, не отдельная очередь работников. Потолок RAM: [`../../docs/deployment-sizing-and-cost-2026.md`](../../docs/deployment-sizing-and-cost-2026.md) — диапазоны из кода, не коммерческое КП.

## Качество и воспроизводимость

| Что | Где |
|---|---|
| CI | бейдж в [`../../README.md`](../../README.md); живые `*latest.json` не старше семи дней |
| Пины прогонов | [`../../docs/evidence/runtime-baseline-latest.json`](../../docs/evidence/runtime-baseline-latest.json) (CI pin = `commit_sha` / `tests_passed` / `tests_collected` в этом JSON, `attested_by=ci`; локальный pytest ≠ pin) |
| Лицензия | [`../../LICENSE`](../../LICENSE) · [`../../docs/license-policy-2026.md`](../../docs/license-policy-2026.md) |
| Офлайн-контур | [`../../docs/evidence/offline-bundle-trial-latest.json`](../../docs/evidence/offline-bundle-trial-latest.json) — пробный Docker image-track, не данные заказчика |

Презентация для поля формы: [`AeroBIM_demo_day.pdf`](../03-presentation/AeroBIM_demo_day.pdf). Архив КТ#2: [`aerobim_kt2.pptx`](../03-presentation/aerobim_kt2.pptx). Речь 29–30.09: [`demo_day_slides.md`](../03-presentation/demo_day_slides.md). Видео не записываем.

После правок документации CI pin может отставать от HEAD до следующего прогона CI.
