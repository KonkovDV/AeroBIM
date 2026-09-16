# Репозиторий

**Ссылка для формы:** https://github.com/KonkovDV/AeroBIM

> Мы на стадии доработки контура заказчика. Одна команда показывает находку с доказательствами на учебном комплекте. Валидация эффективности и внедрение у назначающей стороны ещё не начались. Checkpoint `GO` — регуляторно-измерительный MVP. `customer_go` остаётся false, пока нет независимого размеченного корпуса, двух разметчиков, подписанного профиля назначающей стороны и подтверждения импорта в СОД.

Ядро — MIT. IfcOpenShell / IfcTester — LGPL-3.0+; web-ifc — MPL-2.0. PyMuPDF вынесен в необязательный extra и не входит в основной контур. Политика: [`docs/license-policy-2026.md`](../../docs/license-policy-2026.md).

## Структура

| Путь | Содержимое |
|---|---|
| [`backend/`](../../backend/) | Python 3.12, FastAPI, проверка IFC / IDS |
| [`frontend/`](../../frontend/) | 3D-просмотр IFC, наложение на чертёж, панель замечаний |
| [`samples/`](../../samples/) | Учебные комплекты, не выгрузка заказчика |
| [`docs/`](../../docs/) | Документация и доказательства |

## Сборка и запуск

```bash
git clone https://github.com/KonkovDV/AeroBIM
cd AeroBIM/backend
pip install -e ".[dev,raster]"
python -m aerobim.tools.run_kt3_jury
```

Та же установка, учебный шлюз приёмки: `python -m aerobim.tools.run_demo_ifc_acceptance_gate`. Extra `pdf-agpl` в default не входит.

Технический статус `summary.passed` ставят только детерминированные движки ([ADR-001](../../docs/architecture/ADR-001-verdict-ownership-2026.md)). Интеграцию с Tangl / 10D не заявляем.

Цифры тестов CI — [`docs/evidence/runtime-baseline-latest.json`](../../docs/evidence/runtime-baseline-latest.json). Локальный pytest этот файл не заменяет.
