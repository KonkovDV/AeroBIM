<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock" -->
# AeroBIM

[English version](README.md)

[![CI](https://github.com/KonkovDV/AeroBIM/actions/workflows/ci.yml/badge.svg)](https://github.com/KonkovDV/AeroBIM/actions/workflows/ci.yml)
[![Checkpoint](https://img.shields.io/badge/checkpoint-GO-brightgreen.svg)](docs/pilot-claim-boundary-2026.md)
[![Customer sign-off](https://img.shields.io/badge/customer_sign--off-NO__GO-red.svg)](audit/reports/CRITICAL_BLOCKERS.md)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**AeroBIM проверяет комплект на согласованность с самим собой.** Площадь в ведомости против площади в IFC, отметка в ПД против отметки в РД, требование ТЗ против фактического наполнения — на публичных машиночитаемых требованиях экспертизы (IFC + IDS + листы + текст спецификаций). Каждый файл по отдельности может открываться чисто. Дефект живёт в шве и обычно всплывает на площадке.

На выходе — находки с прослеживаемостью до листа и GUID: HTML, JSON, PDF (черновик покрытия) и структурный BCF. Решение остаётся за экспертом. AeroBIM — не среда общих данных, не просмотрщик модели и не замена специалисту. Проверщики модели вроде Tangl работают на модели; СОД вроде 10D — на наличии, версиях и маршрутах. Этот репозиторий работает на **шве между файлами**. Это не коннектор Tangl и не СОД.

С 2 апреля 2026 года ЦИМ АГР в IFC обязателен к подаче в Москве (постановление Правительства Москвы № 17-ПП от 16 января 2026; совместное распоряжение ДИТ и ДГП № ДГП-Р-1/26/64-16-6/26). С 18 августа 2026 совместное распоряжение ДГП/ДИТ № ДГП-Р-56/26/64-16-473/26 уточняет требования к трёхмерным моделям в информационных системах Москвы. Это **городские правила подачи**, не подписанный профиль приёмки Самолёта и не заявление о точности продукта. Городской мэппинг АГР IFC опубликован под Revit; AeroBIM нативный RVT не принимает.

Программа Техлаба Москва, задача по автоматизированной верификации проектной и рабочей документации, заказчик — ГК «Самолёт». Статус программы — не измеренный результат на комплекте Самолёта. Индекс пакета: [`submission/README.md`](submission/README.md).

> Мы на стадии доработки контура заказчика. Одна команда показывает находку с доказательствами на учебном комплекте. Валидация эффективности и внедрение у назначающей стороны ещё не начались. Checkpoint `GO` — регуляторно-измерительный MVP. `customer_go` остаётся false, пока нет независимого размеченного корпуса, двух разметчиков, подписанного профиля назначающей стороны и подтверждения импорта в СОД.

## Что делает клон

| Запрос | Что реально делает git |
|---|---|
| Приём 2D + BIM + тексты | IFC 2x3 / 4 / 4x3, IDS 1.0, PDF вектор/растр, текст спецификации |
| Сверка модели, чертежей, правил | Детерминированные IFC + IDS + междокументное сравнение (настраиваемая ε-полоса) |
| Подсветка и замечание | Оверлей 2D, оболочка ревью 3D, шаблоны RU/EN, HITL эксперта |
| Отчёт для координации | HTML + JSON + PDF (черновик покрытия) + структурный архив BCF 2.1 / 3.0 |
| Эксперт остаётся ответственным | `summary.passed` — Shared-gate. Языковая модель его не пишет ([ADR-001](docs/architecture/ADR-001-verdict-ownership-2026.md)) |

Молчание никогда не считается успехом: пропущенный обязательный движок не может спрятаться внутри зелёного отчёта.

## Статус

| | |
|---|---|
| **Работает на этом клоне** | Учебные комплекты, проверка IDS с отказом при пропуске, живой CLI, CI, оверлей, структурный BCF, оболочка ревью (находки → замечание → лист/3D → BCF) |
| **Ждёт остатка** | Два разметчика-человека + заключение на тот же том (RT-001b) · подписанный профиль Самолёта (RT-002c) · system-aware clash (речь **RT-003c**) · федеративный IFC заказчика (`c_customer_federated_ifc`) · импорт BCF в их СОД |
| **Не заявляется** | Точность продукта >90% · SLA заказчика ≤30 мин · native DWG · native RVT/NWD · MEP delivered · CDE-ready BCF · production-ready |

Граница: [`docs/pilot-claim-boundary-2026.md`](docs/pilot-claim-boundary-2026.md). Блокеры: [`audit/reports/CRITICAL_BLOCKERS.md`](audit/reports/CRITICAL_BLOCKERS.md). Карта: [`docs/TIER0_INDEX.md`](docs/TIER0_INDEX.md).

## Попробовать

```bash
git clone https://github.com/KonkovDV/AeroBIM.git
cd AeroBIM/backend

python3.12 -m venv .venv            # Windows: py -3.12 -m venv .venv
source .venv/bin/activate           # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -e ".[dev,raster]"

# 1. Проверка приёмки IFC + IDS на учебном комплекте
python -m aerobim.tools.run_demo_ifc_acceptance_gate

# 2. Тот же комплект с оверлеем и BCF
python -m aerobim.tools.run_demo_vertical_slice

# 3. Трек сидящего члена жюри: живой гейт + пакет + шесть задач трекера
python -m aerobim.tools.run_kt3_jury
# → artifacts/kt3-jury/latest.json (passed=false, GUID-находка)
# → artifacts/kt3-without-customer/latest.json

# 4. Опциональная оболочка ревью в браузере (не CLI жюри; не СОД)
python -m aerobim.tools.run_review_stand
# → http://127.0.0.1:5173/  (API на 8080)
# из корня: python scripts/run_review_shell.py
# Windows PowerShell (обязательный префикс .\ ):
#   .\start.bat
# Не вводить: start          (Start-Process; запросит FilePath)
# Не вводить: start.bat     (PowerShell не запускает .bat из cwd)

pytest tests -q
# Чистый клон: 0 failed. Опциональные extra — skip. Локальный счётчик — не CI pin ниже.
python -m aerobim.main   # → http://127.0.0.1:8080/health
```

Оба демо заканчиваются `summary.passed=false`: в учебном комплекте посажены дефекты. Эти числа — не точность продукта. Красный бейдж — **подпись заказчика** (`customer_go` false), не продукт Checkpoint `NO_GO`.

Дополнительные наборы: `.[clash]` геометрические коллизии, `.[docling]` нетекстовые документы, `.[enterprise]` S3/Postgres, `.[pdf-agpl]` PyMuPDF (для команд выше не нужны). Из `frontend/`: `npm start` (`npm ci`, если Vite ещё не ставили).

## Оболочка ревью

Рабочее место в браузере над **сохранёнными отчётами**. UI никогда не пишет `summary.passed` ([ADR-001](docs/architecture/ADR-001-verdict-ownership-2026.md)). Нативные RVT/NWD/DWG отвергаются до загрузки. По умолчанию `GET /v1/auth/bff` = 501. Лабораторная cookie — не SSO заказчика. Один клик репетиции: только development `POST /v1/demo/seed-fixture` (в OpenAPI нет; git-фикстуры, не комплект заказчика) или законченное задание анализа открывает находки, замечание, оверлей, 3D и BCF на одном экране.

Подробности: [`frontend/README.md`](frontend/README.md).

## Что происходит за один прогон

Комплект на входе. Детерминированные проверки. Один сводный отчёт.

1. **Модель.** Свойства и величины проверяются через IfcOpenShell. IFC2x3 (схема buildingSMART; публикации ISO нет), IFC4 ADD2 (ISO 16739-1:2018) и IFC4x3 (ISO 16739-1:2024) идут через одно ядро. ISO/PAS 16739:2005 — это IFC2x Platform, не IFC2x3. Расхождение имён наборов свойств между релизами выдаётся как `ValidationIssue`, а не как молчаливый пропуск. Правила по функциям: [`docs/ifc-compatibility-matrix.md`](docs/ifc-compatibility-matrix.md).
2. **Правила.** IDS 1.0 проверяется через IfcTester. Официальные наборы Мособлгосэкспертизы и СПб ГАУ ЦГЭ (ЦИМ ОКС ред. 3.1.0 + ЦИМ РИИ ред. 1.1.0) лежат в `samples/`; профиль ЦГЭ ([`samples/profiles/spb-cge/`](samples/profiles/spb-cge/manifest.json)) — опубликованный набор правил (OFFICIAL_PUBLISHED), а не подписанный заказчиком профиль приёмки. CI на `ubuntu-latest` гоняет `python -m aerobim.tools.validate_spb_cge_profile --no-write --verify-committed-evidence`: подмена `.ids` или устаревший SHA evidence валит сборку. Запрошенный набор, который не загрузился, роняет проверку — он не может выглядеть как чистый проход.
3. **Остальные документы.** Модель сопоставляется с пометками на чертеже, спецификациями и расчётными текстами, с настраиваемой ε-полосой и с русскими/европейскими группированными числами. Источники сверяются; ничего не пересчитывается. Независимая корректность расчётов не реализована.
4. **Отчёт.** У каждой находки есть `finding_id`, `source_id` и `evidence_refs` (без них находка не сохраняется). Людям — HTML, машинам — JSON, для обмена замечаниями — структурный архив BCF 2.1 / 3.0. Оболочка ревью в браузере (web-ifc + Three.js) показывает IFC в 3D и доказательства на листе.

Результат можно проверить по двум причинам.

- **Одинаковый вход — одинаковый `summary.passed`.** Технический флаг собирается из детерминированных ошибок и таблицы доступности проверок ([ADR-001](docs/architecture/ADR-001-verdict-ownership-2026.md)). Если советующий текст языковой модели включён, он только черновит формулировку замечания и никогда не пишет `summary.passed`. На профилях заказчика внешние вызовы советующего контура запрещены.
- **Молчание никогда не считается успехом.** Каждая опциональная проверка отчитывается статусом `ok`, `skipped` или `failed`. Любое значение `FAILED` принудительно ставит `summary.passed=false`. Отключённый движок коллизий не может спрятаться внутри зелёного отчёта. Та же граница отдаётся на `GET /v1/system/capabilities`.

`summary.passed` — прохождение настроенного Shared-gate: технический статус «проверки прошли». Это не контрактная «пригодность документации» и не разрешение строить. Архитектура: [`docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md`](docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md).

```mermaid
flowchart LR
  pack["IFC + IDS + чертежи + тексты"] --> checks["Детерминированные проверки"]
  checks --> report["Отчёт с доказательствами"]
  report --> reviewer["Решает эксперт"]
```

## Checkpoint: `GO` (`regulatory_measurement_mvp`)

Продуктовый Checkpoint — **регуляторно-измерительный MVP**. `customer_go` остаётся **false**. Это не утверждение «система не работает». Код и учебные комплекты работают. **Подмены измерения** закрывают то, чего нет от Самолёта. Недифференцированные `closes_rt001/002/003` остаются false. Красный бейдж подписи заказчика не читать как продукт `NO_GO`.

| ID | Подмена измерения (без Самолёта) | Остаток (не подменяется) |
|---|---|---|
| **RT-001** | `a_content_pairing` **CLOSED** (**RT-001a**) — типовые замечания экспертизы РФ (эксперимент Б) + публичные IDS + учебный комплект / инъекция. `b_protocol_rehearsal` **CLOSED** — два независимых симулированных прохода на том же учебном комплекте, живые κ/α/AC1 | `b_criterion_dual_rater` **OPEN** (**RT-001b**) (двое людей + заключение на *тот же* том). `c_customer_corpus` **OPEN**. Открытые бенчмарки — другой контур. Симуляция — не двое людей. Не точность продукта |
| **RT-002** | `a_regulatory` **CLOSED** (**RT-002a**) — публичные IDS (Мособлгосэкспертиза, СПб ГАУ ЦГЭ, городской АГР) как линейка измерения. `b_eir_carrier` **CLOSED** (**RT-002b**) — EIR v4.0 и BIM-стандарт v4.0 на канальном комплекте как **текст** (пин без имён файлов). Публичный IDS экспертизы — не EIR назначающей стороны | `c_corporate_signed` **OPEN** (**RT-002c**; `b_corporate` остаётся OPEN) — подпись Самолёта / `customer_approved` IDS. Текст EIR — не подписанный профиль. Город-издатель — не подпись Самолёта. Не писать недифференцированно «RT-002 CLOSED» |
| **RT-003** | `a_federated_geometric_rehearsal` **CLOSED** (**RT-003a**) — посаженный IfcClash (стены; труба против стены). `b_navis_federation_carrier` **CLOSED** — три NWD-федерации. `b_ifc_system_graph_rehearsal` **CLOSED** (**RT-003b**) — граф `IfcSystem` на HVAC-фикстуре (две системы, `IfcRelAssignsToGroup`); не труба против стены | `b_mep_system_clash` **OPEN** (**RT-003c**, `NOT_VERIFIED`) — 0 duct/pipe/cable в IFC заказчика; EIR называет LOD ОВ/ВК/ИТП/ЭОМ/СС, моделей нет. `c_customer_federated_ifc` **OPEN** — выгрузка NWD→IFC не поставлена. MEP delivered не заявляется |

Машинный SSOT: [`docs/evidence/rt-blocker-volumes-2026-09.md`](docs/evidence/rt-blocker-volumes-2026-09.md) · `python -m aerobim.tools.export_rt_blocker_volumes`.

Экспорт BCF ZIP — структурный T1 ([`audit/evidence/bcf-structural-handoff-2026-07-25.json`](audit/evidence/bcf-structural-handoff-2026-07-25.json)). Импорт в независимую СОД — **NOT_VERIFIED**. Чтение DWG и нативных RVT/NWD отсутствует: отказ, не молчание (вход — IFC). Независимая корректность расчётов не реализована: источники сверяются, а не пересчитываются.

ГОСТ Р 21.101-2026 (приказ Росстандарта № 129-ст от 12 февраля 2026; **в силе с 1 апреля 2026**, взамен 21.101-2020; GUID как идентификатор электронного документа ПД/РД) — правило **идентификации документа**. AeroBIM с первого дня ведёт находки к устойчивому идентификатору. Это совпадение механизма, а не заявление о полном соответствии стандарту. Дата введения стандарта (1 апреля) — не дата обязательной подачи ЦИМ АГР в Москве (2 апреля).

Реестр: [`audit/reports/CRITICAL_BLOCKERS.md`](audit/reports/CRITICAL_BLOCKERS.md). Речь: [`docs/demo/KT2_JURY_FAQ_2026_08_12.md`](docs/demo/KT2_JURY_FAQ_2026_08_12.md) · [`docs/demo/KT3_JURY_FAQ_2026_08_25.md`](docs/demo/KT3_JURY_FAQ_2026_08_25.md).

## OpenBIM и как мы измеряем

| Практика (август 2026) | В этом репозитории | Разрыв до «готово» |
|---|---|---|
| IDS 1.0 как машинный информационный контракт | IfcTester: чужая версия или незагруженный набор роняют проверку | Хеш комплекта заказчика + подписанный профиль (RT-002c) |
| Согласие двух разметчиков до публикации точности | Планировщик Уилсона и harness κ/α есть; κ без меток заказчика нет | Корпус заказчика + два разметчика (RT-001) |
| BCF → СОД | Структурный ZIP (T1) | Журнал импорта T2 в СОД Самолёта |
| ISO 19650 | Lite-поля на отчёте (метаданные Shared-gate) | Это не СОД; ISO 19650-6 — обмен H&S, не этот гейт |
| FAIR research software | `CITATION.cff`, реестр лицензий, воспроизводимые команды | Учебный комплект F1 ≠ точность продукта |

## Что работает сегодня

<details>
<summary>Возможности на учебных комплектах (не точность продукта; корпус заказчика — RT-001)</summary>

Все статусы ниже — уровень репозитория или учебных комплектов, если не указано иное. Результат на фикстурах не является точностью продукта: корпус заказчика, который позволил бы такое утверждение, — это блокер RT-001.

**На комплектах, которые можно клонировать сегодня**

- Проверка свойств и величин IFC; IDS 1.0: если набор правил не загрузился, проверка падает
- Междокументные противоречия (таксономия `ConflictKind`, настраиваемая критичность) и аннотации чертежа ↔ IFC (заявленный GUID становится `ifc_guid` только после подтверждения в пространственном индексе)
- Настраиваемая ε-полоса (SI-нормализация); извлечение требований из текста по детерминированным шаблонам (ни одна модель ничего не подписывает)
- Честность доступности проверок; разграничение доступа к артефактам на профилях `samolet_pilot` / `production` (в development по умолчанию выключено); выгрузка HTML/JSON; PDF — черновик покрытия; структурный архив BCF 2.1 / 3.0
- Детерминированная работа с PDF (pypdfium2 + pdfminer; по умолчанию `AEROBIM_PDF_BACKEND=pdfium`)
- Просмотр IFC в браузере и оверлей 2D; автономная сборка Docker (`closed-contour --smoke`; без Docker — вне scope)
- Паки нормативных правил (применимость и журнал эксперта; учебный пак не является подписанным профилем заказчика) и по желанию инвентарь комплектности (не нормативный вывод)
- Протокол измерения качества (интервалы Уилсона, планировщик выборки; промежуточный ориентир 0.60) — протокол, а не опубликованная оценка продукта

**Опционально, частично или отсутствует**

- Геометрические коллизии: набор `.[clash]` — репетиция движка, а не системные коллизии MEP; при обязательном требовании SKIPPED становится FAILED
- OCR изображений: набор `.[raster]`; нулевой результат при запрошенном OCR становится FAILED
- PyMuPDF: набор `pdf-agpl` (AGPL-3.0 / Artifex); нет в runtime lock и в образе Docker
- Советующий контур LLM/VLM: экспериментальные черновики; никогда не пишет `summary.passed`
- OpenCDE BCF API push: экспериментально; не заменяет доказанный импорт в СОД заказчика
- Граф знаний по IFC: экспериментальный советующий контур запросов
- Приём DXF: опциональный ezdxf, частично и не проверено; это не поддержка DWG
- Конверт открепленной подписи: только хеши и роли; цепочка доверия остаётся **NOT_VERIFIED**
- Браузерная сессия OIDC: не реализовано (по умолчанию 501); лабораторный контур cookie не является промышленным входом по SSO
- Точность >90% и утверждённые нормы: упирается в RT-001 и RT-002

</details>

## HTTP API

<details>
<summary>Точки API (локально <code>python -m aerobim.main</code>)</summary>

`GET /health` без аутентификации. `/v1/*` требует `AEROBIM_API_BEARER_TOKEN`, если не задано `AEROBIM_ALLOW_ANONYMOUS_DEV=true` (только development). Мутирующие маршруты делят один `require_bearer_auth` (контракт CI).

| Метод | Путь | Назначение |
|---|---|---|
| `GET` | `/health` | Проверка готовности |
| `GET` | `/v1/auth/bff` | Обнаружение входа. По умолчанию **501**. Лабораторный `200 LAB` — не SSO заказчика |
| `GET` | `/v1/system/capabilities` | Заявленная граница возможностей, включая то, чего нет |
| `POST` | `/v1/uploads` | Приём файлов; возвращает путь относительно хранилища |
| `POST` | `/v1/validate/ifc` | Проверка IFC против требований и IDS |
| `POST` | `/v1/analyze/project-package` | Полный анализ комплекта: модель, чертежи, спецификация, расчёт |
| `POST` | `/v1/analyze/project-package/submit` | Постановка крупного комплекта в **in-process** `BackgroundTasks` API-процесса (не durable worker). `Idempotency-Key`; тот же ключ и другой payload → 409; лимит на арендатора → 429; отмена через `request_cancel`; вне development записи заданий в Redis; после сбоя процесса `QUEUED` снимает `reclaim_stale_queued` |
| `GET` | `/v1/analyze/project-package/jobs/{job_id}` | Статус фонового задания |
| `POST` | `/v1/analyze/project-package/jobs/{job_id}/cancel` | Отмена задания |
| `GET` | `/v1/reports` | Список сохранённых отчётов с фильтрами |
| `GET` | `/v1/reports/{id}` | Один отчёт |
| `GET` | `/v1/reports/{id}/coverage` | Карта покрытия проверок (четыре состояния) |
| `GET` | `/v1/reports/{id}/revision-diff` | Дельта находок; «не воспроизведено» ≠ исправлено |
| `GET` | `/v1/reports/{id}/export/{json,html,pdf,bcf}` | Выгрузка; `?version=3` — BCF 3.0. PDF — черновик покрытия. XLSX нет |
| `POST` | `/v1/reports/{id}/review-events` | HITL эксперта; `summary.passed` не меняет |
| `GET` | `/v1/reports/{id}/review-events` | История HITL |
| `GET` | `/v1/reports/{id}/review-kpi` | Сводка разбора (не дни цикла в СОД) |
| `POST` | `/v1/demo/seed-fixture` | Только development; git-фикстура; в опубликованном OpenAPI нет |

Полный анализ комплекта может принять отчёт OpenRebar (`reinforcement_report_path`) с дайджестом SHA-256. Это сверка заявленных источников, а не пересчёт. Дайджест: `python -m aerobim.tools.openrebar_provenance_digest`. OpenCDE `POST .../export/bcf-api/push` — экспериментальная отправка в хаб, не доказательство импорта в СОД заказчика.

</details>

## Архитектура

Пять слоёв, зависимости направлены только внутрь:

```
core/            DI-контейнер, токены, конфигурация (без импортов проекта)
domain/          Неизменяемые модели, порты-Protocol, контракт логирования
application/     Оркестрация сценариев: сведение требований, поиск противоречий
infrastructure/  Адаптеры: IfcOpenShell, IfcTester, Docling, IfcClash, BCF, хранилище
presentation/    HTTP-слой FastAPI, middleware корреляции
```

**48 Protocol ports** связаны с **75 adapter modules** через **63 DI tokens** в `bootstrap_container()`. Это живой инвентарь: он пересобирается в [`docs/evidence/runtime-baseline-latest.json`](docs/evidence/runtime-baseline-latest.json) и сверяется в CI против обоих README, поэтому руками эти числа не правятся.

Артефакты лежат за портом `ObjectStore`, поэтому локальное хранилище и совместимые с S3 бакеты — один и тот же путь в коде. При заданном `AEROBIM_DB_URL` сводки отчётов дополнительно индексируются в Postgres; для пилота это допустимо, но до промышленной эксплуатации схему следует переносить миграцией вне приложения.

Локальный клон работает на значениях по умолчанию. Полная таблица `AEROBIM_*` свёрнута в [английском README](README.md), раздел Configuration: CI проверяет её в обе стороны (код → доки и доки → код).

## Документация

В репозитории публикуется проверяемый набор: код, требования, границы утверждений, архитектура и доказательства. Служебные инструкции и рабочие журналы умышленно не публикуются.

| Тема | Документ |
|---|---|
| Начать здесь | [карта для жюри](docs/TIER0_INDEX.md) · [техническое обоснование](docs/docs.md) |
| Пакет подачи | [индекс КТ#3; архив КТ#2](submission/README.md) |
| Речь КТ#3 | [карточка для жюри](docs/demo/KT3_JURY_FAQ_2026_08_25.md) |
| Блокеры | [критические блокеры](audit/reports/CRITICAL_BLOCKERS.md) |
| Что заявляется | [границы заявлений](docs/pilot-claim-boundary-2026.md) |
| Архитектура | [ADR-001](docs/architecture/ADR-001-verdict-ownership-2026.md) · [ADR-005 данные](docs/architecture/ADR-005-customer-data-handling-2026.md) |
| Оболочка ревью | [фронтенд](frontend/README.md) |
| Лицензии | [политика лицензий](docs/license-policy-2026.md) |

## Цитирование

Используйте [`CITATION.cff`](CITATION.cff) (кнопка GitHub «Cite this repository») или [`docs/CITATION.bib`](docs/CITATION.bib). Цитируйте точный Git-тег или SHA коммита, а не плавающий `latest`. Принципы FAIR для исследовательского ПО ([Chue Hong et al., 2022](https://doi.org/10.15497/RDA00068); [Barker et al., *Sci Data*](https://doi.org/10.1038/s41597-022-01710-x)) — это цель документации: назначение, установка, лицензия, цитирование, статус. Этот репозиторий **не** является сертифицированной FAIR-оценкой.

<!-- AEROBIM_DOCUMENTED_ENV:BEGIN -->
<!-- machine-checked parity list (export_runtime_baseline --check-readme)
AEROBIM_ALLOW_ANONYMOUS_DEV
AEROBIM_API_BEARER_TOKEN
AEROBIM_API_TENANT_ID
AEROBIM_APP_NAME
AEROBIM_APPLY_SAMOLET_UPLOAD_CAPS
AEROBIM_BCF_API_BASE_URL
AEROBIM_BCF_API_PROJECT_ID
AEROBIM_BCF_API_TOKEN
AEROBIM_BCF_API_VERSION
AEROBIM_BSI_API_TOKEN
AEROBIM_BSI_VALIDATION_URL
AEROBIM_CLASH_AFFECTS_PASS
AEROBIM_CLASH_MIN_AABB_VOLUME_M3
AEROBIM_CLASH_SKIP_TINY
AEROBIM_CORS_ALLOW_CREDENTIALS
AEROBIM_CORS_ORIGINS
AEROBIM_CROSS_DOC_SEVERITY
AEROBIM_CUSTOMER_PACK_LLM_EGRESS
AEROBIM_CUSTOMER_PACK_LLM_EGRESS_CONSENT_REF
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
AEROBIM_MAX_MODEL_BYTES
AEROBIM_MAX_OFFICE_BYTES
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
frontend/     Оболочка ревью в браузере (IFC 3D и оверлей на чертеже)
samples/      Учебные комплекты IFC, IDS, чертежей и спецификаций; бенчмарк-паки
docs/         Документация и артефакты доказательств
audit/        Claims lock, реестр блокеров, цитируемые фикстуры честности
submission/   Индекс пакета подачи (КТ#3 актуальный; КТ#2 в архиве)
```

Объём кода и зафиксированные CI счётчики пройденных тестов генерируются, а не пишутся руками:

<!-- AEROBIM_RUNTIME_BASELINE:BEGIN -->
<!-- regenerated by: python -m aerobim.tools.export_runtime_baseline -->
tests_passed: backend=3157, frontend=387; commit 90c7927972a3; see docs/evidence/runtime-baseline-latest.json · src ~101025 LOC; tests ~66226 LOC; extraction macro_f1=0.8600000000000001 (fixture corpus; not product accuracy)
<!-- AEROBIM_RUNTIME_BASELINE:END -->

## Стек

Python 3.12+ с FastAPI и Uvicorn. Работу с IFC выполняет набор buildingSMART — IfcOpenShell, IfcTester, IfcClash; оболочку ревью в браузере — web-ifc и Three.js; PDF обрабатывают pypdfium2 и pdfminer.six, экспорт PDF — reportlab, а PyMuPDF, RapidOCR и Docling подключаются как опциональные наборы. Пятислойная чистая архитектура, внедрение зависимостей через конструктор, порты на Protocol.

## Лицензия

MIT для кода, написанного в этом репозитории. Сторонние компоненты сохраняют свои лицензии: pypdfium2, pdfminer.six, Pillow и reportlab — разрешительные; IfcOpenShell и IfcTester — LGPL-3.0+; web-ifc — MPL-2.0; PyMuPDF имеет двойную лицензию AGPL-3.0 / Artifex, поэтому остаётся опциональным набором и отсутствует в runtime lock и в образе Docker.

Машиночитаемый реестр: [`audit/dependency_license_inventory.json`](audit/dependency_license_inventory.json) · политика: [`docs/license-policy-2026.md`](docs/license-policy-2026.md). Это не юридическое заключение, и продукт в целом нельзя описывать как MIT без раскрытия сторонних компонентов.
