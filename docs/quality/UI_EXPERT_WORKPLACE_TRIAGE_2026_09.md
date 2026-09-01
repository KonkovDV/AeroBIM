<!-- claims-lint: allow-file reason="UI expert-workplace Red Team triage; review shell not full cycle; natives fail-closed; NO_GO" -->
---
title: "UI expert-workplace Red Team triage — 2026-09-01"
date: "2026-09-01"
last_updated: "2026-09-01"
status: active
version: "1.0.3"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: coverage_map_only
detected_count: 0
claim_boundary: >
  Review shell vs TZ full-cycle expert seat. Upload → run → triage → remark →
  export is the gap. Natives stay fail-closed. UI does not write summary.passed.
  Not a 10D/Tangl connector. Checkpoint NO_GO.
---

# Триаж рабочего места эксперта (01.09.2026)

Машина: `python -c "from aerobim.domain.ui_expert_workplace_triage import ui_expert_workplace_triage_snapshot"`.

Бэкенд — пять слоёв, порты/адаптеры/токены по CI-пину. Фронт в git — **review shell** над сохранёнными отчётами (`frontend/src/App.tsx`). ТЗ просит полный цикл: загрузил комплект → увидел прогресс → отсмотрел находки → отредактировал замечания → выгрузил отчёт. Половины цепочки в UI не было; этот проход закрывает **проводку** загрузки, джоба, KPI, восьми экранов и **dev-only** `POST /v1/demo/seed-fixture` (git walls+IDS, не заказчик) — не «рабочее место сдано».

Checkpoint **`NO_GO`**. `detected_count: 0`. UI **не** закрывает RT-001 / RT-002 / RT-003.

Позиционирование (не модель-чекер против Tangl/10D): согласованность **комплекта** (модель ↔ чертежи ↔ ТЗ ↔ расчёты ↔ смежные разделы) и файловый выход BCF/HTML/JSON. Импорт в СОД заказчика — **NOT_VERIFIED**.

Связанные: [`FORMAT_INGEST_TRIAGE_2026_09.md`](FORMAT_INGEST_TRIAGE_2026_09.md) · [`../architecture/ADR-001-verdict-ownership-2026.md`](../architecture/ADR-001-verdict-ownership-2026.md) · [`../tz/NATIVE_AUTODESK_INGEST_BOUNDARY_2026.md`](../tz/NATIVE_AUTODESK_INGEST_BOUNDARY_2026.md) · [`TRACKER_EIGHT_TASKS_2026_08.md`](TRACKER_EIGHT_TASKS_2026_08.md).

## Восемь экранов (IA, не delivery)

| ID | Экран | git | Заметка |
|---|---|---|---|
| SCR-PROJECTS | Проекты и комплекты | partial | Список отчётов, не workspace комплекта |
| SCR-UPLOAD | Загрузка комплекта | partial | Dropzone + progress; native fail-closed в копирайте |
| SCR-RUN | Прогон анализа | partial | `jobs/{job_id}`; SSE нет; 30 мин — цель ТЗ, не SLA |
| SCR-EXPERT | Рабочее место эксперта | partial | Resizable 3 панели; клавиатура J/K/A/R/E; windowed list >40 |
| SCR-REMARK | Карточка замечания | partial | HITL + история review-events; этаж/ось или «нет в индексе» |
| SCR-EXPORT | Отчёт и экспорт | partial | HTML JSON BCF 2.1/3.0 PDF; XLSX нет в API |
| SCR-DIFF | Сравнение версий | partial | HTTP finding delta; no_longer_reported ≠ исправлено |
| SCR-USER | Дашборд «Пользователь» | partial | `review-kpi` + карта ТЗ; OIDC BFF 501 |

Стек TanStack Router / Query / Zustand / Radix / Tailwind v4 / Storybook / Playwright / axe-core — **план спринта 0**, не факт git. Не обещать Fragments как продукт: не грузить федерацию ~1 ГБ в вкладку.

## Этот проход (KILL / HOLD / ACCEPT)

| ID | Атака | Тормоз |
|---|---|---|
| RT-UI-PASSED-FRONT | Считать `summary.passed` во фронте | ADR-001: только показ |
| RT-UI-LLM-VERDICT | Текст ИИ как подписанный вердикт | Пометка черновика; HITL |
| RT-UI-GREEN-SKIP | Зелёный отчёт при skipped движке | Тишина ≠ успех |
| RT-UI-ACCURACY | % фикстуры как точность продукта | `detected_count=0` |
| RT-UI-PARSE-BROWSER | 1,5 ГБ модели в браузере | Конвертация на бэкенде; web-ifc — фикстура |
| RT-UI-NATIVE-RVT | UI обещает native RVT/NWD/DWG | Обмен IFC+PDF/A |
| RT-UI-CDE-10D | Кнопки живого 10D/Tangl/CADLib | Файловый обмен; коннекторов нет |
| RT-UI-SLA | 5–10 комплектов/день или 30 мин как SLA | Цель ТЗ, не замер |
| RT-UI-FRAG-FED | Федерация ~1 ГБ .frag во вьюер | Стриминг по этажу или не ship |
| RT-UI-FIO | ФИО сидящих в UI или в этом пине | Брифы — роли |
| RT-UI-XLSX-FAKE | Кнопка XLSX с 404 как «сдано» | Пока HTML/JSON/BCF/PDF |
| RT-UI-OIDC-LIVE | Production SSO при BFF 501 | Две роли — алиасы API |
| RT-UI-NOGO-MASK | Хром UI = Checkpoint GO | Баннер NO_GO |
| RT-UI-STACK-CLAIM | TanStack/Storybook как shipped | Vite + React + vitest |
| RT-UI-SPLIT | Навсегда один App.tsx | Резать по фичам, тесты зелёные |
| RT-UI-THEME | Неон / выдуманный брендбук | Светлая лаконичная; blue alias |
| RT-UI-KEYBOARD | Только мышь на сотнях находок | J/K/A/R/E/? + windowed list >40 |
| RT-UI-JOBS | SSE и таймер 30 мин как продукт | Поллинг jobs |
| RT-UI-KEEP-SHELL | Снести shell до цикла загрузка→отчёт | Shell оставить, петлю добавить |
| RT-UI-HONEST-CAP | Таблица capabilities внизу | Баннеры skipped/failed сверху |
| RT-UI-HITL-REMARK | Нет inline-редактора | `review-events` уже есть |
| RT-UI-COV-MAP | Карта покрытия = точность | Семейства, не `summary.passed` |
| RT-UI-SEAM | Мы заменим Tangl/10D | Шов комплекта; BCF файлом |
| RT-UI-UPLOAD-WIRE | Upload API без UI | Dropzone + fail-closed копирайт |
| RT-UI-KPI-WIRE | review-kpi без экрана | Дашборд эффекта читает KPI |
| RT-UI-EIGHT | Восемь экранов уже продукт | Колонка git = partial/missing |
| RT-UI-DEMO-PROD | Seed-fixture как продуктный API | Вне dev — публичный 404; samples из git |
| RT-UI-DEMO-ACCURACY | Две IDS-находки огнестойкости = точность продукта | `detected_count=0`; PrecisionClaim.publishable |
| RT-UI-DEMO-PACK | Git-seed = пакет заказчика обработан | Только стены+IDS; чертежи/ТЗ/расчёты в этом POST нет |
| RT-UI-SEED-PASSED | Вернуть `passed` в JSON сида, чтобы фронт владел флагом | Сид даёт `report_id` + `issue_count`; флаг с GET отчёта |
| RT-UI-TZ-MATRIX-DONE | Матрица ТЗ Web UI = done как сдача | Строка **partial**; этот пин — SSOT |
| RT-UI-JURY-VITE | Vite как дефолт чужого ноутбука жюри | Ноутбук жюри = `run_kt3_jury`; UI — трек ИТ-ментора |
| RT-UI-STORE-NOISE | Грязный локальный audit store = объём канала | Демо ментора — пустой `AEROBIM_STORAGE_DIR` |
| RT-UI-FONTS | Офлайн-ноутбук падает из-за CDN-шрифтов | Нет `fonts.googleapis.com`; системный UI/mono |
| RT-UI-OPENAPI-DEMO | OpenAPI публикует seed-fixture как продуктный operation | `include_in_schema=False`; роутер только при `is_dev_environment` |
| RT-UI-SEED-VOLUME | `issue_count` сида = объём канала SIG-01 | Счётчик фикстуры; SIG-01 — фраза канала |
| RT-UI-ANON-BIND | Anonymous + не loopback = LAN-сид | Хост по умолчанию 127.0.0.1; anonymous — opt-in |
| RT-UI-DEMO-SEED | Пустой список отчётов = shell нельзя показать | Dev-only git-seed копирует samples под storage |
| RT-UI-VIEWER-ID | Перезагрузка IFC на каждую смену объекта report | Fetch ключ — `report_id` |

## Что UI не закроет

RT-001 (корпус + два оценщика), RT-002b (подпись Самолёта), RT-003 (федеративный MEP). Native DWG нет. Независимый пересчёт ЛИРА нет. Импорт BCF в СОД не доказан. OIDC не реализован.

Не говорить: «рабочее место эксперта сдано»; «RVT читаем в браузере»; «SLA 30 минут измерен»; «интегрированы с 10D»; «две находки фикстуры = точность»; «фронт — показ жюри».

## Два трека показа (речь, не delivery)

| Трек | Кто | Что нажимать | Что нельзя |
|---|---|---|---|
| Жюри КТ#3 | сидящий член, чужой ноутбук | `python -m aerobim.tools.run_kt3_jury` | Vite как дефолт; native RVT; GO |
| ИТ-ментор | локальный `npm run dev` | «Загрузить демонстрационный комплект» | «пакет обработан»; SLA; XLSX сдан |

Ожидаемый IDS-пример на обоих треках — учебные стены: FireRating REI60 vs REI30. Это сценарий фикстуры, не RT-001 CLOSED.

Checkpoint **`NO_GO`**.
