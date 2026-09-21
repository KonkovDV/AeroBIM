# Репозиторий

**Ссылка для формы:** https://github.com/KonkovDV/AeroBIM

> Мы на стадии доработки контура заказчика. Одна команда показывает находку с доказательствами на учебном комплекте. Валидация эффективности и внедрение у назначающей стороны ещё не начались. Checkpoint `GO` — регуляторно-измерительный MVP. `customer_go` остаётся false, пока нет независимого размеченного корпуса, двух разметчиков, подписанного профиля назначающей стороны и подтверждения импорта в СОД.

Ядро — MIT. IfcOpenShell / IfcTester — LGPL-3.0+; web-ifc — MPL-2.0. PyMuPDF вынесен в необязательный extra и не входит в основной контур. Политика: [`docs/license-policy-2026.md`](../../docs/license-policy-2026.md).

## Структура

| Путь | Содержимое |
|---|---|
| [`backend/`](../../backend/) | Python 3.12, FastAPI, проверка IFC / IDS |
| [`frontend/`](../../frontend/) | Оболочка ревью: панель замечаний и просмотр IFC. Подсветка ошибки на листе — P1-демо, не рабочее место эксперта |
| [`samples/`](../../samples/) | Учебные комплекты, не выгрузка заказчика |
| [`docs/`](../../docs/) | Документация и доказательства |

## Сборка и запуск

Канон: [Try it](../../README.md#try-it). Windows PowerShell (без активации venv):

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,raster]"
.\.venv\Scripts\python.exe -m aerobim.tools.run_kt3_jury
```

Linux/macOS: `python3.12 -m venv .venv`, `source .venv/bin/activate`, `pip install -e ".[dev,raster]"`, затем та же команда `run_kt3_jury`. Extra `pdf-agpl` в default не входит. `requirements-lock.txt` на Windows не ставить.

Та же установка, учебный шлюз приёмки: `python -m aerobim.tools.run_demo_ifc_acceptance_gate`.

Технический статус `summary.passed` ставят только детерминированные движки ([ADR-001](../../docs/architecture/ADR-001-verdict-ownership-2026.md)). Интеграцию с Tangl / 10D не заявляем.

Цифры тестов CI — [`docs/evidence/runtime-baseline-latest.json`](../../docs/evidence/runtime-baseline-latest.json). Локальный pytest этот файл не заменяет.

Показ демо-дня — семь слайдов: [`AeroBIM.pptx`](../03-presentation/AeroBIM.pptx). Живая команда выше.
