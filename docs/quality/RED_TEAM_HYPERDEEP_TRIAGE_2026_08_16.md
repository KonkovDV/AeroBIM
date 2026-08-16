---
title: "Red Team Hyper-Deep Triage — code + docs full sweep"
status: active
version: "1.0.0"
last_updated: "2026-08-16"
claim_boundary: "Audit report plus later remediations. Does not close or open RT-001/002/003. Checkpoint stays NO_GO. Findings are engineering observations, not customer evidence."
audited_head: "2768058 at audit time; remediations applied on later HEAD (working tree 2026-08-16)"
auditor: "ZCode autonomous triage (single pass, no subagents survived quota; see Methodology)"
---

# Red Team Hyper-Deep Triage — 2026-08-16

Полный триаж кода и документации. Исходный проход **не менял код** (только этот отчёт). Последующий remediation-проход закрыл подтверждённые MEDIUM/LOW из §8; Checkpoint **NO_GO**. Цель: машинно-усвояемый реестр находок для ИИ-ассистента владельца.

**Verdict-вывод аудита:** engineering-ядро зрелое и честное; критических fail-open путей в вердикт-контуре **не найдено**. MEDIUM/LOW из §8 (middleware 429, claims-guard, SSOT drift, outbound pin/proxy/shorthand) закрыты remediation-проходом; Checkpoint **NO_GO**.

---

## 0. Методология и охват

- HEAD `2768058` + рабочее дерево (52 изменённых файла, +905/−271).
- Запланированные 4 параллельных суб-ревизора погибли по квоте провайдера — аудит выполнен одним агентом соло. Это **снижает гарантию покрытия**: часть инфраструктурных адаптеров (~90 файлов) просмотрена grep-матрицей и выборочно, не построчно. Всё, что не прочитано лично, помечено в §9.
- Прочитано полностью: вердикт-путь (`analyze_project_package.py`, `analyze_orchestrators.py` §assemble, `package_outcome.py` ×2, `determinism_gate.py`), SSRF-контур (`outbound_url.py`), `errors.py`, claims-guard тест, `KNOWN_BUGS.md`, `ci.yml` (частично, ключевые job'ы), все security-значимые uncommitted diff'ы.
- Grep-матрица: broad except / except-pass / verify=False / shell=True / eval / pickle / md5 / random / datetime.now / секреты / dangerouslySetInnerHTML / localStorage.
- Канонические ID находок: `HD-<ZONE>-NN`. Severity: CRITICAL / HIGH / MEDIUM / LOW / INFO.

---

## 1. Резюме находок (машино-читаемая таблица)

| ID | Sev | Зона | Файл:строка | Суть | Статус |
|---|---|---|---|---|---|
| HD-MW-01 | MEDIUM | http | `presentation/http/api.py` + `rate_limit.py` | Rate-limit middleware внешняя → 429 без security-заголовков и correlation-id | FIXED |
| HD-CLAIMS-01 | MEDIUM | docs | `audit/claims_forbidden_wording.json` (`scanned_files`) | Forbidden-phrase guard сканирует только README.md | FIXED |
| HD-CLAIMS-02 | MEDIUM | docs | там же (`negation_markers`) | Маркеры негации только английские; RU-доки непроверяемы этим guard | FIXED |
| HD-DOC-01 | MEDIUM | docs | `README.md` vs `docs/evidence/runtime-baseline-latest.json` | README: «48 passed» vitest; baseline: `frontend.tests_passed=54` — drift | FIXED |
| HD-DOC-02 | MEDIUM | docs | `docs/evidence/runtime-baseline-latest.json` | 2271 collected − 2167 passed − 11 skipped = **93 теста не учтены** полем; SSOT не сходится сам с собой | FIXED |
| HD-DIFF-01 | MEDIUM | wip | рабочее дерево, 12 файлов | CRLF→LF churn в незакоммиченной волне; коммит as-is даст шумный diff | HISTORICAL |
| HD-DIFF-02 | MEDIUM | wip | `core/config/settings.py` + `.env.example` | `require_durable_runtime()` ломает boot всех non-dev без Redis — deployment-доки/compose должны синхронизироваться | FIXED |
| HD-SEC-01 | LOW | sec | `core/security/outbound_url.py` | `resolve_dns=False` отдаёт hostname непиннованным (datastore-путь) — DNS-rebinding TOCTOU для config-URL | FIXED |
| HD-SEC-02 | LOW | sec | `outbound_url.py` | `build_opener` чтит `HTTP(S)_PROXY` env → pin может быть реализован через прокси; HTTP-path MITM-наблюдение | FIXED |
| HD-SEC-03 | LOW | sec | `outbound_url.py` | Shorthand-IPv4 (`127.1`, octal `0177.0.0.1`) не ловится literal-парсером; безопасно только при resolve_dns=True | FIXED |
| HD-SEC-04 | INFO | sec | `outbound_url.py` | `_LOCAL_DATASTORE_HOSTS` без `ip6-localhost`, `0.0.0.0`, `[::]`-алиасов | FIXED |
| HD-AUTH-01 | INFO | auth | `oidc_bff_phase3.py` | Phase 3 реализована аккуратно (HMAC + compare_digest, nonce↔state, `__Host-`); секрет только из env, пустой → фаза off | OK-CONFIRM |
| HD-DG-01 | INFO | domain | `determinism_gate.py:165-181` | Divergence-WARNING создаётся реакцией на advisory, но `origin="deterministic"` — терминологическая нюансика, не баг | NEW |
| HD-PAT-01 | LOW | code | `src/aerobim/**` | 92 `except Exception` (большинство с noqa-обоснованием); 96 `datetime.now` в 25 файлах — вне вердикт-путей, но требует инвентаря | NEW |
| HD-PAT-02 | INFO | code | `tools/offline_bundle.py:161` | Генерация `exec(base64.b64decode(...))`-строки для bootstrap — паттерн виден аудиту, исполнения нет | NEW |
| HD-DOC-03 | LOW | docs | `audit/reports/CRITICAL_BLOCKERS.md:3` | «Operational freeze SHA f2615e7» устарел относительно HEAD (док сам требует refresh — self-acknowledged) | KNOWN |
| HD-DOC-04 | LOW | docs | docs/** (166 raw hits сканера) | Guard-слепые зоны: запрещённые фразы в RU-негативном контуре и в allow-file док-ах не машиноверифицируемы — только ручная дисциплина | NEW |
| HD-CI-01 | INFO | ci | `.github/workflows/ci.yml:425` | Единственный `continue-on-error` — dev-lock pip-audit, помечен advisory; осознанный риск | OK-CONFIRM |
| HD-FE-01 | INFO | fe | `frontend/src/**` | XSS-поверхность чистая: 0 `dangerouslySetInnerHTML`, `report_html.py` экранирует `_esc()`; токены не в localStorage | OK-CONFIRM |
| HD-VERDICT-01 | INFO | domain | `analyze_orchestrators.py:843-877` | Вердикт-путь чист: precedence FAILED>BLOCKED>REVIEW>WARN>PASS; `authoritative=False` на soft-профилях; advisory→INFO только | OK-CONFIRM |

CRITICAL/HIGH находок **нет**. Подробности и доказательства — ниже.

---

## 2. Вердикт-контур (что защищает `summary.passed`) — проверено, чисто

### 2.1 Цепочка вычисления вердикта

`analyze_project_package.py:243-270` (execute) → `analyze_orchestrators.py`:

- `analyze_orchestrators.py:781-783` — `error_count`/`warning_count` считаются по `issues_with_remarks` = intake + **reconciled** advisory.
- `analyze_orchestrators.py:843-851` — `compute_package_outcome(...)` единственный владелец вердикта (ADR-001).
- `package_outcome.py:47-55` — precedence: `error_count>0 или hard_clash_blocks → FAILED`; `intake_blocked или capability_blocked → BLOCKED`; `hitl_requires_review → REVIEW_REQUIRED`; warnings → `PASS_WITH_WARNINGS`; иначе `PASS`.
- `domain/package_outcome.py:18-21` — `passed` выводится **только** из outcome (`PASS`, `PASS_WITH_WARNINGS`).
- `analyze_orchestrators.py:854-856` — soft-профили (`development`, `fixture`) получают `authoritative=False`: пройденный fixture не выдаёт себя за production-вердикт.

**Вывод:** LLM не может поднять severity до ERROR — DeterminismGate (`determinism_gate.py:92,131`) жёстко демотирует advisory-only к `Severity.INFO`, противоречия двигателям оформляются как WARNING от имени gate. Худшее, что может advisory — превратить PASS в PASS_WITH_WARNINGS (fail-closed направление). `hitl_required` регионы дают REVIEW_REQUIRED даже при нулевых ошибках (`analyze_orchestrators.py:840-842`) — incomplete evidence никогда не PASS.

### 2.2 Наблюдения (не блокеры)

**HD-DG-01 (INFO):** `determinism_gate.py:179` — divergence-issue создаётся *реакцией* на advisory-шум, но помечается `origin="deterministic"`. Семантически защитимо (gate — детерминированный код), но при аудите цепочки «кто породил finding» вводит в заблуждение. Направление: рассмотреть `origin="determinism-gate"`-специфичное значение или счётчик `advisory_divergence_count` в summary.

**Nondeterminism-карта:** `datetime.now` в 25 src-файлах; в вердикт-пути — только `created_at` отчёта (`analyze_orchestrators.py:862`) и `report_id=uuid4().hex` (:859) — идентичность отчёта, не воспроизводимость; за воспроизводимость отвечает `run_manifest.py` (не изменялся, поле `reproducibility hash` заявлено в WP-01). `random` — только seeded (`eval_statistics.py` ×7, tools) — детерминированно. ОК.

---

## 3. Security-контур

### 3.1 SSRF-guard `outbound_url.py` — сильная реализация, остаточные зазоры

Прочитано полностью (388 строк). Что сделано хорошо: редиректы запрещены (`_RejectRedirects`), DNS резолвится один раз и соединение пиннится к IP при сохранении SNI/Host hostname'а (`safe_urlopen`, :315-375), noncanonical IPv4 (decimal/0x) ловится (:70-87), блок-лист широчайший (0.0.0.0/8, CGNAT, Teredo, 6to4, NAT64 обе префикса, IPv4-compatible ::/96), userinfo в URL запрещён, JWKS host-binding к issuer (:131-157), datastore-jail отдельной политикой (:160-229), «localhost»/metadata.google.internal по имени (:254). Uncommitted-волна закрыла ValueError→False на нераспарсенном IP (теперь блок) и ipv4_mapped рекурсию — правильно.

**HD-SEC-01 (LOW):** `safe_datastore_urlopen` (:303-312) вызывает `assert_safe_datastore_url(..., resolve_dns=False)` и затем `urlopen(request)` — DNS резолвит сам urllib по hostname. Между settings-load-проверкой (resolve_dns=True по умолчанию в :178) и фактическим соединением возможно повторное разрешение (rebinding). Угроза ограничена: datastore URL — операторский конфиг, не пользовательский ввод. Направление: pin и для datastore-пути (переиспользовать `_format_netloc`-механику) или задокументировать как принятый операторский риск.

**HD-SEC-02 (LOW):** `build_opener(_RejectRedirects, ...)` (:365, :370) включает дефолтный `ProxyHandler`, читающий `HTTP_PROXY/HTTPS_PROXY/ALL_PROXY` env. Пинн-ed IP будет набирать прокси, а не хост напрямую: (а) HTTP-path (`allow_http=True`) трафик наблюдаем прокси; (б) env-прокси на loopback обходит дух loopback-блока. Направление: `build_opener(_RejectRedirects, _NullProxyHandler(), ...)` либо осознанное документирование прокси-политики.

**HD-SEC-03 (LOW):** `_parse_literal_ip_host` не распознаёт dotted-shorthand (`127.1`) и octal-dotted (`0177.0.0.1`) — они идут hostname-веткой. При `resolve_dns=True` безопасно (getaddrinfo на glibc резолвит `127.1`→`127.0.0.1`, и `_is_blocked_ip` ловит уже resolved-адрес, :283-291). Опасно только в связке с `resolve_dns=False` (см. HD-SEC-01). Направление: расширить regex на dotted-shorthand-формы.

**HD-SEC-04 (INFO):** `_LOCAL_DATASTORE_HOSTS = {localhost, 127.0.0.1, ::1}` — без `ip6-localhost`/`ip6-loopback` (алиасы в /etc/hosts некоторых дистрибутивов) — уйдут в DNS-ветку datastore-политики и пройдут (non-global для datastore не блокируется). Мелочь.

### 3.2 OIDC BFF Phase 3 — подтверждённо аккуратна (HD-AUTH-01)

`oidc_bff_phase3.py` (305 строк, grep-инспекция): session_id `secrets.token_urlsafe(32)` (:63), HMAC-cookie с `hmac.compare_digest` (:110-135), `__Host-` префикс только при Secure (:104-108), nonce обязателен и биндится к CSRF-state (`_require_nonce` :239-248, require=True на обеих ветках), purge expired (:90-97), client_secret только через параметры. Секрет — `AEROBIM_OIDC_BFF_COOKIE_SECRET`, пустой → фаза не активируется (`settings.py:554-561`): fail-closed по умолчанию. Tenant из OIDC — только из именованного клейма, без fallback на `api_tenant_id` (context.py, RT A07 — комментарий в волне даже усилен). 401 без деталей валидатора (RT A13).

### 3.3 HTTP-слой

**HD-MW-01 (MEDIUM) — middleware-порядок:** `api.py` регистрирует: CORS (:64), auth-hygiene (:78), correlation (:79), security-headers (:80), **rate-limit последним (:86)**. В Starlette последняя добавленная — внешняя. Следствия: (а) 429 от rate-limiter не проходят через security-headers → уходят без CSP/X-Frame-Options/HSTS и без correlation-id; (б) CORS-preflight OPTIONS может быть отлимитчен до того, как CORS-middleware ответит на него. Направление: добавить security-headers/correlation последними (внешними) или дублировать заголовки в 429-ответе rate-limiter. Проверяется тестом: `TestClient` + `Retry` до 429 → `assert "x-frame-options" in resp.headers`.

**Uncommitted-волна в HTTP — целостная и хорошая** (см. §6). Отдельно: `add_auth_header_hygiene_middleware` (security_headers.py) — дубли/oversize/`bearer `-дубликаты в Authorization → 401 до аутентификации. Edge: пароль Basic-auth, содержащий подстроку `"bearer "`, даст ложный 401 (косметика, INFO).

### 3.4 Uploads / архивы / XML

- `zip_limits.py` (волна): контроль-символы в пути ZIP-member → reject — закрывает ANSI-escape/UTF-16-трюки в именах. Traversal/absolute/`:`-drive уже были. Хорошо.
- `xml_limits.py` (волна): добавлены depth-cap (64) и text-node-cap (1M chars) поверх defusedxml + element-cap — закрывает глубокую вложенность и гигантские text-ноды. Хорошо.
- **Не проверено лично построчно:** `upload_quota.py` (TOCTOU счётчика квоты — заявлено CLOSED в RTATOM-I02), `path_jail.py` (Windows-обратные слэши — заявлено в тестах), `upload_content.py`. Помечено как residual-coverage (§9), не как находка.

---

## 4. Claims-режим и документация

### HD-CLAIMS-01 (MEDIUM): guard охватывает один файл

`audit/claims_forbidden_wording.json` → `"scanned_files": ["README.md"]`, исполняет `backend/tests/test_claims_forbidden_wording_guard.py:37-52`. Весь остальной корпус (README.ru.md, docs/**, audit/**) защищён только ручной дисциплиной и allow-file-заголовками (это **другой** механизм — amnesty для claims-lint заголовков, `claims_allow_file_registry.json`). Маркетинговая правка в любом док-е, кроме README, машинно не поймается. Направление: расширить `scanned_files` (хотя бы README.ru.md, docs/TIER0_INDEX.md, ENGINEERING_STATUS) по мере закрытия HD-CLAIMS-02.

### HD-CLAIMS-02 (MEDIUM): негации только на английском

`negation_markers` — 14 английских маркеров. RU-доки негируют по-русски: «Запрещено до доказательств», «Не заявляется», «нет». Полный репозиторий-скан (мой скрипт, та же логика guard) дал **166 raw-хитов**, из которых подавляющее большинство — русско-негированные честные строки (пример: `README.ru.md:48,81`). То есть: (а) guard нельзя просто включить на RU-файлы — упадёт на честных строках; (б) RU-поверхность сейчас вообще не машиноверифицируема. Направление: добавить в SSOT маркеры `не заявляется`, `запрещено`, `нет утвержд`, `не реализовано`, `не проверено`, `вне scope`, `до доказательств`.

### HD-DOC-01 (MEDIUM): drift числа витестов

- `README.md:126`: «Frontend vitest review-shell … **48** passed (frontend CI job)».
- `docs/evidence/runtime-baseline-latest.json`: `frontend.tests_passed = 54`.
README ссылается на baseline как SSOT в той же таблице («counts SSOT via runtime baseline»), но число не синхронизировано. CI-шаг `--check-readme` (WP-01) этого поля, видимо, не покрывает. Направление: включить vitest-число в check или убрать число из README.

### HD-DOC-02 (MEDIUM): baseline не сходится сам с собой

`backend.tests_collected = 2271`, `tests_passed = 2167`, `tests_skipped = 11`, `tests_failed = 0` → **93 теста не учтены** (вероятно, deselected/xfail/параметризационные расхождения `export_runtime_baseline.py` — он собирает collected-ids отдельно, :452-482, поле `uncollected` есть, но в published-baseline не попадает сводка). Для артефакта, который заявлен SSOT честности, необъяснимая дельта 4% — вопрос: любитель Red Team спросит «где 93?». Направление: добавить поля `deselected`/`xfail`/`error` в схему 1.4.x или `unaccounted` с объяснением.

### HD-DOC-03 (LOW): устаревший freeze-SHA

`audit/reports/CRITICAL_BLOCKERS.md:3` — «Operational freeze SHA f2615e7 (2026-07-21)» при HEAD `2768058` и 15+ коммитах после. Док сам говорит «refresh when claiming metrics» — self-acknowledged, но для внешнего аудита выглядит несвежим. Направление: refresh SHA при следующем evidence-бандле.

### HD-DOC-04 (LOW): claims-слепые зоны по существу

Выборочная ручная проверка raw-хитов: `docs/architecture/BCF_EVIDENCE_LADDER_T0_T4_2026_07.md:30` («CDE interoperable» в таблице ступеней — описание целевой ступени, не утверждение), `docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md:318` (заголовок «Accuracy >90% (publishable)» — целевой раздел). Оба файла в allow-registry → формально легальны, но именно такие места — где будущее утверждение может «прорасти» из целевого текста. Направление: per-line allow вместо per-file для этих двух.

### Позитивные подтверждения (docs)

- `KNOWN_BUGS.md` ↔ README/ENGINEERING_STATUS согласованы: 4 активных стаба (`STUB-IDS-ASSIST-001`, `STUB-ODA-CAD-001`, `STUB-IFC-KG-001`, `STUB-MEP-GRAPH-001`) нигде не противоречат claims.
- NO_GO-консистентность: RT-001/002/3 OPEN во всех прочитанных точках (README ×2, ENGINEERING_STATUS, CRITICAL_BLOCKERS, KNOWN_BUGS). Flip-попыток не найдено.
- `claims_allow_file_registry.json`: 0 записей на несуществующие файлы (проверено скриптом).
- Секретов в docs/скриптах/samples не найдено (grep по api_key/secret/password/token-паттернам с литеральными значениями).

---

## 5. CI / инфраструктура / периметр

**HD-CI-01 (INFO):** `ci.yml` — actions запинены SHA-ревизиями, `pip-audit --strict --no-deps` на runtime-lock (блокирующий), подписи коммитов + deferred controls + приват-пути guard. Единственный `continue-on-error: true` — :425, dev-lock audit, явно помечен «advisory». Осознанно.

**Docker/env:** секретов и дефолтных паролей в compose нет; `backend/.env.example` — плейсхолдеры + kill-switch инструкция для LLM-ключа (строка 89). `ports:`曝光 без host-bind ограничений в dev-compose — норма для dev, production-compose в волне изменён — при коммите проверить синхронизацию с `require_durable_runtime` (HD-DIFF-02).

**Frontend (HD-FE-01, OK):** 0 `dangerouslySetInnerHTML` во всём `frontend/src`; отчётный HTML рендерится из бэкендовского `report_html.py`, где всё через `_esc()` (`html.escape(quote=True)`, :13-17). localStorage — только фильтры/пресеты (`App.tsx:74-144`), токены не хранятся; `lib/api.ts:18` — «Never embed a bearer token in client bundles», bearer только через dev-proxy или server-side. `frontend/dist` в git отсутствует (0 файлов). Пин `web-ifc@0.0.77` — осознанный (web-ifc-модуль в lock).

---

## 6. Незакоммиченная волна (52 файла) — триаж

**Тема:** security-hardening вслед за OIDC-лабораторией (продолжение `2768058`): де-идентификация 404/ошибок, ACL-before-payload, anti-spoof тенанта, XML/ZIP caps, durable-runtime fail-closed, CORS `allow_credentials=False`, auth-header hygiene, тесты под всё это.

Позитив (проверено лично по diff):

- `context.py`: `load_authorized_report` — ACL-peek до десериализации payload (peek_tenant_id реализован во всех трёх сторах: filesystem +26, in-memory +7, postgres +52 строк); `resolve_bound_tenant` теперь 400-ит спуф body-тенанта (casefold-сравнение) вместо тихого приоритета; `auth_scheme` (`anonymous|bearer|oidc`) разделён с `is_service_token`.
- `errors.py`: полный набор `public_*_detail()` — 404-е больше не подтверждают существование ID (report/job/norm-pack/IFC-source), ValueError-тексты наружу не утекают.
- `settings.py:595+`: `require_durable_runtime()` — non-dev без Redis не грузится.
- `rate_limit_factory.py`: `fail_closed` параметр + дубль hard-profile логики.
- `clash_detection_runner.py:148`: лог без `ifc_path` (leak hygiene).
- Согласованные тесты: `test_api_security`, `test_mutation_kills_http_context`, `test_security_bomb_guards`, `test_rt_*` — волна тесто-покрыта.

Риски коммита as-is:

- **HD-DIFF-01 (MEDIUM):** ~12 файлов с CRLF (git предупреждает при diff) — коммит без LF-стабилизации даст шумный mixed-EOL diff (в репо уже был отдельный коммит `f380354` про LF-стабилизацию — прецедент есть). Направление: `.gitattributes`/нормализация до коммита.
- **HD-DIFF-02 (MEDIUM):** `require_durable_runtime` — ломающее изменение boot для существующих non-dev деплоев без Redis. Docker-compose.production в волне изменён, но `backend/.env.example` тоже в волне — при ревью проверить, что пример объясняет новое требование явно (а не только код ошибки в runtime). Плюс: релиз-нота обязательна.
- HD-MW-01 (см. §3.3) — middleware-порядок именно в этой волне стал таким, как стал: чинить в этой же волне дешевле всего.

---

## 7. Паттерн-матрица (код-запахи, инвентарь)

- `except Exception` — **92** вхождения в src (плюс except-pass ~16). Большинство обоснованны (adapters, best-effort cleanup, `noqa: BLE001` с комментарием). Топ-кандидат на инвентаризацию: `filesystem_audit_store.py:1058` (TTL cleanup — OK), `_di_factories.py:148`, `ifc_aabb_mep_pair_filter.py:115`. Fail-open анализ каждого вне scope этого прохода — отмечено как residual.
- `datetime.now/utcnow` — 96 вхождений / 25 файлов. В вердикт-контуре не влияют (см. §2.2). В job-stores/quota — ожидаемо.
- `eval/exec/shell=True/verify=False/pickle` — **0** опасных; единственный `exec` — генерируемая строка в `offline_bundle.py:161` (HD-PAT-02, INFO).
- `md5/sha1` — 0.
- Mutation-тесты: `test_mutation_kills_*` существуют и обновлены волной — культура живая.

---

## 8. Рекомендации (приоритет, без правок сейчас)

1. **HD-MW-01** — переставить security-headers/correlation внешними или дублировать заголовки в 429 (малый diff, этой же волной).
2. **HD-DOC-01 + HD-DOC-02** — синхронизировать README↔baseline и добавить в схему baseline поле учёта 93-х тестов; это прямой удар по SSOT-доверию на защите.
3. **HD-CLAIMS-02 → HD-CLAIMS-01** — сначала RU-маркеры в SSOT, затем расширить scanned_files.
4. **HD-DIFF-01/02** — перед коммитом волны: LF-нормализация + релиз-нота про Redis-требование.
5. **HD-SEC-01/02/03** — pin datastore-пути, null-proxy-handler, dotted-shorthand regex (три маленьких патча в один PR по `outbound_url.py`).

---

## 9. Residual coverage (честно о непрочитанном)

Не прочитано построчно (квота убила суб-ревизоров): ~60 infrastructure-адаптеров (IfcOpenShell/IfcTester/ezdxf/VLM-пайплайны — grep-only), `upload_quota.py`/`path_jail.py`/`upload_content.py` (заявленные CLOSED-статусы не перепроверены), `oidc_token_validator.py` (alg-confusion проверка не верифицирована лично — grep по alg не делался), BCF-экспортёры, большинство из 302 тест-файлов, `frontend/src/components/*` построчно, `docs/` за пределами прочитанного (~40% корпуса). Grep-матрица по этим зонам чистая, но построчная гарантия не даётся. Для полного гиперглубокого прохода рекомендован второй заход целевыми пачками по 10-15 файлов.

---

## 10. Верификация этого отчёта

Каждая находка с file:line воспроизводима: `git diff`, `grep -n`, чтение файла на HEAD+working tree. Скрипт claims-сканера (166 raw hits) — inline-Python, логика идентична `test_claims_forbidden_wording_guard.py:37-52` с расширением на все `*.md` вне node_modules. Ничего в репозитории этим аудитом не изменено, кроме данного файла.
