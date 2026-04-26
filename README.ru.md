# AeroBIM

[English version](README.md)

Платформа с открытым исходным кодом для **кросс-модальной семантической валидации BIM**.

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
| Экспорт BCF 3.0 | ✅ Экспериментально |
| Базовый слой для корпоративного хранилища (`ObjectStore` + TTL + Postgres index hook) | ✅ Базовый слой |
| HTML / JSON export | ✅ |
| Браузерный IFC viewer (`web-ifc` + `Three.js`) | ✅ Начальный этап |

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
| BCF 3.0 | ✅ Экспериментально | `GET /v1/reports/{id}/export/bcf?version=3`, по умолчанию остаётся 2.1 |
| BCF API | 🔜 План развития | Интеграция с CDE / трекерами задач |

## Базовый слой корпоративного хранилища

В итерации B.1 уже поставлен базовый совместимый слой хранения:

- доменный порт `ObjectStore` для бинарных артефактов (`put/get/delete/presign`);
- `LocalObjectStore` для текущего локального рабочего контура;
- `S3ObjectStore` для S3/MinIO через опциональные enterprise-дополнения;
- `PostgresAuditStore` как база для индекса метаданных отчётов в Postgres;
- `AEROBIM_REPORT_TTL_DAYS` для хранения отчётов по TTL.

Пока это именно базовый этап:

- без enterprise-дополнений система продолжает работать на локальном хранилище без изменения HTTP-контрактов;
- при наличии `AEROBIM_DB_URL` и enterprise-зависимостей сводки индексируются в Postgres;
- исходные IFC и превью чертежей уже вынесены за абстракцию `ObjectStore`, поэтому дальнейший переход на S3/MinIO не требует смены API-маршрутов.

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
# pip install -e ".[enterprise]"  # адаптеры хранения S3/Postgres

pytest tests -v
python -m aerobim.main
```

## Локальный контур качества

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

## Основные API-маршруты

| Метод | Path | Описание |
|---|---|---|
| `GET` | `/health` | Проверка готовности |
| `POST` | `/v1/validate/ifc` | Валидация IFC по требованиям + IDS |
| `POST` | `/v1/analyze/project-package` | Мультимодальная проверка пакета проекта |
| `GET` | `/v1/reports` | Список сохранённых отчётов |
| `GET` | `/v1/reports/{id}` | Получить отчёт |
| `GET` | `/v1/reports/{id}/source/ifc` | Скачать исходный IFC, привязанный к отчёту |
| `GET` | `/v1/reports/{id}/drawing-assets/{asset_id}/preview` | Скачать сохранённое превью чертежа |
| `GET` | `/v1/reports/{id}/export/bcf` | BCF 2.1 по умолчанию; `?version=3` включает BCF 3.0 |

## Конфигурация

Ключевые переменные окружения:

| Переменная | Значение по умолчанию | Назначение |
|---|---|---|
| `AEROBIM_STORAGE_DIR` | `var/reports` | Локальное корневое хранилище отчётов |
| `AEROBIM_CROSS_DOC_SEVERITY` | `warning` | Политика severity для междокументных противоречий |
| `AEROBIM_DB_URL` | *(unset)* | URL Postgres для индекса сводок |
| `AEROBIM_REPORT_TTL_DAYS` | *(unset)* | TTL для сохранённых отчётов |
| `AEROBIM_S3_BUCKET` | *(unset)* | S3/MinIO bucket |
| `AEROBIM_S3_ENDPOINT_URL` | *(unset)* | Пользовательский endpoint для MinIO/S3-совместимого хранилища |
| `AEROBIM_S3_REGION` | `us-east-1` | Регион подписи |
| `AEROBIM_S3_ACCESS_KEY_ID` | *(unset)* | Ключ доступа |
| `AEROBIM_S3_SECRET_ACCESS_KEY` | *(unset)* | Секретный ключ |
| `AEROBIM_S3_PREFIX` | `aerobim` | Префикс object keys |

Полный список: [backend/.env.example](backend/.env.example) и [ops/environment-matrix.md](ops/environment-matrix.md).

## Документация

- [docs/06-architecture-reference.md](docs/06-architecture-reference.md) — каноническая архитектура
- [docs/13-academic-execution-plan-2026.md](docs/13-academic-execution-plan-2026.md) — план Iterations A–C
- [docs/14-enterprise-storage-foundation.md](docs/14-enterprise-storage-foundation.md) — поставленный базовый слой для B.1
- [docs/15-local-quality-gate.md](docs/15-local-quality-gate.md) — локальные проверки форматирования/линта/типов/тестов в паритете с CI
- [ops/environment-matrix.md](ops/environment-matrix.md) — матрица окружения и dependency profiles

## Управление проектом

- [Contributing](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)
- [Citation Metadata](CITATION.cff)
- [Support](SUPPORT.md)
- [Maintainers](MAINTAINERS.md)
- [Release Policy](RELEASE_POLICY.md)

## Архитектура

Пятислойная Clean Architecture с направлением зависимостей внутрь:

```text
core/           DI container, tokens, config
domain/         Immutable models, Protocol ports, logging contract
application/    Use case orchestration
infrastructure/ External adapters (IFC/IDS/BCF/storage)
presentation/   FastAPI HTTP API + middleware
```

Storage-слой уже использует абстракцию `ObjectStore`, поэтому локальное хранилище и S3/MinIO переключаются без изменения публичных API-маршрутов.

## Академический Стандарт Отчётности

### Граница Утверждений

Этот README разделяет подтверждённые факты и плановые намерения.

- Подтверждёнными считаются возможности, которые имеют исполнимые адаптеры, тестовое покрытие, API-контракты или сохранённые артефакты отчётов.
- Пункты плана развития (например, более тяжёлый VLM-путь и BCF API) явно отмечаются как будущая работа.
- Бенчмарк-метрики трактуются как контекстные измерения для конкретной среды, а не как универсальные гарантии.

### Базовый Протокол Воспроизводимости

Перед публикацией локальных выводов используйте минимальный набор:

```bash
cd backend
python -m ruff format --check src tests
python -m ruff check src tests
python -m mypy src
pytest tests -q
python -m aerobim.tools.seed_smoke_report
```

Для утверждений по бенчмаркам фиксируйте путь набора бенчмарков, CLI-параметры, режим threshold-gate и пути к итоговым артефактам.

### Цитирование И Переиспользование

- Если отдельный citation-файл отсутствует, указывайте URL репозитория, commit SHA и идентификаторы отчётов/артефактов.
- Для связки AeroBIM ↔ OpenRebar фиксируйте provenance digest и версию контракта отчёта.
- При сравнении базового regex-подхода и более тяжёлых мультимодальных подходов явно описывайте ограничения методологии.

## Лицензия

[MIT](LICENSE)

