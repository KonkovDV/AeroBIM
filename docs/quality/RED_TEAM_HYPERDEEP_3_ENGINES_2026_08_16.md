---
title: "Red Team Hyper-Deep Round 3 — engines, stores, auth-flow, exports"
status: active
version: "1.0.0"
last_updated: "2026-08-16"
claim_boundary: "Audit report plus later remediations. Checkpoint stays NO_GO. Round 3 of HD-trilogy: IDs HD3-*. See round 1 (RED_TEAM_HYPERDEEP_TRIAGE_2026_08_16.md) and round 2 (RED_TEAM_HYPERDEEP_2_SEAMS_2026_08_16.md)."
audited_head: "2768058 (committed) + uncommitted working tree 2026-08-16"
auditor: "ZCode autonomous triage, round 3 (solo)"
---

# Red Team Hyper-Deep Round 3 — движки, сторы, auth-flow, экспорты

Третий проход закрыл residual-зоны раундов 1–2: адаптеры движков (IDS/IfcClash/IFC-open), сторы, settings-гейты, OIDC BFF целиком, экспорты, норм-паки, PDF, выборочная проверка мутационных тестов. Последующий remediation-проход закрыл MEDIUM/LOW из §1; Checkpoint **NO_GO**.

**Сквозной вывод раунда 3:** культура fail-closed реализована на *бизнес*-уровне безупречно (SKIPPED→ERROR, all-skipped→FAILED), но имеет **микро-швы на уровне парсеров**: «отсутствие данных → успех». Дефолт `get("status", True)` у IDS и молчаливый `continue` у clash-маппера — один и тот же паттерн: если движок перестанет присылать поле, система прочтёт тишину как «всё хорошо». Второй слепой класс — **ресурсный жизненный цикл** (кэш IFC-моделей без эвикции). Оба класса не видны на фикстурах и проявятся только на реальных объёмах/версионном дрейфе зависимостей.

---

## 1. Реестр находок (машино-читаемо)

| ID | Sev | Зона | Файл:строка | Суть | Статус |
|---|---|---|---|---|---|
| HD3-IDS-01 | MEDIUM | ids | `ifc_tester_ids_validator.py` | `spec.get("status", True)` — отсутствующий ключ `status` дефолтит в «прошла» | FIXED |
| HD3-CLASH-01 | MEDIUM | clash | `ifc_clash_detector.py` | Малформированные записи движка молча `continue` | FIXED |
| HD3-IFC-01 | MEDIUM | ifc | `ifc_file_open.py` | Процессный кэш IFC-моделей без эвикции/лимита | FIXED |
| HD3-BFF-01 | MEDIUM | auth | `oidc_bff_phase3.py` / `context.py` | Lab JWT без подписи; cookie не AuthPrincipal; `require_verified_bff_session` | FIXED |
| HD3-BFF-02 | LOW | auth | `oidc_bff_phase3.py` | `session_id.encode("ascii")` вне try | FIXED |
| HD3-IDS-02 | LOW | ids | `ifc_tester_ids_validator.py` | Двойное независимое декодирование IDS | FIXED |
| HD3-IFC-02 | LOW | ifc | `ifc_file_open.py` | Marker-JSON с абсолютными путями | FIXED |
| HD3-EXP-01 | LOW | exports | `routes/exports.py` | Неизвестный `version` молча → BCF 2.1 | FIXED |
| HD3-BFF-03 | INFO | auth | in-memory session store | Рестарт/мульти-реплика | OK-CONFIRM |
| HD3-PDF-01 | INFO | pdf | `report_pdf.py` | simple_pdf OK | OK-CONFIRM |

**OK-подтверждения:** clash-детектор честный по духу (all-skipped → `ClashCapabilityError("failed")`, `ifc_clash_detector.py:286-291`; AssertionError не «тихий пас», :272-276); норм-пак loader fail-closed по approval-цепочке (`json_norm_rule_pack_loader.py:120-126`: advisory-пак не может штамповать `customer_approved`, требуется `approval_ref`); filesystem audit store — атомарные записи tmp+`os.replace`, commit-маркеры, orphan-реестр, integrity-verify при `get` и при `peek_tenant_id`; `allow_anonymous_dev` по умолчанию False; LOCAL-alias с warning и датой удаления 2026-09-21; model_router вердикт-нейтрален по конструкции (решение о маршруте — выше, в trust_policy); мутационный тест-файл `test_mutation_kills_http_context.py` — 62 реальных теста.

---

## 2. Движки: микро-швы «тишина = успех»

### HD3-IDS-01 (MEDIUM): дефолт-True обходит fail-closed guard

Проект гордится тем, что SKIPPED-спецификации IfcTester превращаются в ERROR (`ids_schema_gate.py:233-252`: `status is None → RULE_SKIPPED`). Но в адаптере статус читается как `spec.get("status", True)` (`ifc_tester_ids_validator.py:112`) и `requirement.get("status", True)` (:190). Отсутствие ключа — это не `None`, а `True`: guard не срабатывает, spec молча считается прошедшим. Если будущая версия ifctester переименует/перестанет эмитить `status` (schema drift), весь IDS-контур тихо позеленеет. Это ровно тот класс ошибки, от которого система заявлена защищённой. Направление: `spec.get("status")` без дефолта (None попадёт в guard), требование-уровень — аналогично.

### HD3-IDS-02 (LOW): двойное чтение IDS-файла

Наш независимый парсер версий читает текст с `errors="replace"` (:41), IfcTester открывает файл сам (:49). Кривая UTF-8 → разные имена спек у двух читателей → дедуп-фильтр (:59-67) молча не матчится → задвоенные/противоречивые issues без сигнала. Направление: один источник текста (прочитать байты → декодировать один раз → передать обоим).

### HD3-CLASH-01 (MEDIUM): маппер глотает малформированный вывод

`clash_results_from_sets` (`ifc_clash_detector.py:193-216`): `clashes` не Mapping → `continue`; элемент не Mapping → `continue`. Дрейф формата IfcClash → пустой результат → «коллизий нет» → в жёстких профилях `hard_clash_blocks=False`. Сам движок защищён (`_guarded` превращает исключения в `failed`), но тихая деградация *формата* проходит насквозь. Направление: считать отброшенные записи, ≠0 → лог + `ClashCapabilityError("failed")`.

## 3. Ресурсный жизненный цикл

### HD3-IFC-01 (MEDIUM): вечный кэш IFC-моделей

`ifc_file_open.py`: `_memory` (:22) растёт без ограничений — ключ `(path, mtime, size)`, значение — живая ifcopenshell-модель (десятки–сотни МБ на реальных федерированных моделях). Никакой эвикции, никакого max-size, удаления только в тестах (:51-60). Прод-сценарий «мульти-тенант грузит модели весь день» → OOM-перезапуск циклом. Фикстуры этого никогда не увидят (штучные файлы). Направление: LRU по суммарному размеру/количеству + метрика evictions в `ifc_parse_cache_stats`. Сопутствие (HD3-IFC-02, LOW): marker-файлы содержат абсолютные пути (`:127-133`) — при выгрузке cache-dir как артефакта утекает структура ФС.

## 4. Auth-flow BFF Phase 3

Порядок в целом правильный: PKCE+state, код обменивается сервер-сервер через SSRF-guarded `safe_urlopen`, nonce обязателен, HMAC-кука с `compare_digest`, `__Host-` при Secure. Найдено:

- **HD3-BFF-01 (MEDIUM, требует верификации):** lab-ветка без валидатора берёт `sub`/`email` из **непроверенного** декода JWT (`:230-236`), честно помечая `identity_verified=False`. Вопрос не в коде, а в **границе потребления**: если любая ветка (ACL-биндинг тенанта, HITL expert-события, сессии) трактует phase-3 сессию как OIDC-принципала без проверки `identity_verified` — это авторизация по неподписанному токену. Проверить все места чтения сессии; direction: жёсткий assert `identity_verified` на входе в любые authz-решения + тест «lab-сессия не проходит require_oidc».
- **HD3-BFF-02 (LOW):** `parse_session_cookie` — `session_id.encode("ascii")` стоит до try (:129-133): кука с не-ASCII session_id даёт необработанный UnicodeEncodeError → 500 на каждом запросе с такой кукой. Обернуть или `errors="replace"`-реджект.
- **HD3-BFF-03 (INFO):** session store in-memory — рестарт/мульти-реплика; согласовано с честным `auth_bff=NOT_IMPLEMENTED`, но при активации phase 3 в проде нужен Redis-store (тот же класс, что HD2 durable-runtime).

## 5. Сторы, settings, экспорты, норм-паки

- **Filesystem audit store** (grep-структура + diff): атомарность, commit-маркеры, orphan-реестр, integrity-verify и в `get`, и в новом `peek_tenant_id` — добротно. `_acquire_exclusive_lock` (:118) — тот же O_EXCL-паттерн, что HD2-UQ-01: обобщить stale-lock-риск на все файловые локи хранилища (квота + стор + review store).
- **Settings:** `allow_anonymous_dev=False` по умолчанию; LOCAL→ADVISORY alias с once-per-process warning и датой удаления; `require_durable_runtime`/`require_secure_auth` вызываются из единой точки загрузки. Шов HD2-DI-02 (конфиг=снапшот на boot) остаётся недокументированным явно.
- **Экспорты (HD3-EXP-01, LOW):** все маршруты через `load_authorized_report` (ACL ✓), BCF-API push с UUID-валидацией project_id и 404-маскировкой (✓). Но `version` в BCF-экспорте не валидируется: `version=99` молча возвращает 2.1. Для API с версионной семантикой — вернуть 400 на неизвестную.
- **Норм-пак loader:** approval-цепочка fail-closed подтверждена (advisory/synthetic не может стать `customer_approved`; `approval_ref` обязателен) — RT-002-гейт на стороне кода держит.
- **PDF:** самописный writer без зависимостей, усечение 120 симв., временный каталог очищается. Residual: `core/simple_pdf.py` (86 строк) прочитан не построчно — экранирование PDF-строк не проверялось (у PDF-текста свои escape-правила; риск — сломанный, не опасный вывод).

## 6. Проверка мутационных тестов (выборочная)

`test_mutation_kills_http_context.py` — 62 теста с реальными мутациями контекста (assert'ы на 404-маскировку, ACL, tenant-spoof). Не «тесты ради тестов». Класс живой и обновлён текущей волной.

## 7. Сводный профиль трёх раундов

| Измерение | Оценка | Комментарий |
|---|---|---|
| Вердикт-честность (бизнес-уровень) | **образцово** | precedence + DeterminismGate + authoritative-флаг |
| Вердикт-честность (парсер-уровень) | **швы** | HD3-IDS-01, HD3-CLASH-01: «тишина = успех» при дрейфе формата |
| Security-периметр | **сильно** | SSRF-pin, path_jail, XML/ZIP caps; остатки — proxy-env, datastore-pin |
| Конкурентность/жизненный цикл | **слабое место №1** | DI-lock, JWKS-ротация, quota-race, IFC-кэш, stale-локи |
| Воспроизводимость | **почти** | HD2-RM-01: origin-фильтр в engine_signature |
| Docs/claims | **сильно, но хрупко** | guard=README-only, RU-маркеры, drift чисел SSOT |

Топ-5 сквозных приоритетов (объединяя раунды): HD3-IDS-01 → HD2-RM-01 → HD3-IFC-01 → HD2-OIDC-01 → HD2-DI-01. Все пять — маленькие диффы с непропорционально большим эффектом на доверие к системе.

## 8. Residual coverage после трёх раундов

Осталось непрочитанным построчно: `ifc_open_shell_validator.py` (420 строк — ядро IFC-проверок), `core/simple_pdf.py`, `privacy_guard.py` (grep-попытка упала на паттерне — не проверен PII-механизм `/Rotate`+counters), `report_html.py` тело (экранирование подтверждено по вызовам `_esc`, но макро-логика не читана), `postgres_audit_store.py` SQL-слой, адаптеры VLM-пайплайнов, `App.tsx` целиком, ~290 тест-файлов. Четвёртый проход, если понадобится: (а) ifc_open_shell_validator + simple_pdf, (б) privacy_guard + VLM-адаптеры, (в) postgres-стор + report_html.
