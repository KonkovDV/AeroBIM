<!-- claims-lint: allow-file reason="Frontend plan for the AI executor; forbidden claims quoted only as prohibitions; review shell; NO_GO" -->
---
title: "План развития фронтенда (для ИИ-исполнителя) — 2026-09-03"
date: "2026-09-03"
last_updated: "2026-09-03"
status: active
version: "1.3.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: coverage_map_only
detected_count: 0
claim_boundary: >
  Фронтенд — review shell над сохранёнными отчётами, не полный цикл CDE и не
  коннектор 10D/Tangl. UI не пишет summary.passed (ADR-001). Нативные
  RVT/NWD/DWG — fail-closed. SSE нет, только опрос jobs. Checkpoint NO_GO.
---

# План развития фронтенда — для ИИ-исполнителя

SSOT по рамкам: [`UI_EXPERT_WORKPLACE_TRIAGE_2026_09.md`](UI_EXPERT_WORKPLACE_TRIAGE_2026_09.md).
Операционный синтез КТ#3: [`KT3_HYPERPLAN_TRIAGE_RT_WH_2026_09.md`](KT3_HYPERPLAN_TRIAGE_RT_WH_2026_09.md).
Этот документ — исполняемый план: каждый пакет работ (WP) имеет файлы, шаги,
критерии приёмки и тесты. Исполнитель обязан держать гейты зелёными после
каждого WP, а не «в конце».

## 1. Снимок git после прохода 03.09

Стек (факт, не план): React 19 + TypeScript + Vite 7, Three.js + web-ifc
(lazy-чанк), vitest 4 + Testing Library, Playwright только для
`smoke:browser`. TanStack/Storybook/Tailwind — **не поставлены и не разворачиваются**
(RT-UI-STACK-CLAIM).

Восемь экранов IA (`frontend/src/lib/tz-ui-screens.ts`) — все `partial`.
Каркас: `App.tsx` (292 строки, порог 300 — RT-UI-SPLIT), фичи в
`features/{workplace,findings,export,shell,reports,honesty,capabilities}`,
чистые функции в `lib/`, хуки в `hooks/`.

Гейты на 03.09: `npm test` — 26 файлов / 109 тестов; `npm run lint`
(lint-ui-strings) — чисто; `npm run build` — чисто (web-ifc — отдельный
lazy-чанк, предупреждение о размере — исходное, не регрессия).

## 2. Сделано в проходе 03.09 (baseline этого плана)

| ID | Что | Файлы |
|---|---|---|
| FE-01 | Экспорт: ошибки показываются `role="alert"`, кнопки блокируются на время выгрузки (раньше `void downloadExport` глотал отказ) | `features/export/ExportActionsBar.tsx` |
| FE-02 | Поиск находок (правило/текст/GUID/этаж/ось/категория); воронка фильтров вынесена в чистую `filterTriageIssues` | `lib/issue-triage.ts`, `App.tsx`, `features/findings/FindingListPanel.tsx` |
| FE-03 | Ctrl+Enter сохраняет правку замечания | `features/findings/RemarkCardPanel.tsx` |
| FE-04 | Состав пакета виден на экране загрузки; `packCompositionLine` переехал в `lib/pack-draft.ts` | `components/PackUploadPanel.tsx`, `features/shell/PackScreens.tsx` |
| FE-05 | Бейдж числа находок на вкладке «Эксперт» (aria-hidden, имя кнопки не меняется) | `components/WorkspaceNav.tsx` |
| FE-06 | `aria-live="polite"` у счётчика показанных находок | `features/findings/FindingListPanel.tsx` |
| — | ALLOWED_WORDS линтера: `ctrl`, `enter` (клавиши как enum-токены) | `scripts/ui-latin-scan.mjs` |

Тесты: +7 (поиск/воронка, экспорт-ошибка и busy, бейдж, Ctrl+Enter, состав
пакета). Поведение HITL-фильтра при извлечении сохранено один-в-один
(мёртвая ветка `hasHitlRegion` упрощена до `rule_id === HITL_RULE_ID`,
логическая эквивалентность проверена тестом).

## 3. Жёсткие рамки для исполнителя (нарушение = брак)

1. UI **не пишет** `summary.passed` и не вычисляет вердикт (ADR-001); страж —
   `src/summary-passed-source-scan.test.ts`, не ослаблять.
2. Не заявлять в копирайте: точность продукта в процентах, измеренный SLA
   (30:00 — цель ТЗ, не замер), «CDE-ready», живой импорт BCF в 10D/Tangl,
   native RVT/NWD/DWG, «пакет заказчика обработан» для git-фикстуры.
3. Нет SSE — только опрос `jobs/{job_id}` (RT-UI-JOBS). Нет XLSX-кнопки —
   эндпоинта нет, фальшивый 200 хуже отсутствия (RT-UI-XLSX-FAKE).
4. OIDC не имитировать: BFF = 501, переключатель роли — localStorage-макет,
   баннер честности ролей не снимать (RT-UI-OIDC-LIVE, RT-UI-ROLE-LS).
5. Баннер NO_GO и honesty-панели не прятать и не «улучшать» до зелёного
   (RT-UI-NOGO-MASK, RT-UI-HONEST-CAP).
6. Все видимые строки — через `RU_COPY` (`lib/i18n/ru.ts`); латиница только
   по правилам `scripts/ui-latin-scan.mjs` (капс-акронимы, идентификаторы,
   ALLOWED_WORDS).
7. Не грузить федерацию ~1 ГБ во вьюер; web-ifc остаётся lazy-чанком
   (RT-UI-PARSE-BROWSER, RT-UI-FRAG-FED).
8. CDN-шрифты запрещены (RT-UI-FONTS); новых рантайм-зависимостей — только
   с записью в этом плане и причиной.
9. Демо-фикстура — dev-only; не выносить seed в продакшн-копирайт
   (RT-UI-DEMO-PROD).
10. Клавиатура — первоклассная: J/K/A/R/E/? не ломать; новые списки —
    windowed при >40 строках (RT-UI-KEYBOARD).

## 4. Цикл работы исполнителя (на каждый WP)

```bash
cd frontend
npm test            # vitest, все зелёные
npm run lint        # lint-ui-strings, латиницы в видимых строках нет
npm run build       # tsc --noEmit ×2 + vite build
cd ..
python scripts/lint_claims.py                    # Claims Lock
python scripts/lint_claims.py --full-docs        # полный скан документов
```

Порядок: прочитать триаж-документ → один WP за коммит → гейты → коммит
(UTF-8: `$env:PYTHONIOENCODING='utf-8'` перед git-командами на Windows).
Новые документы с запрещёнными формулировками в контексте запрета — с
заголовком `claims-lint: allow-file` и записью в
`audit/claims_allow_file_registry.json`.

## 5. Пакеты работ

### WP-FE-07. Вьюер: свойства элемента и фильтр этажа (приоритет 1, демо ментору)

**Статус: done, 03.09.** Метод живёт на контроллере (`getElementProps(guid)` поверх уже открытой модели), не как свободная функция с повторным `OpenModel`. Fetch IFC по-прежнему ключ `report_id`.

Цель: при выборе находки с GUID эксперт видит read-only свойства IFC-элемента
(имя, тип, этаж) и может сузить сцену до этажа находки.

- Файлы: `components/IfcViewerPanel.tsx`, `lib/ifc-scene.ts`,
  `lib/i18n/ru.ts`, тест `components/IfcViewerPanel.test.tsx` (новый).
- Шаги: (1) в `ifc-scene.ts` добавить `getElementProps(modelID, expressID)`
  поверх уже загруженной модели — без повторной загрузки байт
  (RT-UI-VIEWER-ID: fetch ключ — `report_id`); (2) панель свойств под вьюером,
  строки через `RU_COPY`; (3) селектор этажа из `IfcBuildingStorey` модели;
  фильтрация через видимость поддерева, не через пересоздание сцены.
- Критерии: смена отчёта не перезагружает IFC того же `report_id`; панель
  свойств read-only; нет заявки на «произвольный осмотр модели» в копирайте.
- Тесты: мок `ifc-scene` — панель рендерит свойства; смена GUID обновляет
  панель без повторного fetch.
- Запреты: не тащить Fragments/федерацию; не обещать измерения как
  «замер для сметы».

### WP-FE-08. 2D-панель: зум/пан и клик по региону (приоритет 1)

**Статус: done, 03.09.** Зум — CSS `transform` контейнера. Клик — только HITL, не штамп/титул.

Цель: на превью листа эксперт зумирует зону находки и кликом по HITL-региону
выбирает связанную находку.

- Файлы: `components/DrawingEvidencePanel.tsx`, `styles.css`, тест
  `components/DrawingEvidencePanel.test.tsx` (расширить).
- Шаги: (1) зум/пан на CSS `transform` + pointer events, без зависимостей;
  (2) кнопка «сбросить масштаб»; (3) регионы (`DrawingRegionRef`) рендерить
  как кнопки с `aria-label`, клик → `onSelectIssue` активной находки региона;
  (4) `prefers-reduced-motion` отключает анимацию зума.
- Критерии: координаты наложения не искажаются при зуме (масштабируется
  контейнер, не пересчёт bbox); копирайт по-прежнему «детерминированный
  bbox, не CV».
- Тесты: клик по региону вызывает выбор находки; сброс возвращает scale=1.

### WP-FE-09. Список находок: скролл к выбранной строке (приоритет 1)

**Статус: done, 03.09.**

Цель: при J/K навигации в виртуальном списке (>40) выбранная карточка всегда
в видимой области.

- Файлы: `features/findings/FindingListPanel.tsx`.
- Шаги: при смене `selectedIssueIndex` с клавиатуры — корректировать
  `scrollTop` контейнера так, чтобы строка входила в окно (сейчас окно лишь
  расширяется до выбранной, без прокрутки); не скроллить при выборе мышью.
- Критерии: J/K на списке из 200 находок не теряет выбранную строку из
  видимости; `shownCount` остаётся `aria-live`.
- Тесты: jsdom — смена выбора за пределами окна меняет `scrollTop`.

### WP-FE-10. Прогон: журнал сессии и подтверждение отмены (приоритет 2)

**Статус: done, 03.09.**

Цель: эксперт видит прогоны текущей сессии (job_id, статус, итоговое время)
и не отменяет задание случайно.

- Файлы: `components/AnalyzeRunPanel.tsx`, `hooks/useRunPolling.ts`,
  `lib/i18n/ru.ts`, тест `components/AnalyzeRunPanel.test.tsx` (расширить).
- Шаги: (1) журнал в `sessionStorage` (не сервер, не «история компании»);
  (2) подтверждение отмены через `window.confirm` с честным текстом;
  (3) строки через `RU_COPY`.
- Критерии: журнал очищается с сессией; копирайт не называет журнал
  аудитом или журналом СОД.
- Запреты: не добавлять SSE; не показывать «ETA».

### WP-FE-16. Список находок: этаж/ось, снэп фильтра, копирование GUID (приоритет 1)

**Статус: done, 03.09.** Этаж/ось на карточке (или честное «нет в индексе»); фильтр не оставляет выбранную строку вне списка; GUID копируется с карточки замечания.

Цель: эксперт видит локацию, не открывая карточку; J/K и замечание остаются согласованы с видимым фильтром; GUID можно скопировать без выделения `<code>`.

- Файлы: `features/findings/FindingListPanel.tsx`, `features/findings/RemarkCardPanel.tsx`,
  `hooks/useSnapSelectionToFilter.ts`, `lib/issue-triage.ts` (`snapIssueIndexToVisible`),
  `lib/hitl-event-copy.ts`, `lib/i18n/ru.ts`, `App.tsx`.
- Шаги: (1) строка `эт.` / `ос.` на карточке, пустое значение = `spatialMissing`;
  (2) если выбранный индекс скрыт фильтром — `selectIssue` на первую видимую;
  пустой список не сдвигает выбор; (3) кнопка «Копировать GUID»; (4) типы HITL-событий
  в истории и KPI через одну функцию.
- Критерии: ось/этаж не выдумываются; `App.tsx` ≤ 300; окно виртуализации поднято
  до 148 px под дополнительную строку.
- Запреты: не заявлять «ось всегда есть»; не имитировать RBAC.

### WP-FE-11. Дашборд «Эффект»: CSS-диаграммы KPI (приоритет 2)

**Статус: done, 03.09.**

Цель: `ReviewKpiPanel` показывает распределение событий `by_type`
горизонтальными барами на чистом CSS.

- Файлы: `components/ReviewKpiPanel.tsx`, `styles.css`, тест рядом.
- Шаги: бары `div` с шириной в процентах; подпись, что журнал HITL — не
  точность продукта (копирайт уже есть, не размывать).
- Критерии: пустой журнал — пустой экран с честной подписью, не «0 %».
- Запреты: без chart-библиотек (новая зависимость = отдельное обоснование).

### WP-FE-12. Доступность: фокус и axe-проход (приоритет 2)

**Статус: done, 03.09.** `axe-core` только в тестах. Не WCAG-сертификат.

Цель: клавиатурный фокус следует за выбором находки; базовые axe-нарушения
закрыты в тестах.

- Файлы: `features/findings/FindingListPanel.tsx`,
  `features/workplace/ExpertWorkplace.tsx`, `package.json` (devDependency
  `axe-core` — только для тестов, не рантайм-стек), тесты рядом.
- Шаги: (1) выбранная карточка получает `tabIndex={0}` и фокус при J/K;
  (2) roving tabindex в списке; (3) `axe` на ключевых экранах в vitest
  (jsdom-совместимое подмножество правил).
- Критерии: axe без critical/serious на экранах «Эксперт» и «Замечание»;
  фокус видим (outline не снят).
- Запреты: не заявлять «WCAG-сертификацию» — это внутренний проход.

### WP-FE-13. Сквозной тест маршрута комиссии (приоритет 2)

**Статус: done, 03.09.** Успешный job открывает эксперта через `onReportReady` (не отдельный клик «К эксперту»).

Цель: один App-тест повторяет маршрут демо: загрузка → прогон → эксперт →
замечание → экспорт (все вызовы api замоканы).

- Файлы: `src/App.test.tsx` (расширить).
- Критерии: маршрут проходит без реального бэкенда; каждая панель появляется
  в ожидаемом порядке; `npm run smoke:browser` остаётся зелёным при живом
  бэкенде.

### WP-FE-14. Хвосты i18n и provenance

**Статус: done, 03.09.** Provenance/KPI/демо/карта покрытия/прогон/навигация — через `RU_COPY`. Английские отказы карты покрытия убраны.

Цель: добить оставшиеся динамические строки provenance/KPI в `RU_COPY`;
проверить, что `lint-ui-strings` покрывает новые панели.

- Файлы: `components/ProvenancePanel.tsx`, `components/ReviewKpiPanel.tsx`,
  `components/CoverageMapPanel.tsx`, `components/DemoFixturePanel.tsx`,
  `components/TzWorkplaceCoveragePanel.tsx`, `components/AnalyzeRunPanel.tsx`,
  `features/honesty/BlockerHonestyPanel.tsx`, `lib/i18n/ru.ts`.

### WP-FE-17. Рабочий цикл оболочки: повтор API и пустые экраны

**Статус: done, 03.09.** Отказ списка/отчёта — баннер с «Повторить» (тот же epoch перезапрашивает GET списка и GET отчёта). Пустой эксперт — кнопки «Открыть проекты» / «К загрузке». Не маскирует BFF 501.

- Файлы: `features/shell/ErrorBanner.tsx`, `hooks/useSelectedReport.ts`,
  `App.tsx`, `features/workplace/ExpertWorkplace.tsx`.
- Запреты: не имитировать OIDC; не снимать баннер ролей.

### WP-FE-15. HOLD до живого OIDC (не маскировать 501)

Негативные HTTP RBAC-тесты (viewer → 403 на POST review-events) — только
когда BFF перестанет отвечать 501. До этого — ничего не имитировать.
Серверные пресеты фильтров — после фриза, отдельным решением.

## 6. Очередность

| Когда | Пакеты | Статус 03.09 вечер |
|---|---|---|
| Сделано 03.09 утро | FE-01…FE-06 | done |
| До демо ИТ-ментору | WP-FE-07, WP-FE-08, WP-FE-09, WP-FE-16 | done |
| До 15.09 | WP-FE-10, WP-FE-11, WP-FE-12, WP-FE-13, WP-FE-14, WP-FE-17 | done |
| Пока BFF = 501 | WP-FE-15 | HOLD |

Гейты после WP-FE-14/17: `npm test` — 37 файлов / 142 теста; `npm run lint` — чисто;
`npm run build` — чисто. `App.tsx` = 300 строк. Новая рантайм-зависимость не добавлялась.
Живая оболочка 03.09 вечер: `127.0.0.1:5173` против API `127.0.0.1:8080`; учебный отчёт
открывается, баннер `GET /v1/auth/bff = 501` остаётся. WP-FE-15 не имитировать.
`axe-core` — только `devDependencies`, jsdom, правило color-contrast выключено.
Это внутренний проход, не сертификат WCAG.

### Red Team: KILL / ACCEPT / HOLD этого прохода

| ID | Решение | Почему |
|---|---|---|
| WP-FE-07 | ACCEPT | Свойства = `GetLine` имя/тип/GUID; этаж = `IfcRelContainedInSpatialStructure`, не дерево агрегации и не QTO |
| WP-FE-08 | ACCEPT | Кликабельны только HITL-регионы; связь с находкой по `sheet_id` (`DrawingRegionRef` не несёт `finding_id`) |
| WP-FE-09 | ACCEPT | Скролл только при смене выбора не с мыши; математика в `computeScrollTopToReveal` |
| WP-FE-10 | ACCEPT | Журнал в хранилище вкладки; `confirm` перед отменой; нет SSE и нет ETA |
| WP-FE-11 | ACCEPT | Пустой журнал HITL → честная пустая подпись, не «0 % ошибок» |
| WP-FE-12 | ACCEPT | Roving `tabIndex`; axe без critical/serious; не заявлять WCAG |
| WP-FE-13 | ACCEPT | Маршрут на замоканном API; успешный job сам открывает эксперта через `onReportReady` |
| WP-FE-16 | ACCEPT | Этаж/ось с карточки; пустое = «нет в индексе»; снэп фильтра; GUID copy; HITL-типы через `hitlEventTypeLabel` |
| WP-FE-14 | ACCEPT | Хвосты копирайта в `RU_COPY`; английский отказ coverage убран |
| WP-FE-17 | ACCEPT | Повтор GET; пустой эксперт с переходами; epoch перезапрашивает отчёт |
| WP-FE-15 | HOLD | BFF остаётся 501; негативный RBAC не имитировать |
| Fragments / федерация | KILL | Не грузить ~1 ГБ во вкладку |
| XLSX / OIDC live / SLA | KILL | Без изменений рамок триажа |

## 7. Definition of Done (каждый WP)

1. Гейты раздела 4 зелёные; новые тесты на новое поведение.
2. Видимые строки — только `RU_COPY`; линт латиницы чист.
3. Ни один запрет раздела 3 не нарушен; копирайт не обещает больше git.
4. `App.tsx` ≤ 300 строк; новая логика — в `lib/` (чистые функции) или
   `hooks/`.
5. Запись в этом плане: статус WP → done, дата, коммит.

Checkpoint **`NO_GO`**. Этот план не закрывает RT-001 / RT-002b / RT-003 и не
меняет позиционирование: шов комплекта, файловый выход BCF/HTML/JSON, импорт
в СОД заказчика — NOT_VERIFIED.
