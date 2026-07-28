# Red Team — статус ремедиации (2026-07-28)

- **Проверенный commit (базовая линия аудита):** `3bc812d` (main).
- **Дата проверки:** 2026-07-28.
- **Среда:** Windows, backend `.venv` (Python 3.12); ruff/mypy/pytest локально; CI — GitHub Actions.
- **Способ получения исходников:** рабочее дерево `c:\plans\AeroBIM`, ветка main (синхронизирована с origin).
- **Фактический результат тестов до фикса:** 1254 passed, 7 skipped, 144 subtests (локально).
- **Что не удалось выполнить:** живой вызов VLM (нет ключа оператора); внешние доказательства заказчика (RT-001/002/003) недоступны разработке.

> Метод: утверждения сверены с кодом/тестом/артефактом. Исторические отчёты не считались доказательством текущего состояния main.

## P0 — исправлено этим заходом

### RT-2807-01 — Межарендаторная изоляция кэша VLM не закреплена структурно
- **Статус:** закрыто тестом (в пределах проверенного сценария).
- **Класс:** ошибка кода (fail-open по умолчанию) / остаточный риск из §5, §17.1, §17.10.
- **Файлы/символы:** `infrastructure/di/bootstrap.py::_build_advisory_vlm_pipeline`, `_safe_cache_namespace`; `core/config/settings.py::kimi_cache_namespace`.
- **Воспроизведение (до фикса):** `ADVISORY_VLM_PIPELINE` — процессный singleton; при заданном `kimi_cache_dir` строился `FilesystemVlmResponseStore` с пустым namespace → один физический кэш и один ключ на всех арендаторов. У `read_region` нет per-request identity, поэтому construction-time namespace `""` означал общий кэш.
- **Влияние:** при будущем подключении контура к многоарендаторной поверхности — повторное воспроизведение ответа одного арендатора для другого.
- **Смягчение до фикса (честно):** `kimi_advisory_ready()` жёстко выключен на `samolet_pilot`/`production`, и контур не потребляется ни одной поверхностью → риск был ограничен dev/fixture-профилями (тестовые данные).
- **Исправление:** новый `kimi_cache_namespace` (только из доверенной deployment-конфигурации — не из тела запроса/имени файла/sheet_id/ответа модели). Постоянный кэш строится **только** при валидном namespace; иначе — **fail-closed: кэш отключён** (никогда не общий). Namespace валидируется (`[A-Za-z0-9._-]`, 1–64, без `.`/`..`, без разделителей) и физически изолирует каталог (`kimi_cache_dir/<namespace>`) поверх namespace-в-ключе.
- **Тесты (регресс):** `tests/test_advisory_cache_tenant_isolation.py` — отключение без namespace; включение и физическая изоляция с namespace; разные арендаторы → разные корни; path-unsafe namespace → fail-closed; unit на `_safe_cache_namespace`.
- **Критерий готовности:** ruff/mypy зелёные; тесты зелёные; вердикт не изменился (advisory вне verdict-пути); новых claims нет.
- **Закрыто позже (тема «cache», коммит ee37926):** key-safety (sha256-hex, без traversal), symlink-refusal, TTL + удаление, owner-only perms на store — с регресс-тестами. Symlink/TTL/key-safety **доказаны на Linux** через Docker (`python:3.12-slim`, Debian 13 trixie): 14/14 cache-тестов, `test_symlink_target_is_refused` PASSED (не skipped). Артефакт: `audit/evidence/vlm-cache-linux-store-proof-2026-07-28.json`.
- **Остаётся:** привязка namespace к проверенной личности в реальном потребителе (когда контур будет подключён); symlink-тест на Windows по-прежнему skip (нет `os.symlink` без привилегии) — покрыт Linux-доказательством.

## Проверено и подтверждено как уже закрытое (без изменений)

- **Итоговый вердикт (инвариант):** `summary.passed` формирует только `DeterministicValidationOrchestrator`; advisory идёт через `DeterminismGate` — подтверждено тестом `test_advisory_vlm_off_equals_on.py` (OFF==ON на реальном UC). Advisory-VLM — отдельный токен, не потребляется UC.
- **Prompt-injection через изображение:** вывод VLM — только кандидат-данные по строгой §4-схеме; наш нормализатор игнорирует модельный `normalized_value`; капы ≤128 observations/регион, ≤512 символов raw_value — подтверждено `test_vlm_region_schema.py`.
- **Overtrust самозаявленной уверенности:** по умолчанию HITL для каждого кандидата (verbalized confidence некалибрована) — подтверждено тестом.
- **NaN/Infinity, out-of-range bbox, обрезанный/пустой ответ, oversize изображения:** отбиваются/деградируют — подтверждено тестами.
- **Кэш-целостность:** golden content_sha256 + `entry_matches_request` (второй слой) — подтверждено тестами; ключ включает schema/normalizer/reasoning_effort/namespace.
- **CI/цепочка поставок:** SHA-пины actions обновлены до Node24 (checkout/setup-python/setup-node/upload-artifact → v7), старых SHA нет, lock-drift зелёный — подтверждено `gh run` (последний CI success).

## Частично закрыто / остаётся

- **Полная метапроверка кэша (§5.6):** ключ дискриминирует конфиг; физический TTL/perms/symlink-guard — **остаётся**.
- **Живой smoke tier-A (§17.7):** инструмент честно `NOT_RUN` без ключа; артефакта нет — **остаётся** (нужен оператор).
- **Хеши плана/кропов (§17.8):** `region_plan_sha256` и `crop_sha256` присутствуют; сквозная сверка на реальном листе — не выполнена.

## Второй проход (2026-07-28, комплексный re-audit)

Повторный независимый прогон по всеобъемлющему промпту. Большинство P0/P1 уже закрыто выше и в коммитах сессии; ниже — что добавлено и что честно остаётся.

**Закрыто этим проходом:**
- **§4.3 частичный отчёт (mid-run cancel):** runner-тест доказывает — отмена, пришедшая ВО ВРЕМЯ анализа, дискардит отчёт и не публикует его как завершённый (job → CANCELLED, `report_id` остаётся None). `test_mid_run_cancel_discards_report_and_never_succeeds`.
- **§7 project namespace:** ключ кэша и физический каталог store теперь включают `project` под tenant; два проекта одного арендатора не делят ответы. `kimi_cache_project` (fail-closed при заданном-но-невалидном). Тесты: дискриминация ключа, изоляция проектов, physical scope, fail-closed.

**Честно остаётся / вне кода:**
- **Project-level ACL (§4.1 «два проекта»):** объектный ACL сейчас **tenant-level** (у отчёта/джобы — `tenant_id`, поля `project_id` для ACL нет). Проектная изоляция ACL — проектное решение, а не баг; **не изобретаю** без требования. Кэш при этом проектно-изолирован (§7).
- **Redis `SET NX` (§4.3) — исправление предыдущей неточности:** Redis-бэкенд стора **СУЩЕСТВУЕТ** (`RedisAnalyzeProjectPackageJobStore`, выбирается при `AEROBIM_REDIS_URL`) и использует `set(nx=True)` (**SET NX**) для атомарного клейма idempotency-индекса И создания job-ключа, плюс WATCH/MULTI compare-and-set для переходов. Дефолт/тесты — `InMemory` (Lock + `can_transition` + дедуп). Добавлен конкурентный тест (16 потоков, один idempotency-key → ровно одна job).
- **Известное ограничение (low):** per-tenant concurrency-лимит в `SubmitJob` — TOCTOU (`count_active_for_tenant` и `create` в разных lock-скоупах) → под burst возможен overshoot на 1+. Это **мягкая квота**, не граница безопасности/вердикта; не фикшу половинчато (InMemory-only оставил бы Redis несогласованным). Атомарность самого create-дедупа — доказана тестом.
- **Lockfile drift-гейт (рекуррентная тайм-бомба) — устранена:** CI-проверка теперь **засеивает** выходной файл закоммиченным локом перед `uv pip compile` (без `--upgrade`) → uv **сохраняет** удовлетворяющие пины (pip-tools-семантика). Гейт ловит только реальное расхождение pyproject↔lock (dep добавлен/удалён/сменён constraint), а не апстрим-патч. Доказано локально дискриминирующим прогоном (seed=fastapi 0.140.7 при доступной 0.140.8 → сохранён 0.140.7). Hash-pinning и pip-audit сохранены; свежесть/security-bumps — за Dependabot (PR-канал).
- **Frontend HITL (§12) — ЗАКРЫТО (frontend-волны):** advisory-кандидат vs подтверждённая находка, low-confidence cue, review_required-бейдж — визуально различены + vitest (`6a3779f`, `acd91b0`, `2ac9d94`); XSS через текст предотвращён React (нет `dangerouslySetInnerHTML`); MIME/Blob-guard уже был (`api.ts`, RTATOM-F05).
- **RT-001/002/003** — внешние (ниже).

## Внешние блокеры (нельзя закрыть кодом)

- **RT-001** — точностной adjudicated-корпус заказчика.
- **RT-002** — одобренный нормопак.
- **RT-003** — федеративный MEP (IFC + подписанный scope memo + матрица зазоров).

## Что должен сделать владелец проекта

- Решить политику namespace для будущего потребителя контура (привязка к tenant_id/project_id проверенной личности).
- При включении кэша задать `AEROBIM_KIMI_CACHE_NAMESPACE` из доверенной конфигурации.

## Что должен предоставить заказчик

- Данные для RT-001/002/003 (корпус, нормопак, федеративный MEP).

## Чего нельзя заявлять публично

- «кэш защищён» / «данные изолированы» без оговорки — корректно: «изолировано в пределах проверенного сценария указанными отрицательными тестами».
- «результат детерминирован» для модели — корректно: «повторно воспроизводится сохранённый ответ при совпадении входов и версий».
- Checkpoint остаётся **NO_GO** (RT-001/002/003 открыты).

## Полная сводка сессии 2026-07-28 (от и до)

Консолидация всей работы сессии (`223ecc8..f9c2231` на main). Всё закоммичено, запушено, **CI зелёный** (`f9c2231`). Инварианты целы: вердикт — только детерминированный движок, **advisory OFF==ON**, fail-closed; **новых claims нет**.

**Финальные цифры:** backend — 1303+ test functions (1293 pytest passed, 8 skipped, 144 subtests); frontend — 29 vitest; ruff/mypy/build зелёные.

| Тема | Сделано | Ключевые коммиты |
|------|--------|----------------|
| Deps/CI | pytest 9.x (CVE), Node20→Node24 SHA-pinned actions, relock fastapi/tqdm, **lockfile drift-гейт seed-preserve** (снята тайм-бомба) | `150090e`, `847d566`, `b119fc0`, `490e320`/`1aaf7d7` |
| Advisory-кэш (act-grade) | ключ с дискриминаторами + provenance + сплит replay/model-determinism + metrics | `c7981d3`, `a844f2c`, `05e37f4` |
| Кэш-изоляция/безопасность | tenant fail-closed, project sub-scope, key-safety/symlink/TTL/perms, hash-per-field, Linux Docker-доказательство | `ab7da56`, `e80e551`, `ee37926`, `cc6a9f7`, `d14e298` |
| Prompt-injection/grounding | image-капы + containment, uncalibrated confidence→HITL, запрет control-полей + evidence_note truncation flag, BCF-инъекция инертна | `0f9ddb1`, `dda0f58`, `efb0c7b`, `15a44c5` |
| Object-ACL (cross-tenant→404) | report/IFC/BCF/review (были) + export json/html + jobs get/cancel + drawing-preview | `3d121df`, `6a228bd` |
| Фоновые задания §9 | idempotency-дедуп (tenant-scoped) + cancel/no-resurrection + mid-run discard + concurrency (16 потоков) | `6670fb2`, `d614235`, `2e31dd5` |
| Storage §8 | zip/XML-bomb negative-тесты (гварды были; size-до-памяти в uploads) | `b2d6b03` |
| Frontend HITL §12 | advisory-кандидат, low-confidence, review_required — визуально + vitest | `6a3779f`, `acd91b0`, `2ac9d94` |

**Остаётся (только внешний вход / политика):** живой tier-A Kimi-смоук (ключ оператора); RT-001/002/003 (артефакты заказчика); project-level ACL (проектное решение, не баг); concurrency-лимит TOCTOU (мягкая квота). Ничего из этого не закрывается кодом без внешнего входа. **Checkpoint — NO_GO.**
