# Red Team — гиперглубокий аудит (2026-07-28)

> Независимый адверсариальный статический аудит текущего `main` (HEAD `5e2527b`).
> Метод: охота по опасным паттернам + чтение security-критичных мест + проверка
> инвариантов против **фактического кода** (не отчётов). Цель — найти реальные
> дефекты (fail-open, утечки, обход вердикта), а не пересказать закрытое.

## Итог

**Новых эксплуатируемых дефектов не найдено.** Security-критичные места fail-closed,
ключевые инварианты держатся. Применена одна defense-in-depth правка (assert →
явный guard). Checkpoint остаётся **NO_GO** (внешние RT-001/002/003 — не кодом).

## Проверенные поверхности и вердикты

| Поверхность | Что искал | Вердикт | Доказательство |
|-------------|-----------|---------|----------------|
| Code-exec / десериализация | `eval/exec/os.system/shell=True/pickle/yaml.load/marshal/__import__` | **чисто** | нет в `src/`; `subprocess` только в dev-`tools/` без `shell=True` |
| TLS / SSRF-bypass | отключение TLS-верификации (сертификат / hostname / unverified-контекст / env-доверие) | **чисто** | нет в `src/`; простой HTTP разрешён только флагом в негативном тесте |
| SSRF-резолвер | обход `_is_blocked_ip`, второй DNS, редиректы | **fail-closed** | `outbound_url.py`: blocked→`raise`, DNS-пиннинг, `_RejectRedirects`; `assert chosen` — type-narrowing (недостижим при непустом `infos`) |
| Утечка секретов | `api_key/token/secret` в логах | **чисто** | `api_key` только в `Authorization`-хедере; OIDC логирует generic-причину серверно, клиенту — «Invalid API token» |
| Broad-except (ложный успех) | `except Exception` без обоснования | **fail-closed** | `path_jail:137` (`close()`+`raise`), `analyze_orchestrators:489` (discard events+`raise`), audit-store (`raise` при hard/prod) |
| Security-asserts (стрип под `-O`) | `assert` в security-путях | **1 правка** | `outbound_url:227` безопасен (narrowing); `bootstrap:599` (OIDC-конфиг) — заменён на явный `raise` |
| Владение вердиктом | кто пишет `summary.passed` | **единый источник** | только доменная `summary_passed_from_outcome(outcome)` в детерминированных use-case; capability-blocked форсит `False`; advisory-сеттера нет |
| Изоляция advisory-контура | потребляется ли VLM в вердикте | **изолирован** | `ADVISORY_VLM_PIPELINE` резолвится только в тестах; путь вердикта — `MULTIMODAL_DRAWING_PIPELINE`; OFF==ON доказан (`test_advisory_vlm_off_equals_on`) |
| CORS | `*` + credentials | **безопасно** | `allow_origins=settings.cors_origins` (конфиг, не `*`-хардкод), методы GET/POST, `allow_credentials` не выставлен (False) |
| Object-ACL | cross-tenant существование | **404-парати** | `assert_report/job/norm_pack_access` → 404 (не 403), не подтверждает существование чужого |

## Применённая правка (low, defense-in-depth)

**`_build_oidc_validator` (bootstrap.py):** валидация security-конфига OIDC
(issuer/audience/jwks_url) была на `assert`. `assert` **стрипается** под `python -O`.
Сейчас это избыточно (свойство `oidc_enabled` уже истинно только при всех трёх), но
хрупко к рефактору свойства и к запуску под `-O`. Заменено на явный `raise
RuntimeError` — держится под `-O` и при будущем рефакторе. Тест
`test_oidc_validator_build_failclosed.py`: enabled-но-частичный конфиг → `RuntimeError`
(не `AssertionError`), disabled → `None`.

**Честная оценка серьёзности:** НЕ live-уязвимость (текущая ветка недостижима из-за
свойства `oidc_enabled`), а устранение анти-паттерна «assert для валидации».

## Что НЕ закрыто (только внешний вход / политика)

- Живой tier-A Kimi-смоук — ключ оператора.
- RT-001/002/003 — артефакты заказчика (корпус / нормопак / федеративный MEP).
- Project-level ACL — проектное решение (сейчас tenant-level), не баг.
- Per-tenant concurrency-лимит TOCTOU — мягкая квота, не граница безопасности.

## Инварианты (подтверждены против кода)

- Вердикт — только детерминированный движок; **advisory OFF==ON**; fail-closed.
- Новых публичных claims нет; формулировки честные (реплей ≠ детерминизм модели).
- **Checkpoint = NO_GO.**

## Второй проход — весь код + вся документация (2026-07-28)

Расширенный адверсариальный проход по всей кодовой базе и документации. **Существенных ошибок не найдено** — фиксы не фабрикую.

| Проверка | Результат |
|---------|----------|
| Гейты | ruff format (373) + ruff check + mypy (**218**) + pytest (**1295 passed, 8 skipped, 144 subtests**) + baseline drift + markdown-links — **все зелёные** |
| Doc-honesty | каждый рисковый claim (`>90%` / DWG / MEP delivered / production-ready / «reads like human») — **только** в запрещающем/негативном контексте (Claims Lock / «Not claimed» / NOT_VERIFIED / RT-00X open); противоречий claim↔код нет |
| Согласованность чисел | нет устаревших хардкод-счётчиков (README-сниппет в допуске; frontend 29 синхронизирован; исторические снимки помечены датой) |
| Test-integrity | нет полых `assert True`/`xfail`; **8 skip'ов — честные env-гейты** (symlink-privilege Windows ×4, optional extras ezdxf/docling/ifcclash, PyJWT); OpenAPI-snapshot **PASSED** (контракт не дрейфует) |
| Безопасность (1-й проход) | fail-closed подтверждён; OIDC-build `assert`→`raise` уже исправлен |

**Вывод:** код и документация в чистом, внутренне-согласованном и честном состоянии. Исправлять нечего; **Checkpoint = NO_GO** (внешние RT-001/002/003 — не кодом).
