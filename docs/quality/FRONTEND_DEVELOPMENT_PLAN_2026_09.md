<!-- claims-lint: allow-file reason="Frontend plan for the AI executor; forbidden claims quoted only as prohibitions; review shell; NO_GO" -->
---
title: "План развития фронтенда (для ИИ-исполнителя) — 2026-09-03"
date: "2026-09-03"
last_updated: "2026-09-04"
status: active
version: "1.4.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: coverage_map_only
detected_count: 0
claim_boundary: >
  Фронтенд — review shell над сохранёнными отчётами, не полный цикл CDE и не
  коннектор 10D/Tangl. UI не пишет summary.passed (ADR-001). Нативные
  RVT/NWD/DWG — fail-closed. SSE нет, только опрос jobs. Checkpoint GO; customer_go false.
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
Каркас: `App.tsx` (порог 300 — RT-UI-SPLIT), фичи в
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
4. OIDC заказчика не имитировать. По умолчанию `GET /v1/auth/bff` = 501.
   Lab `200 LAB` — не SSO: непроверенная cookie не авторизует. Баннер читает
   discovery, не хардкодит 501 (RT-UI-OIDC-LIVE, RT-UI-ROLE-LS).
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

### WP-FE-15. HOLD: живой OIDC заказчика (не маскировать 501 по умолчанию)

**Статус: HOLD, 04.09.** Не закрывает RT-001 / RT-002 / RT-003. Не промышленный SSO.

Лаборатория (только `oidc_bff_phase3_ready`, не `samolet_pilot` / `production`):
`GET /v1/auth/bff` = 200 `LAB`; проверенная cookie может стать `AuthPrincipal`;
viewer/user → 403 на expert HITL. Это HTTP RBAC лаборатории, не SSO заказчика.

По умолчанию и на жёстких профилях: `GET /v1/auth/bff` = 501 `NOT_IMPLEMENTED`.
Баннер оболочки читает discovery, не хардкодит 501. localStorage — макет экрана.

- Файлы: `oidc_bff_phase3.py`, `context.py`, `hooks/useAuthBff.ts`,
  `features/honesty/RoleHonestyBanner.tsx`.
- Запреты: не писать «OIDC live»; не считать 200 LAB закрытием WP как SSO.

### WP-FE-18. Приём 1,5 ГБ ≠ разбор SPF 256 МиБ (P0, К1)

**Статус: done, 04.09.** Не поднимает SPF. Не добавляет протокол докачки.
Не закрывает RT-001/002b/003. Не измеренный RSS на файле заказчика.

Экран загрузки и экран прогона прямо разделяют четыре числа из
[`IFC_ANALYZE_VS_INGEST_CAP_2026_08.md`](IFC_ANALYZE_VS_INGEST_CAP_2026_08.md):
SPF 256 МиБ, bSI 256 MB, WASM 256 МиБ, диск 1,5 ГБ на жёстком профиле.
Одна отправка с прогрессом и отменой уже была; докачка с места обрыва —
честный HOLD, не фальшивый tus.

- Файлы: `lib/i18n/ru.ts`, `lib/pack-kind.ts`, `PackUploadPanel.tsx`,
  `AnalyzeRunPanel.tsx`.
- Запреты: не поднимать `AEROBIM_MAX_IFC_BYTES`; не писать «принимаем 1,5 ГБ
  в браузере»; не смешивать приём и SPF-`open()`.

### WP-FE-19. HITL подтверждено/отклонено ≠ дни цикла (P1, К3)

**Статус: done, 04.09.** Экран «Эффект» показывает split из `review-kpi`
и прямо пишет, что это не «минус один круг» в СОД.

- Файлы: `lib/kpi-bars.ts`, `ReviewKpiPanel.tsx`, `lib/i18n/ru.ts`.
- Запреты: не выводить дни цикла без журнала ревизий заказчика.

### WP-FE-20. Пункт ИТЗ / СТО / СП — поле первого класса (P0, К1)

**Статус: done, 04.09.** Не новый порт. Поля `norm_source` / `norm_clause` уже
были в отчёте. Закрывает вопрос «привязка к пункту ИТЗ» на колле 15.09.

Карточка: подпись «Пункт ИТЗ / СТО / СП». Список: фильтр + группировка +
строка на карточке. Поиск включает штамп. HTML-колонка и BCF `norm=`.
Пустой штамп = «нет пункта», не OCR.

- Файлы: `lib/issue-triage.ts`, `FindingListPanel.tsx`, `RemarkCardPanel` copy,
  `hooks/useFindingFilters.ts`, `hooks/useTriageView.ts`, `report_html.py`,
  `bcf_report_exporter.py`.
- Запреты: не выдумывать пункт; PDF-кнопка остаётся (эндпоинт есть).

Серверные пресеты фильтров — после фриза, отдельным решением.

### WP-FE-21. Баннер возможностей и цикл «покрытие ТЗ» человеческим языком (P0, К1)

**Статус: done, 04.09.** Не закрывает RT-001/002/003. Не native DWG. Не MEP-solver.
Матрица ТЗ Web UI остаётся `partial`.

Баннер и таблица возможностей больше не показывают enum `skipped`/`failed`/`ok`.
`failed`/`missing` → «не выполнена → вердикт отрицательный». Пропуск и
`not_verified` → «не выполнена → тишина ≠ успех». Для `mep_system_clash` —
«сети в IFC не переданы». В цикле комплекта шаг «Покрытие ТЗ» открывает экран
«Эффект» (карта пункт→функция→git). PDF-кнопка не снималась.

- Файлы: `lib/capability-copy.ts`, `CapabilityHonestyPanel.tsx`,
  `AnalyzeRunPanel.tsx`, `PackCycleStrip.tsx`, `CapabilityTopBanner` tests.
- Запреты: не писать «вердикт отрицательный» на каждый пропуск в профиле
  development как измеренный SLA; не помечать строку ТЗ Web UI как done.

### WP-FE-22. Один клик: учебный комплект → эксперт с BCF (P1-9, B3)

**Статус: done, 04.09.** Не новый движок. Не SSO. Не точность продукта.
Не снимает PDF. Не распиливает `App.tsx`.

После кнопки учебного комплекта или успешного прогона оболочка остаётся на
экране эксперта: список, карточка (пункт ИТЗ, этаж/ось или «нет в индексе»),
лист и 3D, BCF на той же полосе. Вкладка «Экспорт» не обязательна. Плашка
демо сжимается, когда отчёт уже на экране. Выбор свежепосеянного id не
сбрасывается, если список отчётов отстал на один GET.

- Файлы: `DemoFixturePanel.tsx`, `ExpertWorkplace.tsx`, `App.tsx`,
  `useReports.ts`, `lib/rehearsal-land.ts`.
- Запреты: не писать второй auth-стек; не убирать PDF из `ExportFormat`;
  не обещать SLA 30:00.

## 6. Очередность

| Когда | Пакеты | Статус 03.09 вечер |
|---|---|---|
| Сделано 03.09 утро | FE-01…FE-06 | done |
| До демо ИТ-ментору | WP-FE-07, WP-FE-08, WP-FE-09, WP-FE-16 | done |
| До 15.09 | WP-FE-10, WP-FE-11, WP-FE-12, WP-FE-13, WP-FE-14, WP-FE-17 | done |
| До 11.09 | WP-FE-18, WP-FE-19, WP-FE-20 | done 04.09 |
| 04.09 вечер | WP-FE-21 | done 04.09 |
| 04.09 | WP-FE-22 | done 04.09 |
| Пока нет IdP заказчика | WP-FE-15 | HOLD |

Гейты: `npm test` — 41 файл / 170 тестов; `npm run lint` — чисто; `npm run build` — чисто.
`App.tsx` ≤ 300 строк. Новая рантайм-зависимость не добавлялась. По умолчанию баннер
читает `GET /v1/auth/bff` (501); 200 LAB не SSO заказчика. WP-FE-15 остаётся HOLD.
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
| WP-FE-15 | HOLD | По умолчанию BFF = 501; 200 LAB ≠ SSO заказчика; viewer 403 только в лаборатории |
| WP-FE-18 | ACCEPT | Копирайт приём≠SPF; докачка HOLD; SPF не поднят |
| WP-FE-19 | ACCEPT | Split HITL; не дни цикла СОД |
| WP-FE-20 | ACCEPT | Штамп ИТЗ/СТО/СП в карточке, фильтре, HTML/BCF; пустое ≠ OCR |
| WP-FE-21 | ACCEPT | RU-статусы возможностей; шаг покрытия ТЗ; enum не в баннере |
| WP-FE-22 | ACCEPT | Склейка репетиции: демо/прогон → эксперт с BCF; PDF на месте |
| Fragments / федерация | KILL | Не грузить ~1 ГБ во вкладку |
| XLSX / OIDC live / SLA | KILL | Без изменений рамок триажа |

## 7. Definition of Done (каждый WP)

1. Гейты раздела 4 зелёные; новые тесты на новое поведение.
2. Видимые строки — только `RU_COPY`; линт латиницы чист.
3. Ни один запрет раздела 3 не нарушен; копирайт не обещает больше git.
4. `App.tsx` ≤ 300 строк; новая логика — в `lib/` (чистые функции) или
   `hooks/`.
5. Запись в этом плане: статус WP → done, дата, коммит.

Checkpoint **`GO`**; `customer_go` false. Этот план не закрывает RT-001 / RT-002b / RT-003 и не
меняет позиционирование: шов комплекта, файловый выход BCF/HTML/JSON, импорт
в СОД заказчика — NOT_VERIFIED.
