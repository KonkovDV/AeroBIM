<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
# AeroBIM

[English version](README.md)

[![CI](https://github.com/KonkovDV/AeroBIM/actions/workflows/ci.yml/badge.svg)](https://github.com/KonkovDV/AeroBIM/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Проверка критериев приёмки для openBIM-комплектов.** На входе — модели IFC, наборы правил IDS, чертежи и тексты требований; на выходе — находки с прослеживаемыми доказательствами в форматах HTML, JSON и BCF. AeroBIM помогает эксперту найти дефекты комплекта **до** координации и экспертизы. Это не среда общих данных, не просмотрщик модели и не замена эксперту.

> ### Checkpoint: `NO_GO`
>
> Это внутренняя оценка готовности к *подписанию у заказчика*, а не утверждение «система не работает». Код и фикстуры работают. Открытыми остаются три блокера, и ни один из них не снимается кодом:
>
> - **RT-001** — нет корпуса российской проектной документации с заключениями экспертизы. Открытые AEC-Bench, IFC-Bench и GNI существуют, но это другой контур.
> - **RT-002** — нет профиля приёмки, подписанного заказчиком. Официальные IDS Мособлгосэкспертизы лежат в этом репозитории, но это не одно и то же.
> - **RT-003** — коллизии MEP на объединённой модели **NOT_VERIFIED**. Инвентарь публичных объединённых моделей измерен, сам прогон коллизий — нет.
>
> Реестр блокеров: [`audit/reports/CRITICAL_BLOCKERS.md`](audit/reports/CRITICAL_BLOCKERS.md) · граница утверждений: [`docs/pilot-claim-boundary-2026.md`](docs/pilot-claim-boundary-2026.md) · владение вердиктом: [`docs/architecture/ADR-001-verdict-ownership-2026.md`](docs/architecture/ADR-001-verdict-ownership-2026.md) · инженерный статус: [`docs/ENGINEERING_STATUS_2026_08.md`](docs/ENGINEERING_STATUS_2026_08.md).
>
> Не заявляется до доказательств: точность продукта >90%, DWG-ready, MEP delivered, CDE-ready BCF, независимая корректность расчётов. Зелёный прогон на фикстурах — не подписание.

## Задача

На листе PDF в ведомости площадей стоит одно число, у стены IFC с тем же GUID — другое. Каждый файл по отдельности выглядит корректно: дефект существует только между ними и обычно всплывает уже на площадке. AeroBIM поднимает находку с прослеживаемостью до листа и до GUID, оставляет вердикт эксперту и никогда не подписывает переход Shared → Published.

## Как это работает

Комплект на входе, детерминированные проверки, один сводный отчёт:

- **IFC** — проверка свойств и величин на IfcOpenShell: IFC2x3, IFC4 и IFC4x3 проходят через одно ядро.
- **IDS 1.0** — проверка на IfcTester, включая официальные наборы правил Мособлгосэкспертизы, которые лежат в `samples/`.
- **Сопоставление документов** — модель против аннотаций чертежа, спецификаций и расчётных текстов, с полем допуска по ISO 12006-3.
- **Отчёт** — прослеживаемость каждой находки (`finding_id`, `source_id`, `evidence_refs`), таблица доступности проверок, выгрузка в HTML и JSON, структурный архив BCF 2.1 / 3.0.

Результат проверяем по двум причинам. Вердикт детерминирован: одинаковый вход даёт одинаковый `summary.passed`. И молчание никогда не считается успехом: каждая опциональная проверка отчитывается статусом `ok`, `skipped` или `failed`, а любое значение `FAILED` принудительно ставит `summary.passed=false` — отключённый движок не может выглядеть как чистый проход.

Рамка соответствует ISO 19650: AeroBIM готовит доказательства для состояния *Shared* и никогда не выдаёт контрактную авторизацию *Published*. Архитектура: [`docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md`](docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md).

## Где применимо

Проверка комплекта до стройки — экспертиза, ГИП, контроль качества документации — на стыке модели, чертежей и требований. Не замена среде общих данных и не полевой журнал дефектов.

## Возможности

Все статусы ниже — уровень репозитория или фикстур, если не указано иное. Результат на фикстурах не является точностью продукта: корпус заказчика, который позволил бы такое утверждение, — это блокер RT-001.

| Возможность | Статус | Доказательства | Примечание |
|---|---|---|---|
| Проверка свойств и величин IFC | Доступно | fixture | IfcOpenShell; IFC2x3, IFC4, IFC4x3 через одно ядро |
| Проверка IDS 1.0 | Доступно | fixture | IfcTester; запрошенный набор правил, который не загрузился, роняет проверку |
| Междокументные противоречия | Доступно | fixture | Таксономия `ConflictKind` (подмножество), настраиваемая критичность |
| Аннотации чертежа ↔ IFC | Доступно | fixture | Заявленный GUID становится `ifc_guid` только после подтверждения в пространственном индексе; без ручного разбора |
| Допуски ISO 12006-3 (поле ε) | Доступно | fixture | — |
| Извлечение требований из текста | Доступно | fixture | Детерминированные шаблоны; ни одна модель ничего не подписывает |
| Бенчмарк извлечения (русский AEC) | Доступно | fixture | macro_f1 на корпусе фикстур не является точностью продукта |
| Метаданные отчёта в логике ISO 19650 | Доступно | fixture | Только стадия, ревизия и контейнер — не среда общих данных |
| Просмотр IFC в браузере и оверлей 2D | Доступно | fixture | Оболочка ревью на web-ifc и Three.js |
| Честность доступности проверок | Доступно | fixture | `FAILED` блокирует `summary.passed`; отдаётся на `/v1/system/capabilities` |
| Прослеживаемость находки | Доступно | fixture | `finding_id`, `source_id`, `evidence_refs`; без них находка не сохраняется |
| Разграничение доступа к артефактам | Доступно | fixture | Principal по Bearer или OIDC против `tenant_id` отчёта |
| Экспорт BCF 2.1 / 3.0 | Доступно | fixture | Структурный архив, два независимых потребителя, приём файлов; импорт в сторонний CDE остаётся NOT_VERIFIED |
| Выгрузка отчёта в HTML и JSON | Доступно | fixture | — |
| Детерминированная работа с PDF | Доступно | core | pypdfium2 + pdfminer; по умолчанию `AEROBIM_PDF_BACKEND=pdfium` |
| Автономная сборка Docker | Доступно | eng | Подтверждено прогоном `closed-contour --smoke`; без Docker — вне scope |
| Паки нормативных правил | Доступно | eng | Правила применимости и журнал эксперта; пак-фикстура не является подписанным профилем заказчика |
| Инвентарь комплектности | Доступно | eng | По желанию; не нормативный вывод о комплектности |
| Протокол измерения качества | Доступно | protocol | Интервалы Уилсона и планировщик объёма выборки; промежуточный ориентир 0.60 |
| Конверт открепленной подписи | Частично | fixture | Только хеши и роли; цепочка доверия остаётся NOT_VERIFIED |
| Коллизии (IfcClash) | Optional extra | optional | `.[clash]`; репетиция движка, а не системные коллизии MEP; при обязательном требовании SKIPPED становится FAILED |
| OCR изображений (RapidOCR) | Optional extra | optional | `.[raster]`; нулевой результат при запрошенном OCR становится FAILED |
| PyMuPDF | Optional extra | `pdf-agpl` | Двойная лицензия AGPL-3.0 / Artifex; нет в runtime lock и в образе Docker |
| Советующий контур LLM и VLM | Экспериментально | fixture | Только черновик формулировки замечания, никогда не пишет `summary.passed`; на профилях заказчика внешние вызовы запрещены |
| OpenCDE BCF API push | Экспериментально | — | Не заменяет доказанный импорт в CDE заказчика |
| Граф знаний по IFC | Экспериментально | fixture | Советующий контур запросов |
| Приём DXF | Частично, не проверено | fixture | Опциональный ezdxf; не поддержка DWG |
| Нативный разбор DWG | Missing | — | Fail-closed и никогда не OK; принимается PDF или IFC как производный вход с прослеживаемостью |
| Human-level CV / чтение чертежа | Missing | — | Деградация OCR не является машинным чтением чертежа |
| Системные коллизии MEP | Не проверено | только fixture | Всегда `geometry_verified=False`; публичные объединённые модели не измерены (RT-003) |
| Независимая корректность расчётов | Не реализовано | — | Источники сверяются, ничего не пересчитывается |
| Браузерная сессия OIDC | Не реализовано | lab | По умолчанию 501; лабораторный контур cookie не является production SSO |
| Импорт BCF в независимый CDE | Не проверено | — | Чек-лист и верификатор готовы; нет реального журнала CDE с хешами |
| Точность >90% и утверждённые нормы | Blocked | customer | Требует корпуса (RT-001) и подписанного профиля (RT-002) |

### Совместимость с IFC

IFC2x3 (ISO 16739:2005), IFC4 ADD2 (ISO 16739-1:2018) и IFC4x3 (ISO 16739-1:2024) проходят через одни и те же адаптеры проверки, фикстуры всех трёх релизов лежат в `samples/ifc/`. Расхождение имён наборов свойств между релизами выдаётся как `ValidationIssue`, а не как молчаливый пропуск. Правила деградации по функциям: [docs/ifc-compatibility-matrix.md](docs/ifc-compatibility-matrix.md).

### Доказательства по BCF

Экспорт доказан, импорт в чужую среду общих данных — нет, и эти две вещи умышленно разделены. Структурный архив доступен (`/export/bcf`, для BCF 3.0 — `?version=3`) и подтверждён двумя независимыми потребителями: [`audit/evidence/bcf-structural-handoff-2026-07-25.json`](audit/evidence/bcf-structural-handoff-2026-07-25.json). Импорт в независимый CDE остаётся NOT_VERIFIED — [`audit/evidence/cde-import-proof/STATUS.json`](audit/evidence/cde-import-proof/STATUS.json) — а точность обратного обмена заблокирована за ним. До появления такого доказательства формулировка «BCF готов к CDE» запрещена. Полная лестница: [`docs/architecture/BCF_EVIDENCE_LADDER_T0_T4_2026_07.md`](docs/architecture/BCF_EVIDENCE_LADDER_T0_T4_2026_07.md).

## Быстрый старт

```bash
git clone https://github.com/KonkovDV/AeroBIM.git
cd AeroBIM/backend

# CPython 3.12 — версия, зафиксированная в CI. Windows: py -3.12 -m venv .venv
python3.12 -m venv .venv
source .venv/bin/activate   # Linux/macOS

# Базовая работа с PDF — pypdfium2; оверлею PyMuPDF не нужен
pip install -e ".[dev,raster]"

# 1. Проверка приёмки на фикстуре IFC + IDS
python -m aerobim.tools.run_demo_ifc_acceptance_gate
# → artifacts/ifc-acceptance-gate-demo/{report.html,acceptance-gate.json}

# 2. Тот же комплект с оверлеем на чертеже
python -m aerobim.tools.run_demo_vertical_slice
# → artifacts/vertical-slice-demo/report.html: фрагмент листа, оверлей,
#   текстовые доказательства, таблица проверок, манифест прогона, архив BCF

pytest tests -q
python -m aerobim.main   # → http://127.0.0.1:8080/health
```

Оба демо заканчиваются с `summary.passed=false`, и это ожидаемый результат: в комплекте-фикстуре заложены дефекты. Это фикстуры, а не данные заказчика, и полученные на них числа не являются точностью продукта.

Дополнительные наборы зависимостей: `.[clash]` — геометрические коллизии, `.[docling]` — разбор нетекстовых документов, `.[enterprise]` — адаптеры S3 и Postgres, `.[pdf-agpl]` — устаревшие инструменты на PyMuPDF (для всего выше не нужны).

## API

| Метод | Путь | Назначение |
|---|---|---|
| `GET` | `/health` | Проверка готовности |
| `GET` | `/v1/system/capabilities` | Заявленная граница возможностей, включая то, чего нет |
| `POST` | `/v1/uploads` | Приём файлов; возвращает путь относительно хранилища |
| `POST` | `/v1/validate/ifc` | Проверка IFC против требований и IDS |
| `POST` | `/v1/analyze/project-package` | Полный анализ комплекта: модель, чертежи, спецификация, расчёт |
| `POST` | `/v1/analyze/project-package/submit` | Постановка крупного комплекта в фоновую очередь |
| `GET` | `/v1/reports` | Список сохранённых отчётов с фильтрами |
| `GET` | `/v1/reports/{id}/export/{json,html,bcf}` | Выгрузка отчёта; `?version=3` переключает BCF 3.0 |
| `POST` | `/v1/reports/{id}/review-events` | Телеметрия ревью; на вердикт не влияет |

## Архитектура

Пять слоёв, зависимости направлены только внутрь:

```
core/            DI-контейнер, токены, конфигурация (без импортов проекта)
domain/          Неизменяемые модели, порты-Protocol, контракт логирования
application/     Оркестрация сценариев: сведение требований, поиск противоречий
infrastructure/  Адаптеры: IfcOpenShell, IfcTester, Docling, IfcClash, BCF, хранилище
presentation/    HTTP-слой FastAPI, middleware корреляции
```

**48 Protocol ports** связаны с **72 adapter modules** через **63 DI tokens** в `bootstrap_container()`. Это живой инвентарь: он пересобирается в [`docs/evidence/runtime-baseline-latest.json`](docs/evidence/runtime-baseline-latest.json) и сверяется в CI против обоих README, поэтому руками эти числа не правятся.

Артефакты лежат за портом `ObjectStore`, поэтому локальное хранилище и совместимые с S3 бакеты — один и тот же путь в коде. При заданном `AEROBIM_DB_URL` сводки отчётов дополнительно индексируются в Postgres; для пилота это допустимо, но до промышленной эксплуатации схему следует переносить миграцией вне приложения.

Полная таблица переменных окружения — в [README.md](README.md), раздел Configuration.

## Разработка

Локально запускается то же, что и в CI:

```bash
cd backend
python -m ruff format --check src tests
python -m ruff check src tests
python -m mypy src
pytest tests -q
```

Измерения — это воспроизводимые команды, а не сохранённые числа:

```bash
python -m aerobim.tools.benchmark_project_package --iterations 1 --warmup-iterations 0
python -m aerobim.tools.measure_package_sla --corpus-kind fixture
python -m aerobim.tools.evaluate_extraction --min-macro-f1 0.70
python -m aerobim.tools.verify_bcf_structural_handoff
python -m aerobim.tools.export_runtime_baseline
python -m aerobim.tools.export_evidence_bundle \
  --pack ../samples/benchmarks/project-package-techlab-demo.json \
  --output ../artifacts/evidence-bundle/techlab-demo
```

Показатели производительности и F1 зависят от среды и относятся к фикстурам. Любое утверждение о производительности публикуется вместе с путём к паку, флагами запуска, отпечатком машины и хешами артефактов. Метаданные цитирования: [`CITATION.cff`](CITATION.cff) и [`docs/CITATION.bib`](docs/CITATION.bib).

## Документация

В репозитории публикуется проверяемый набор: код, требования, границы утверждений, архитектура и доказательства. Служебные инструкции оператора и рабочие журналы сессий умышленно не публикуются.

| Тема | Документ |
|---|---|
| Начать здесь | [`docs/TIER0_INDEX.md`](docs/TIER0_INDEX.md) · [`docs/README.md`](docs/README.md) |
| Пакет подачи КТ#2 | [`submission/README.md`](submission/README.md) |
| Реестр блокеров и checkpoint | [`audit/reports/CRITICAL_BLOCKERS.md`](audit/reports/CRITICAL_BLOCKERS.md) |
| Что заявляется, а что нет | [`docs/pilot-claim-boundary-2026.md`](docs/pilot-claim-boundary-2026.md) · [`docs/capability-claim-matrix-2026.md`](docs/capability-claim-matrix-2026.md) · [`audit/reports/CLAIMS_LOCK_2026_07_17.md`](audit/reports/CLAIMS_LOCK_2026_07_17.md) |
| Инженерный статус | [`docs/ENGINEERING_STATUS_2026_08.md`](docs/ENGINEERING_STATUS_2026_08.md) · [`docs/PROJECT_STATUS_AUDIT_2026.md`](docs/PROJECT_STATUS_AUDIT_2026.md) |
| Принятые риски | [`docs/quality/ACCEPTED_RISKS_REGISTRY_KT2_2026_08_09.md`](docs/quality/ACCEPTED_RISKS_REGISTRY_KT2_2026_08_09.md) |
| Архитектура | [`docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md`](docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md) · [`docs/architecture/ADR-001-verdict-ownership-2026.md`](docs/architecture/ADR-001-verdict-ownership-2026.md) |
| Требования и трассировка | [`docs/tz/README.md`](docs/tz/README.md) · [`docs/samolet.md`](docs/samolet.md) · [`docs/docs.md`](docs/docs.md) |
| Как измеряется качество | [`docs/pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md`](docs/pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md) · [`docs/benchmark-evidence-2026.md`](docs/benchmark-evidence-2026.md) |
| Фикстуры, корпуса, доказательства | [`docs/evidence/README.md`](docs/evidence/README.md) · [`samples/benchmarks/README.md`](samples/benchmarks/README.md) · [`samples/benchmarks/open-corpora/README.md`](samples/benchmarks/open-corpora/README.md) |
| Лицензии и автономное развёртывание | [`docs/license-policy-2026.md`](docs/license-policy-2026.md) · [`docs/offline-deployment-2026.md`](docs/offline-deployment-2026.md) |
| Воспроизводимость | [`docs/REPRODUCIBILITY-2026.md`](docs/REPRODUCIBILITY-2026.md) |

<!-- AEROBIM_DOCUMENTED_ENV:BEGIN -->
<!-- machine-checked parity list (export_runtime_baseline --check-readme)
AEROBIM_ALLOW_ANONYMOUS_DEV
AEROBIM_API_BEARER_TOKEN
AEROBIM_API_TENANT_ID
AEROBIM_APP_NAME
AEROBIM_BCF_API_BASE_URL
AEROBIM_BCF_API_PROJECT_ID
AEROBIM_BCF_API_TOKEN
AEROBIM_BCF_API_VERSION
AEROBIM_BSI_API_TOKEN
AEROBIM_BSI_VALIDATION_URL
AEROBIM_CLASH_AFFECTS_PASS
AEROBIM_CLASH_MIN_AABB_VOLUME_M3
AEROBIM_CLASH_SKIP_TINY
AEROBIM_CORS_ORIGINS
AEROBIM_CROSS_DOC_SEVERITY
AEROBIM_DB_URL
AEROBIM_DEBUG
AEROBIM_ENV
AEROBIM_GATES_ATTESTED
AEROBIM_HOST
AEROBIM_HTTP_RATE_LIMIT_PER_MINUTE
AEROBIM_HYBRID_PROVIDER_CONFIG
AEROBIM_IFC_PARSE_CACHE_DIR
AEROBIM_KIMI_API_BASE_URL
AEROBIM_KIMI_API_KEY
AEROBIM_KIMI_CACHE_DIR
AEROBIM_KIMI_CACHE_NAMESPACE
AEROBIM_KIMI_CACHE_PROJECT
AEROBIM_KIMI_MODEL
AEROBIM_KIMI_REASONING_EFFORT
AEROBIM_LLM_429_RETRIES
AEROBIM_LLM_ADVISORY_ENABLED
AEROBIM_LLM_ADVISORY_MAX_ISSUES
AEROBIM_LLM_ALLOWED_HOSTS
AEROBIM_LLM_API_KEY
AEROBIM_LLM_AUTH_SCHEME
AEROBIM_LLM_BASE_URL
AEROBIM_LLM_BUDGET_LEDGER
AEROBIM_LLM_BUDGET_TZ
AEROBIM_LLM_DATA_LOGGING_ENABLED
AEROBIM_LLM_FOLDER_ID
AEROBIM_LLM_LOCAL_ENABLED
AEROBIM_LLM_MAX_COMPLETION_TOKENS
AEROBIM_LLM_MAX_CONCURRENT
AEROBIM_LLM_MAX_TOKENS_PER_CALL
AEROBIM_LLM_MAX_TOKENS_PER_DAY
AEROBIM_LLM_MAX_TOKENS_PER_RUN
AEROBIM_LLM_MODEL
AEROBIM_LLM_MODEL_REVISION
AEROBIM_LLM_MODEL_SHA256
AEROBIM_LLM_PROVIDER
AEROBIM_LLM_RESPONSE_FORMAT_MODE
AEROBIM_LLM_SEND_SEED
AEROBIM_LLM_TIMEOUT_SECONDS
AEROBIM_MAX_IFC_BYTES
AEROBIM_MEP_AABB_FILTER
AEROBIM_MEP_FEDERATED_SCOPE_PATH
AEROBIM_MEP_SCOPE_MEMO_REF
AEROBIM_NORM_RULE_PACK
AEROBIM_OIDC_AUDIENCE
AEROBIM_OIDC_BFF_AUTHORIZE_URL
AEROBIM_OIDC_BFF_CLIENT_ID
AEROBIM_OIDC_BFF_CLIENT_SECRET
AEROBIM_OIDC_BFF_COOKIE_SECRET
AEROBIM_OIDC_BFF_REDIRECT_URI_ALLOWLIST
AEROBIM_OIDC_BFF_TOKEN_URL
AEROBIM_OIDC_ISSUER
AEROBIM_OIDC_JWKS_EXTRA_HOSTS
AEROBIM_OIDC_JWKS_URL
AEROBIM_OIDC_ROLES_CLAIM
AEROBIM_OIDC_TENANT_CLAIM
AEROBIM_PDF_BACKEND
AEROBIM_PORT
AEROBIM_PRIORITY_PROFILE
AEROBIM_REDIS_URL
AEROBIM_REMARK_LOCALE
AEROBIM_REPORT_TTL_DAYS
AEROBIM_REQUIRE_CLASH
AEROBIM_REQUIRE_MEP_SYSTEM_CLASH
AEROBIM_S3_ACCESS_KEY_ID
AEROBIM_S3_BUCKET
AEROBIM_S3_ENDPOINT_URL
AEROBIM_S3_PREFIX
AEROBIM_S3_REGION
AEROBIM_S3_SECRET_ACCESS_KEY
AEROBIM_SIGNOFF_PROFILE
AEROBIM_STORAGE_DIR
AEROBIM_TRUSTED_PROXY_IPS
AEROBIM_VLM_ENABLED
-->
<!-- AEROBIM_DOCUMENTED_ENV:END -->

## Структура репозитория

```text
backend/      Сервис FastAPI: core → domain → application → infrastructure → presentation
frontend/     Оболочка ревью в браузере
samples/      Фикстуры IFC, IDS, чертежей и спецификаций; бенчмарк-паки
docs/         Документация и артефакты доказательств
audit/        Claims lock, реестр блокеров, цитируемые фикстуры честности
submission/   Пакет подачи к КТ#2
```

Объём кода и зафиксированные CI счётчики пройденных тестов генерируются, а не пишутся руками:

<!-- AEROBIM_RUNTIME_BASELINE:BEGIN -->
<!-- regenerated by: python -m aerobim.tools.export_runtime_baseline -->
tests_passed: backend=2167, frontend=54; commit 88e726be20bc; see docs/evidence/runtime-baseline-latest.json · src ~74536 LOC; tests ~48215 LOC; extraction macro_f1=0.8600000000000001 (fixture corpus; not product accuracy)
<!-- AEROBIM_RUNTIME_BASELINE:END -->

## Стек

Python 3.12+ с FastAPI и Uvicorn. Работу с IFC выполняет набор buildingSMART — IfcOpenShell, IfcTester, IfcClash; оболочку ревью в браузере — web-ifc и Three.js; PDF обрабатывают pypdfium2 и pdfminer.six, а PyMuPDF, RapidOCR и Docling подключаются как опциональные наборы. Пятислойная чистая архитектура, внедрение зависимостей через конструктор, порты на Protocol.

## Лицензия

MIT для кода, написанного в этом репозитории. Сторонние компоненты сохраняют свои лицензии: pypdfium2, pdfminer.six и Pillow — разрешительные; IfcOpenShell и IfcTester — LGPL-3.0+; web-ifc — MPL-2.0; PyMuPDF имеет двойную лицензию AGPL-3.0 / Artifex, поэтому остаётся опциональным набором и отсутствует в runtime lock и в образе Docker.

Машиночитаемый реестр: [`audit/dependency_license_inventory.json`](audit/dependency_license_inventory.json) · политика: [`docs/license-policy-2026.md`](docs/license-policy-2026.md). Это не юридическое заключение, и продукт в целом нельзя описывать как MIT без раскрытия сторонних компонентов.
