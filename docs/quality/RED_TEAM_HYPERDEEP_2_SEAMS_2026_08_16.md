---
title: "Red Team Hyper-Deep Round 2 — seams, gaps, blind spots, rough edges"
status: active
version: "1.0.0"
last_updated: "2026-08-16"
claim_boundary: "Audit report plus later remediations. Checkpoint stays NO_GO. Round 2 of RED_TEAM_HYPERDEEP_TRIAGE_2026_08_16.md (IDs HD-); this round uses IDs HD2-."
audited_head: "2768058 (committed) + uncommitted working tree 2026-08-16"
auditor: "ZCode autonomous triage, round 2 (solo — subagent quota still unavailable)"
---

# Red Team Hyper-Deep Round 2 — швы, зазоры, слепые пятна, шероховатости

Второй проход по местам, которые раунд 1 пометил residual-coverage: DI, персистенция, лимитеры, OIDC-валидатор токенов, uploads-контур, run_manifest, BCF-экспорт, фронтенд-ресурсы. Фокус — **швы между компонентами**, а не повторная проверка вердикт-пути (он чист, см. раунд 1 §2). Последующий remediation-проход закрыл приоритеты §10; Checkpoint **NO_GO**.

**Сквозной вывод раунда 2:** слабое измерение кодовой базы — не логика и не честность (они образцовые), а **конкурентное состояние и жизненный цикл**: гонки холодного старта DI, ротация JWKS, дисковая гонка квоты, устаревшие file-lock'и, семантический дрейф между in-process и Redis-реализациями одного порта. Каждый пункт мелкий; вместе они образуют узнаваемый профиль «сильный соло-инженер, редкие конкурентные сценарии не тренированы».

---

## 1. Реестр находок (машино-читаемо)

| ID | Sev | Зона | Файл:строка | Суть | Статус |
|---|---|---|---|---|---|
| HD2-OIDC-01 | MEDIUM | auth | `infrastructure/security/oidc_token_validator.py` | Неизвестный `kid` после ротации ключей IdP → 401 до истечения JWKS TTL (3600 c); нет refetch-on-miss | FIXED |
| HD2-RM-01 | MEDIUM | domain | `domain/run_manifest.py` | Advisory исключается из reproducibility-хеша по префиксу rule_id, а не по `origin` — LLM-текст может попасть в «детерминированный» хеш | FIXED |
| HD2-RL-03 | MEDIUM | http/deploy | `presentation/http/rate_limit.py` | Ключ лимитера = сокет-пиp; за reverse-proxy все анонимы делят один бакет `proxyIP:anon` → коллективный self-DoS | FIXED |
| HD2-UP-01 | MEDIUM | uploads | `presentation/http/routes/uploads.py` | Диск пишется до `reserve`: параллельные загрузки тенанта проходят pre-check и заливают N×max_bytes в карантин до отказа квоты | FIXED |
| HD2-DI-01 | MEDIUM | di | `core/di/container.py` | Singleton-инициализация без lock: конкурентный холодный resolve запускает фабрику дважды | FIXED |
| HD2-RL-01 | LOW | sec | `redis_rate_limiter.py` vs `rate_limit_backend.py` | Один порт, две семантики: Redis fixed-window vs in-process sliding-window | DOCUMENTED |
| HD2-RL-02 | LOW | sec | settings + backends | `max_events<=0` → `allow()`=True: ноль в конфиге молча отключает бакет | FIXED |
| HD2-UQ-01 | LOW | sec | `core/security/upload_quota.py` | Файловый lock O_EXCL без stale-TTL | FIXED |
| HD2-UP-02 | LOW | uploads | `uploads.py` | Крэш между reserve и promote утекает квоту; реконсиляции для квоты нет | FIXED |
| HD2-PJ-01 | LOW | sec | `core/security/path_jail.py` | Write-путь `open_storage_file` без O_NOFOLLOW | FIXED |
| HD2-OIDC-02 | LOW | auth | `oidc_token_validator.py` | Нет leeway на рассинхрон часов | FIXED |
| HD2-OIDC-03 | INFO | auth | `oidc_token_validator.py` | TTL кэша JWKS по wall-clock | FIXED |
| HD2-RL-04 | INFO | http | `rate_limit.py` | 429 без `Retry-After` | FIXED |
| HD2-DI-02 | INFO | di | boot | Settings снапшотятся на boot | DOCUMENTED |
| HD2-BCF-01 | INFO | bcf | `bcf_report_exporter.py` | Имена zip-записей из `topic_guid` без валидации имени | FIXED |

**OK-подтверждения раунда 2** (проверено, чисто): path_jail целиком (NFKC, percent-decode, ADS/NTFS, reserved names, 8.3-aware fallback, O_NOFOLLOW на чтении), upload_quota check-and-increment под эксклюзивным lock, redis job store cancel/tombstone-семантика, BCF zip строится только из генерируемых GUID, frontend disposal (web-ifc `CloseModel`/`Dispose`, `geometry.delete()`, `revokeObjectURL`), VLM persistent cache fail-closed без валидированного tenant-namespace (`_di_factories.py:384-405`), OIDC alg-pinning (RS256 default, PyJWK kty-guard).

---

## 2. Швы аутентификации

### HD2-OIDC-01 (MEDIUM): ротация JWKS ломает логин на час

`validate()` ищет `kid` в кэшированном JWKS; промах → сразу `OidcValidationError("No JWKS key matched kid")` (`oidc_token_validator.py:68-69`). Кэш живёт 3600 c и инвалидируется только по времени (`:94-101`). Стандартная практика — при неизвестном `kid` сделать **один** принудительный рефетч и повторить поиск; здесь этого нет. Сценарий: IdP ротирует ключи → все новые токены 401 до получаса-часа; для контура «лаборатория перед демо Самолёта» это демо-киллер. Направление: `except kid-not-found → force refetch → retry once`, плюс лог с метрикой.

### HD2-OIDC-02 (LOW) / HD2-OIDC-03 (INFO)

Нет `leeway` на exp/nbf (`:71-84`) — рассинхрон часов между сервисом и IdP даёт спорадические 401. TTL по `time.time()` — NTP-скачок назад продлевает жизнь устаревшего JWKS. Обе мелочи лечатся одним параметром и `time.monotonic()`.

## 3. Шов reproducibility-хеша (HD2-RM-01)

`engine_signature()` (`run_manifest.py:58-78`) заявлен как «deterministic findings only — excludes advisory agent noise», но фильтр `_is_advisory_issue` (`:50-55`) смотрит только на `source_id == "compliance-agent"` и префиксы `AGENT-*`/`AEROBIM-AGENT-*`. При этом DeterminismGate **демотирует** advisory-only находки до INFO, сохраняя их исходный `rule_id` и вкладывая LLM-текст в `message` (`determinism_gate.py:113-145`). Итог: любая advisory-находка с «обычным» rule_id (а LLM-экстрактор именно такие и порождает) попадает в `engine_signature` → в reproducibility-хеш. Пока HybridRouteGate выключен (дефолт), хеш стабилен; при включённом advisory хеш будет меняться от прогона к прогону — и что хуже, **тихо**: никто не сравнит «детерминированный» хеш с LLM-шумом внутри. Направление: добавить в фильтр `getattr(issue, "origin", "") == "advisory"`; тест — прогон с advisory-issue обычного rule_id не должен менять хеш.

Замечание честности: это не ломает вердикт — ломает **доказуемую воспроизводимость** репорт-хеша, которая продаётся как WP-01 фича.

## 4. Швы rate-limiting

- **HD2-RL-03 (MEDIUM, деплой):** ключ = `request.client.host` + sha256(Authorization)[:16] (`rate_limit.py:52-56`). За TLS-терминирующим прокси `client.host` — адрес прокси: все **анонимные** пользователи делят один бакет `proxy:anon` на `requests_per_minute`. Прикрепление Authorization разделяет аутентифицированных, но анонимный контур (health, публичные GET, форма логина) коллективно душится. Направление: доверенный XFF (только от известного прокси) или явное требование аутентификации для лимитируемых маршрутов + документирование прокси-топологии.
- **HD2-RL-01 (LOW):** Redis-бэкенд — fixed-window (Lua INCR+EXPIRE, атомарно, корректно; `redis_rate_limiter.py:7-16`), in-process — честный sliding-window (`rate_limit_backend.py:22-35`). Один и тот же конфиг даёт разное эффективное поведение (2× burst на границе окна у Redis). Тесты гоняют in-process → Redis-граничные кейсы не покрыты. Направление: унифицировать на sliding-window-в-Lua или задокументировать дельту.
- **HD2-RL-02 (LOW):** `max_events <= 0 → return True` в обоих бэкендах — «0 = выкл». Опечатка в конфиге (`AEROBIM_RATE_LIMIT=0`) молча снимает лимит с login/analyze. Направление: валидировать положительность в settings для боевых профилей.
- **HD2-RL-04 (INFO):** 429 без `Retry-After` — клиенты будут ретраить вслепую.

## 5. Швы uploads/квоты

Контур построен правильно: quarantine → magic-bytes/zip-inspect → reserve(атомарный check-and-increment под O_EXCL-lock) → promote(rename) → object-store, с компенсациями release при каждой ошибке. Остались:

- **HD2-UP-01 (MEDIUM):** порядок «сначала пишем на диск, потом резервируем» (`uploads.py:109-138` пишет, `:172` резервирует). Pre-check `assert_can_accept` (:76) — консервативный (max_bytes), но не атомарный с reserve. N параллельных загрузок одного тенанта → N×max_bytes в карantine до первого отказа. Частично смягчено POST-rate-limit'ом на `/v1/uploads/` и `max_upload_bytes`; но это именно квотный обход на уровне диска. Направление: reserve-заранее-и-компенсация, либо per-tenant semaphore на одновременные upload'ы.
- **HD2-UQ-01 (LOW):** file-lock через `os.open(O_CREAT|O_EXCL)` с `unlink` в finally (`upload_quota.py:89-104`) — крэш процесса между open и finally оставляет `.lock` навсегда; все последующие мутации квоты этого тенанта — `RuntimeError("Could not acquire upload-quota lock")`. Нет stale-детекции по возрасту файла. Направление: mtime-based takeover (lock старше X минут → steal) или fcntl/msvcrt-локи.
- **HD2-UP-02 (LOW):** крэш между reserve и promote утекает зарезервированные байты (файл в карантине, счётчик растёт). Для audit-store есть `reconcile_audit_orphans` — для квоты аналога нет.

## 6. Швы DI/жизненного цикла

- **HD2-DI-01 (MEDIUM):** `Container.resolve` (`core/di/container.py:35-41`) — `if registration.instance is None: registration.instance = factory(self)` без синхронизации. FastAPI sync-endpoints в threadpool'е → два конкурентных первых запроса на холодном_singleton запускают фабрику дважды. Последствия зависят от фабрики: двойной `RedisRateLimitBackend` (два пула), двойные mkdir/регистрации, у «проигравшего» экземпляра — мусор со слаботочными ссылками. Не безопасность, но источник трудноуловимых «иногда при старте». Направление: `threading.Lock` вокруг создания + double-checked.
- **HD2-DI-02 (INFO):** все настройки читаются фабриками один раз при первом resolve singleton'ов — рантайм-переконфигурация невозможна без рестарта. Стоит зафиксировать явно в deployment-доке.

## 7. Швы storage/path_jail

`path_jail.py` — лучший файл аудита: NFKC-нормализация до проверок, одинарный percent-decode, NTFS ADS/colons, reserved devices в любом компоненте, trailing dots/spaces, 255-лимит, `safe_storage_token` с collision-free `!hex`-кодированием, O_NOFOLLOW на чтении, 8.3-fallback. Осталось:

- **HD2-PJ-01 (LOW):** write-ветка `open_storage_file` (mode != "rb") делает reject-проверки, потом `path.open(mode)` — между проверкой и open окно подмены на symlink (POSIX, локальный атакующий). Направление: `O_NOFOLLOW|O_CREAT` + `os.fdopen` и на запись.
- **HD2-PJ-02 (INFO):** fallback-ветка `reject_symlinks` (:73-81) сравнивает **нерезолвленные** пути, когда `relative_to(resolve())` падает (Windows 8.3) — эскейп-детекция в этой ветке слабее; спасает двойная проверка вызывающих (`resolve_storage_path:207-209`). Шов задокументировать.

## 8. BCF и job-сторы

- **HD2-BCF-01 (INFO):** экспортёр пишет члены `f"{topic.topic_guid}/markup.bcf"` без валидации имени (`bcf_report_exporter.py:79-81`). Сегодня guid — uuid4; при появлении импортируемых BCF (ingest уже есть!) чужие topic_guid попадут в переписывание — санитизация на границе нужна заранее. Потребительская сторона (zip-slip у жертвы) — вне нашего контроля, но гигиена имени дешева.
- Redis job store: `cancel_requested`-флаг, `mark_cancelled`, tombstone-стадии — семантика отмены присутствует и консистентна с RTATOM-G03. OK.
- `in_memory` vs `redis` job stores: семантики статусов совпадают по grep-признакам; построчное сравнение не делалось (residual).

## 9. Frontend-ресурсы

`ifc-scene.ts`: `CloseModel`, `ifcApi.Dispose`, `flatMesh.delete()`, `ifcGeometry.delete()`, `disposeObject` c geometry/material dispose, `controls.dispose`, `renderer.dispose`; `api.ts:188` и `App.tsx:644` — `revokeObjectURL`. Ошибки фетчей идут в state (`App.tsx:371-375,408-412`). Единственная шероховатость: `catch {}`-блоки без логгирования (`App.tsx:84,134,597,617,646,681,703`) — тихое проглатывание не-критичных ошибок разбора; осознанно, но при отладке станет слепым пятном. INFO.

## 10. Приоритеты раунда 2

1. **HD2-RM-01** — фильтр по `origin` в `engine_signature` + тест (защита продающейся фичи воспроизводимости).
2. **HD2-OIDC-01** — refetch-on-miss JWKS (стабильность демо-контура).
3. **HD2-DI-01** — lock в `Container.resolve` (трёхстрочный фикс, убирает класс «иногда на старте»).
4. **HD2-RL-03 + HD-MW-01 (р1)** — прокси-aware ключинг + заголовки на 429 (единый PR про периметр).
5. **HD2-UP-01/UQ-01** — reserve-ahead или semaphore + stale-lock takeover.

## 11. Residual coverage раунда 2

Не прочитано построчно: адаптеры IfcOpenShell/IfcTester/ezdxf/VLM-пайплайны, `settings.py` полный (1014 строк; проверены точки волн), `filesystem_audit_store.py`/`postgres_audit_store.py` целиком (читаны diff'ы и peek-семантика), `App.tsx` весь (grep + фрагменты), `report_html.py` тело (экранирование подтверждено по всем точкам вызова `_esc`), `oidc_bff_phase3.py` тело (grep-инспекция крипто-точек), `exports.py` маршрут целиком, norm-pack loader, review_event_store. Для третьего прохода рекомендованы пачками: (а) адаптеры движков, (б) сторы целиком, (в) settings+routes.
