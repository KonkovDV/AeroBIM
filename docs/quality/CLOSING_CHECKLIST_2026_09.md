<!-- claims-lint: allow-file reason="Closing checklist Red Team triage; TZ 90%/SLA as non-claims; NO_GO" -->
---
title: "Closing Checklist — все выявленные гэпы, проблемы и что закрыть (сентябрь, КТ#3)"
status: active
version: "1.1.0"
last_updated: "2026-09-04"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: "Рабочий чек-лист + Red Team KILL/HOLD/ACCEPT. Checkpoint GO; customer_go false; RT-001/002/003 OPEN. Источники: серия RED_TEAM_* (25 отчётов), DOCUMENTS_CROSS_AUDIT_2026_09, трекер/gap/UI/SOTA документы."
---

# Closing Checklist — детальный список на закрытие

## 0. Red Team triage (02.09.2026) — KILL / HOLD / ACCEPT

Не выполнять чеклист как backlog «закрыть всё кодом». Validity = licensed inference (Messick/Kane). Cookie/localStorage ≠ RBAC. Таймер ≠ SLA. Ближайшая ось ≠ AxisTag.

| ID | Verdict | Почему |
|---|---|---|
| **A1** | **HOLD** production SSO; **ACCEPT** honesty | HITL 403 на shared Bearer и viewer/user под pilot. По умолчанию `GET /v1/auth/bff` = 501. Lab `200 LAB` — не SSO заказчика: непроверенная cookie не авторизует (HD3-BFF-01); проверенная может bind `AuthPrincipal`, viewer → 403. Поддельная lab-cookie как промышленный RBAC — **KILL**. `hitl_write.ui_role_is_acl=false`. Речь: FAQ «вопрос №1». UI 04.09: загрузка/прогон разделяют приём 1,5 ГБ и SPF/вьюер 256 МиБ; докачка не реализована. |
| **A2** | **KILL** nearest intersection; **ACCEPT** AxisTag+storey | Резолвер **уже** в `ifc_spatial_index.py` (этаж + `IfcGridAxis.AxisTag`). «Ближайшая ось» — атака live_tree_triage. Дом 5 без осей = данные (B7), не код. Гвоздь: два грида → `grid_axis is None`. |
| **A3** | **ACCEPT** | Пресет: pilot/production → пустой LLM/VLM allowlist; `allow` только с `CONSENT_REF`. Не включает egress сам по себе (`llm_local_ready` всё ещё false). |
| **A4** | **ACCEPT already** | Таймер в `AnalyzeRunPanel` с копирайтом «не SLA». Не доказательство ТЗ 30 мин. |
| **A5** | **HOLD** | 1–2 недели; sidecar ≠ R-tree (тест уже). Без RSS на ~1,5 ГБ не заявлять. SPF 256 МиБ не поднимать. |
| **A6** | **ACCEPT** | PDF-кнопка есть. Smoke смотрел `<a href>` — STALE. Теперь кнопки html/json/bcf/pdf + disabled XLSX. |
| **A7** | **ACCEPT** | LF перед коммитом. |
| **A8** | **ACCEPT** | Коммит волны; RED_TEAM_* unpublished не в git. |
| **A9** | **ACCEPT** | `ui-copy.ts`; баннер capabilities на RU. Остаток EN в глубоком chrome — не блокер демо. |
| **A10** | **ACCEPT already** | `team` → `file`; тест миграции есть. |
| **A11** | **ACCEPT** | `App.tsx` = 300 строк (порог плана). Не закрывает WP-FE-15 / SSO. |
| **B1** | **ACCEPT** | Баннер «учебный набор правил» на экране находок. |
| **B2** | **HOLD** owner | Слайд пустых данных пакета — не git (агрегат канала). |
| **B3** | **ACCEPT** glue 04.09; not a new engine | Куски были. Склейка: демо/прогон сажает на эксперт с BCF на полосе; вкладка «Экспорт» не нужна. Не SLA. |
| **B4** | **ACCEPT already** | `TzWorkplaceCoveragePanel` + `ReviewKpiPanel` в App. Не тай-брейк балла. |
| **B5** | **ACCEPT** | Карточка речи: вопрос №1. |
| **C1–C6** | **HOLD** owner | Git не закрывает юрлицо, NDA, письма, брендбук. |
| **D1** | **HOLD** | CLI tool-only есть; `t_manual_s` null без человека. |
| **D2** | **HOLD** | n≥30 после корпуса. |
| **D3** | **HOLD** owner | Второй контрибьютор. |
| **D4** | **HOLD** | Related-work в git; e-process = CLI, не job Actions. Не мини-статья «сдана». |
| **D5** | **ACCEPT already** | Промт в `docs/ai/ACADEMIC_LIT_RADAR.md`. |
| **D6** | **HOLD** owner | Предрегистрация МГСУ — письмо. |

**E поправка:** реестр HD не «пуст». HD19 в `KNOWN_BUGS.md`; HD20-CI-01 запинен комментарием+тестом; HD20-CI-02 — documented residual (pip/uv bootstrap). Не говорить «секреты не найдены ⇒ безопасно».


## A. КОД (по убыванию риска для КТ#3)

| # | Гэп | Где | Оценка | Источник |
|---|---|---|---|---|
| A1 | **Серверный минимум RBAC**: lab HTTP 403 для viewer **есть** (04.09). Production SSO / BFF по умолчанию 501 — HOLD. localStorage остаётся макетом экрана | `ui-role.ts` / `system.py` / `oidc_bff_phase3.py` | HOLD SSO | WP-FE-15 |
| A2 | **IfcGrid-резолвер** «GUID → этаж + ближайшая ось» (заказчик просил локацию в замечании; в доме 5 осей нет — резолвер нужен и для демо, и для запроса B7) | новый domain-модуль + adapter по IfcGrid/IfcBuildingStorey | 1–2 дня | Трекер задача 4; GAP §3 |
| A3 | **Пресет «LLM egress deny для пакета заказчика»**: пустой allowlist как профиль конфига, включение только письменным согласием (механизм HybridRouteGate есть) | settings + `hybrid_route_gate` wiring | часы | Трекер §3.1; CROSS §2 |
| A4 | **Таймер прогона на экране** (stage_progress уже в данных): бесплатное доказательство критерия ТЗ «30 минут» | `AnalyzeRunPanel.tsx` | часы | UI 2.txt #6 |
| A5 | **Streaming IFC-read + дисковый R-tree + bbox-предфильтр** (без RSS на ~1,5 ГБ не заявлять). UI 04.09 уже пишет: приём ≠ SPF 256 МиБ. SPF не поднимать | `ifc_file_open` / UI copy | HOLD RSS | Трекер задача 1; WP-FE-18 |
| A6 | Расширить e2e-прогон экспортов (pdf/html/json/bcf) — кнопка PDF работает, но смоук-путь не закреплён | `frontend/scripts` + Playwright | часы | CROSS §1 (STALE-фикс) |
| A7 | **CRLF-нормализация 5 файлов до коммита** (`vlm_grounding.py`, `bcf3_exporter.py`, `TARGET_HYBRID…`, `docs.md`, `pre_push_gate.py`) | git | 10 минут | session (git warnings) |
| A8 | **Заккоммитить волну** (52 файла: фиксы серии + Expert Workplace) — разбить на fix/feat/docs | git | 1 час | session |
| A9 | Русификация строк UI (шапка/кнопки/ошибки ещё в EN) — один файл строк | `ui-copy.ts` + компоненты | полдня | UI 2.txt #2 |
| A10 | Переименовать team-пресеты («team» никуда не уходит — класс формулировки из claims lock) | `report-filters.ts` | минуты | UI 2.txt #4 |
| A11 | Продолжить разбор App.tsx (шапка/фильтры/шорткаты в хуки; цель <300 строк) — начато | `App.tsx` | 1–2 дня | UI 2.txt #5 |

## B. ДЕМО / ФРЕЙМИНГ КТ#3

| # | Пункт | Действие |
|---|---|---|
| B1 | Дисклеймер «учебный набор правил» на каждом экране с находками (до подписи IDS C2) | слайд + баннер; язык claims-машины |
| B2 | Слайд «пустые данные пакета» — площади 0/16000, арматура 0, инженерия 0, оси нет → запрос B1–B7 с датами превращает провал в дисциплину | слайд |
| B3 | Сквозной маршрут демо одним кликом: комплект → прогон с таймером → список по критичности → карточка Суть/Норма/Ось-Этаж → доказательство на листе и 3D → BCF | **склейка 04.09**: эксперт + BCF на одном экране; не новый движок |
| B4 | Экраны «Покрытие ТЗ» и «Дашборд эффекта» — тай-брейк K3/K4 жюри (среднее 5 оценок, порог 50, тай-брейк — соответствие задачам партнёра) | TzWorkplaceCoveragePanel + review-kpi |
| B5 | Ответ на вопрос №1 комиссии про разграничение доступа — заготовлен: «UI-мок, сервер решает (ADR-001 + OIDC-гейт HITL)» | репетиция |

## C. ОПЕРАЦИОННОЕ / ЮРИДИЧЕСКОЕ (не код, но блокирует)

| # | Пункт | Дедлайн/статус |
|---|---|---|
| C1 | Письменный режим обращения с пакетом (где хранить, кто доступ, срок, удаление) — запрос A1 отправлен | ответ до 03.09 |
| C2 | **Юрлицо** — без него ни NDA, ни пилот МИК, ни грант фонда; решение о форме — на встречу с трекером | горит |
| C3 | ПДн в сканах: обезличивание на входе или изолированный контур с журналом доступа; не личные машины | до загрузки пакетов |
| C4 | Ответы B1–B7/D1–D2 (записки ЛИРА, IFC с площадями/осями/инженерией, подпись IDS, 2 разметчика) — без ответа к 08.09 пункты уходят из окна КТ#3 | 08.09 |
| C5 | Письма: МГСУ (приоритет 1), ВШЭ, МФТИ/Сколтех + запрос в ЛИРА-САПР (формат выгрузок — снимает хрупкий PDF-узел) | до 31.08 / срочно |
| C6 | Брендбук от заказчика (палитра/шрифты) — задача 8 трекера | запрос отправить сразу |

## D. НАУКА / ПРОЦЕСС (КТ#3 → финал)

| # | Пункт |
|---|---|
| D1 | Лабораторный замер «до/после»: **tool-side измерен, `t_manual_s=null`** — осталось провести ручной проход «до» по протоколу (чередование порядка) |
| D2 | Adjudication n≥30 с Wilson CI — после ответов D1–D2; иначе «валидация эффективности» не стартует |
| D3 | Второй контрибьютор — bus-factor=1, главный non-технический риск |
| D4 | Preprint: related-work готов (ACADEMIC_LIT_REVIEW, 9 позиций), e-values CI-гейта — отдельная мини-статья |
| D5 | Опционально: перенос промта литрадара из ACADEMIC_LIT_REVIEW в docs/ai/ |
| D6 | МГСУ-маршрут: протокол публикуется ДО прогона (предрегистрация) — уже сформулировано в письме-шаблоне |

## E. Что закрыто (не делать повторно)

- PDF-кнопка — **работает** (критика STALE); только e2e (A6).
- Кодовый реестр серии HD/HD2…HD20 — **пуст**: GlobalId exact + тест, source-scan гард, advisory_origin объединён, presign в KNOWN_BUGS, CI-комментарий, RL docstring, unrecognized-unit флаг.
- Claims-lint 4 режима — зелёные; excluded_untracked=0; фактчек цитат 20/20 DOI + 27/27 arXiv.
- Секреты/критические — не найдены за 25 отчётов.
