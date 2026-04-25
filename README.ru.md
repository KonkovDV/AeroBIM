# AeroBIM

[English version](README.md)

Open-source платформа для **кросс-модальной семантической валидации BIM**.

AeroBIM проверяет IFC-модели по техническим требованиям, 2D-чертежам, расчётным документам и IDS-пакетам в едином детерминированном конвейере с полной трассировкой происхождения данных и BCF-интероперабельностью.

## Ключевые возможности

| Возможность | Статус |
|---|---|
| Валидация IFC-свойств и количеств (`IfcOpenShell`) | ✅ |
| Валидация IDS 1.0 (`IfcTester`) | ✅ |
| Поиск междокументных противоречий | ✅ |
| Таксономия конфликтов (`ConflictKind`) | ✅ |
| Настраиваемая severity-политика для противоречий | ✅ |
| Проверка коллизий (`IfcClash`, опциональный extra `.[clash]`) | ✅ |
| Экспорт BCF 2.1 | ✅ |
| Экспорт BCF 3.0 | ✅ Experimental |
| Foundation для enterprise storage (`ObjectStore` + TTL + Postgres index hook) | ✅ Foundation |
| HTML / JSON export | ✅ |
| Браузерный IFC viewer (`web-ifc` + `Three.js`) | ✅ Начальный tranche |

## Совместимость IFC

| Релиз IFC | Схема | Поддержка | Примечание |
|---|---|---|---|
| IFC2x3 | ISO 16739:2005 | ✅ Core | Широко распространённый production-профиль |
| IFC4 (ADD2) | ISO 16739-1:2018 | ✅ Core | Нормализация Pset naming и unit assignment |
| IFC4x3 | ISO 16739-1:2024 | ✅ Core | Та же validation-kernel, расширения по alignment/infrastructure |

Подробная матрица: [docs/ifc-compatibility-matrix.md](docs/ifc-compatibility-matrix.md).

## BCF

| Версия | Статус | Примечание |
|---|---|---|
| BCF 2.1 | ✅ Stable | Основной export path |
| BCF 3.0 | ✅ Experimental | `GET /v1/reports/{id}/export/bcf?version=3`, по умолчанию остаётся 2.1 |
| BCF API | 🔜 Roadmap | CDE / issue-tracker integration |

## Enterprise Storage Foundation

В итерации B.1 уже shipped базовый совместимый storage-layer:

- доменный порт `ObjectStore` для бинарных артефактов (`put/get/delete/presign`);
- `LocalObjectStore` для текущего локального runtime;
- `S3ObjectStore` для S3/MinIO через optional enterprise extras;
- `PostgresAuditStore` foundation для индекса метаданных отчётов в Postgres;
- `AEROBIM_REPORT_TTL_DAYS` для retention/TTL persisted reports.

Пока это именно foundation-step:

- без enterprise extras система продолжает работать на локальном storage без изменения HTTP-контрактов;
- при наличии `AEROBIM_DB_URL` и enterprise-зависимостей summaries индексируются в Postgres;
- IFC-source и drawing previews уже вынесены за абстракцию `ObjectStore`, поэтому дальнейший переход на S3/MinIO не требует смены API paths.

## Быстрый старт

```bash
git clone https://github.com/KonkovDV/AeroBIM.git
cd AeroBIM/backend

python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

pip install -e ".[dev,vision]"
# pip install -e ".[clash]"       # clash detection
# pip install -e ".[docling]"     # document extraction
# pip install -e ".[enterprise]"  # S3/Postgres storage adapters

pytest tests -v
python -m aerobim.main
```

## Локальный quality-gate

Перед push в `main` запускайте тот же минимальный набор проверок, что и в CI:

```bash
cd AeroBIM/backend
python -m ruff format --check src tests
python -m ruff check src tests
python -m mypy src
pytest tests -q
```

Если `ruff format --check` сообщает про неотформатированные файлы, примените:

```bash
python -m ruff format src tests
```

## Основные API-paths

| Метод | Path | Описание |
|---|---|---|
| `GET` | `/health` | Probe готовности |
| `POST` | `/v1/validate/ifc` | Валидация IFC по требованиям + IDS |
| `POST` | `/v1/analyze/project-package` | Мультимодальная проверка project package |
| `GET` | `/v1/reports` | Список persisted reports |
| `GET` | `/v1/reports/{id}` | Получить отчёт |
| `GET` | `/v1/reports/{id}/source/ifc` | Скачать IFC source, привязанный к отчёту |
| `GET` | `/v1/reports/{id}/drawing-assets/{asset_id}/preview` | Скачать persisted drawing preview |
| `GET` | `/v1/reports/{id}/export/bcf` | BCF 2.1 по умолчанию; `?version=3` включает BCF 3.0 |

## Конфигурация

Ключевые переменные окружения:

| Переменная | Значение по умолчанию | Назначение |
|---|---|---|
| `AEROBIM_STORAGE_DIR` | `var/reports` | Локальное корневое хранилище отчётов |
| `AEROBIM_CROSS_DOC_SEVERITY` | `warning` | Политика severity для междокументных противоречий |
| `AEROBIM_DB_URL` | *(unset)* | Postgres URL для summary index |
| `AEROBIM_REPORT_TTL_DAYS` | *(unset)* | TTL persisted reports |
| `AEROBIM_S3_BUCKET` | *(unset)* | S3/MinIO bucket |
| `AEROBIM_S3_ENDPOINT_URL` | *(unset)* | Custom endpoint для MinIO/S3-compatible storage |
| `AEROBIM_S3_REGION` | `us-east-1` | Регион подписи |
| `AEROBIM_S3_ACCESS_KEY_ID` | *(unset)* | Access key |
| `AEROBIM_S3_SECRET_ACCESS_KEY` | *(unset)* | Secret key |
| `AEROBIM_S3_PREFIX` | `aerobim` | Префикс object keys |

Полный список: [backend/.env.example](backend/.env.example) и [ops/environment-matrix.md](ops/environment-matrix.md).

## Документация

- [docs/06-architecture-reference.md](docs/06-architecture-reference.md) — каноническая архитектура
- [docs/13-academic-execution-plan-2026.md](docs/13-academic-execution-plan-2026.md) — план Iterations A–C
- [docs/14-enterprise-storage-foundation.md](docs/14-enterprise-storage-foundation.md) — shipped foundation для B.1
- [docs/15-local-quality-gate.md](docs/15-local-quality-gate.md) — локальные CI-parity проверки форматирования/линта/типов/тестов
- [ops/environment-matrix.md](ops/environment-matrix.md) — матрица окружения и dependency profiles