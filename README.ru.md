# AeroBIM

[English version](README.md)

Платформа с открытым исходным кодом для **кросс-модальной проверки BIM** в едином детерминированном конвейере.

AeroBIM сверяет IFC-модели с техническими требованиями, 2D-чертежами, расчётными документами и IDS-пакетами. Результаты сохраняются с трассировкой происхождения и экспортируются в JSON, HTML и BCF.

## Основные возможности

| Возможность | Статус |
|---|---|
| Проверка свойств и величин IFC (`IfcOpenShell`) | ✅ |
| Проверка по IDS 1.0 (`IfcTester`) | ✅ |
| Междокументные противоречия | ✅ |
| Типы конфликтов (`ConflictKind`: жёсткий / несовпадение единиц / неоднозначность) | ✅ |
| Настройка уровня серьёзности противоречий | ✅ |
| Сверка аннотаций чертежа с IFC | ✅ |
| Допуски по ISO 12006-3 (ε-полоса) | ✅ |
| Извлечение требований из текста (regex, без моделей в контуре подписания) | ✅ |
| Корпус RU AEC для оценки извлечения (10 документов, 50 требований) | ✅ |
| Коллизии (`IfcClash`, опция `.[clash]`) | ✅ |
| Экспорт BCF 2.1 | ✅ |
| Экспорт BCF 3.0 | ✅ Экспериментально |
| Контекст ISO 19650-lite в отчёте | ✅ |
| Хранилище артефактов (`ObjectStore`, TTL, индекс Postgres) | ✅ Базовый слой |
| Экспорт JSON и HTML | ✅ |
| Просмотр IFC в браузере (`web-ifc` + `Three.js`) | ✅ |
| Наложение зон проблем на 2D-чертежи | ✅ |
| Разбор PDF/OCR для чертежей | ✅ |
| Распознавание чертежей на VLM | 🔜 В планах |

## Совместимость с IFC

| Релиз IFC | Схема | Поддержка | Примечание |
|---|---|---|---|
| IFC2x3 | ISO 16739:2005 | ✅ Основной | Наиболее распространён в эксплуатации |
| IFC4 (ADD2) | ISO 16739-1:2018 | ✅ Основной | Нормализация имён Pset и единиц |
| IFC4x3 | ISO 16739-1:2024 | ✅ Основной | Тот же ядро проверки, расширения по инфраструктуре |

Подробнее: [docs/ifc-compatibility-matrix.md](docs/ifc-compatibility-matrix.md).

## BCF

| Версия | Статус | Примечание |
|---|---|---|
| BCF 2.1 | ✅ Стабильно | Основной путь экспорта |
| BCF 3.0 | ✅ Экспериментально | `GET /v1/reports/{id}/export/bcf?version=3`, по умолчанию 2.1 |
| BCF API | 🔜 В планах | REST-адаптер для CDE и трекеров задач |

## Быстрый старт

```bash
git clone https://github.com/KonkovDV/AeroBIM.git
cd AeroBIM/backend

python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

pip install -e ".[dev,vision]"
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

Команды для публикации метрик и supplementary-материалов:

```bash
cd backend
python -m aerobim.tools.benchmark_project_package --iterations 1 --warmup-iterations 0
python -m aerobim.tools.run_ablation_study
python -m aerobim.tools.generate_benchmark_report --output-dir ../docs/evidence
python -m aerobim.tools.export_runtime_baseline
```

Граница утверждений для пилота и публикаций: [docs/pilot-claim-boundary-2026.md](docs/pilot-claim-boundary-2026.md).  
Пакет доказательств: [docs/academic-publication-evidence-2026.md](docs/academic-publication-evidence-2026.md).

## API (основное)

| Метод | Путь | Назначение |
|---|---|---|
| `GET` | `/health` | Проверка готовности |
| `POST` | `/v1/validate/ifc` | IFC + требования + IDS |
| `POST` | `/v1/analyze/project-package` | Мультимодальная проверка пакета |
| `GET` | `/v1/reports` | Список отчётов |
| `GET` | `/v1/reports/{id}/export/json` | JSON |
| `GET` | `/v1/reports/{id}/export/html` | HTML |
| `GET` | `/v1/reports/{id}/export/bcf` | BCF 2.1; `?version=3` — BCF 3.0 |

Полный перечень — в [README.md](README.md#api-endpoints).

## Конфигурация

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `AEROBIM_STORAGE_DIR` | `var/reports` | Каталог отчётов |
| `AEROBIM_CROSS_DOC_SEVERITY` | `warning` | Уровень серьёзности междокументных противоречий |
| `AEROBIM_DB_URL` | *(не задано)* | Postgres для индекса сводок |
| `AEROBIM_REPORT_TTL_DAYS` | *(не задано)* | Срок хранения отчётов |
| `AEROBIM_S3_BUCKET` | *(не задано)* | S3/MinIO |

Полный список: [backend/.env.example](backend/.env.example), [ops/environment-matrix.md](ops/environment-matrix.md).

## Документация

- [Карта документации](docs/README.md)
- [Архитектура](docs/06-architecture-reference.md)
- [План исполнения 2026](docs/13-academic-execution-plan-2026.md)
- [Протокол разметки RU](docs/annotation-protocol-2026.md)
- [Наборы бенчмарков](samples/benchmarks/README.md)
- [Эксплуатация](ops/standalone-runbook.md)

## Коммиты в Git

Не коммитьте через агента Cursor — отключите **Agent → Attribution** и используйте [scripts/git_commit.ps1](scripts/git_commit.ps1) или задачу VS Code **AeroBIM: commit**. Подробнее: [docs/git-hygiene-2026.md](docs/git-hygiene-2026.md).

Перед push на GitHub: [docs/github-readiness-audit-2026-05-20.md](docs/github-readiness-audit-2026-05-20.md). Метаданные репозитория: [.github/repository-metadata.md](.github/repository-metadata.md).

## Управление проектом

- [Contributing](CONTRIBUTING.md)
- [Git hygiene](docs/git-hygiene-2026.md)
- [Security](SECURITY.md)
- [Citation](CITATION.cff) · [BibTeX](docs/CITATION.bib)
- [Support](SUPPORT.md) · [Maintainers](MAINTAINERS.md)

## Архитектура

Пятислойная Clean Architecture: `core` → `domain` → `application` → `infrastructure` → `presentation`.  
Внешние библиотеки подключаются только через порты; композиция — в `bootstrap_container()`.

## Лицензия

[MIT](LICENSE)
