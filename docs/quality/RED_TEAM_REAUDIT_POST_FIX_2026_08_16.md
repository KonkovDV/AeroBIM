---
title: "Red Team Re-Audit post-fix — fix scorecard + new findings"
status: active
version: "1.1.0"
last_updated: "2026-08-16"
claim_boundary: "Original pass was audit-only at 4b410c9. §5 records remediations. Checkpoint stays NO_GO. Not product accuracy."
audited_head: "4b410c9 (+ working tree remediations)"
auditor: "ZCode autonomous triage, round 6 (solo) + round-6 remediations"
---

# Red Team Re-Audit — проверка исправлений + новые находки

## 1. Скорборд исправлений (по реестру раундов 1–5)

| ID | Было | Статус | Доказательство |
|---|---|---|---|
| HD3-IDS-01 | `get("status", True)` — fail-open при дрейфе | **FIXED** | `ifc_tester_ids_validator.py:127` `spec.get("status")` (None уходит в SKIPPED-guard); `:205` `requirement.get("status") is True` — строго |
| HD2-RM-01 | advisory в reproducibility-хеше по префиксу | **FIXED** | `run_manifest.py:50-53` — фильтр `origin=="advisory"` добавлен до конвенции |
| HD2-DI-01 | singleton-гонка в DI | **FIXED** | `container.py:27,47` — `RLock` вокруг инициализации |
| HD2-OIDC-01 | JWKS без refetch-on-miss | **FIXED** | `oidc_token_validator.py:38,77-88` — force-refetch с cooldown (`_FORCE_JWKS_COOLDOWN_S`) и повторным поиском |
| HD3-IFC-01 | вечный кэш IFC-моделей | **FIXED** | `ifc_file_open.py:22,80` — `MAX_CACHED_MODELS=8`, `_evict_overflow_locked`, `evictions` в stats |
| HD-MW-01 | 429 без security-заголовков | **FIXED** | `api.py:72→97` — rate-limit теперь внутренняя, security-headers внешняя |
| HD3-CLASH-01 | молчаливый continue малформированных записей | **FIXED** | `ifc_clash_detector.py:224-229` — `discarded`-счётчик → `ClashCapabilityError("failed", "format drift")`; плюс отбраковка пустых GUID |
| HD3-BFF-02 | UnicodeEncodeError на куке | **FIXED** | `oidc_bff_phase3.py:128-136` — `encode("ascii")` внутри try, `UnicodeEncodeError` в catch |
| HD3-EXP-01 | неизвестная BCF version → 2.1 | **FIXED** | `exports.py:84-96` — 400 «Unsupported BCF version» |
| HD-DOC-01 | README 48 vs baseline 54 | **FIXED** | `README.md:126` — «**54** passed … SSOT `frontend.tests_passed`» |
| HD-DOC-02 | 93 теста не учтены | **FIXED** | baseline: поле `tests_unaccounted: 93` — дельта явная |
| HD-CLAIMS-01/02 | guard = README-only, без RU-маркеров | **FIXED (см. HDX-LINT-01)** | новый `scripts/lint_claims.py` — CI в 4 режимах (:112-118), свой тест, scan-roots шире (README×2, frontend/src, customer, partners) |
| HD2-RL-03 | прокси-бакет анонимов | **FIXED** | `rate_limit.py:35-41` — `client_bucket_host`: XFF только от `trusted_proxy_ips` |
| HD2-UQ-01 | stale-lock брикает квоту | **FIXED** | `upload_quota.py:104-108` — mtime-takeover при `age >= _LOCK_STALE_S` |
| HD2-RL-02 | `max_events=0` отключает лимит | **BY-DESIGN** | «0 = off» сохранён как осознанный выбор; guards `>0` перед allow() |
| HD2-UP-01 | диск до reserve (гонка) | **FIXED** (recheck) | `uploads.py`: `reserve(..., hold_id=upload_id)` до `quarantine.open("wb")`; pin `test_upload_route_reserves_quota_before_writing_quarantine` |
| HD3-BFF-01 | enforcement `identity_verified` | **FIXED** (recheck) | `require_verified_bff_session` fail-closed; `require_bearer_auth` не принимает Cookie (`test_api_bearer_auth_does_not_accept_session_cookie`) |
| HD-DIFF-01 | CRLF-шум | **RESOLVED** | волна закоммичена (34ef0b0..4b410c9), дерево почти чистое |

**Итог исходного прохода: 14 из 17 позиций закрыты корректно, 1 осознанно оставлена, 2 не перепроверены.** После §5: 16 из 17 закрыты, HD2-RL-02 остаётся BY-DESIGN. Качество фиксов высокое: каждый — с тестом или механизмом, ни один не «заметён под ковёр».

## 2. Новые находки этого прохода (HDX-*)

### HDX-AG-01 (MEDIUM): рассинхрон областей в новом Acceptance Gate

`domain/ifc_acceptance_gate.py` (новый sell-path, 201 строка): `outcome`/`passed` проецируются из **полного** пакета (:130-149, любой ERROR любой категории → `failed`), а `findings`/`blocking_finding_count` — только из категорий IFC/IDS (`:24-31,95`). Пакет, заваленный, например, ERROR'ом `package_completeness` или signature-audit, даст артефакт **`outcome=failed` при `blocking_finding_count=0`** — «красный без единой красной находки» в лице продукта. Направление: поле `outcome_scope: "full_package"` + `blocking_outside_projection_count`, либо консистентная проекция области.

### HDX-AG-02 (LOW): третья копия advisory-декодера

`_is_advisory` (`:79-88`) дублирует логику `run_manifest._is_advisory_issue` (origin + `AGENT-` префиксы + compliance-agent). Три места одной конвенции (эффективно: determinism-gate, run_manifest, acceptance gate) — drift-risk при следующем изменении. Направление: единая функция в domain.

### HDX-AG-03 (INFO): «critical» вне перечня Severity

`:160` — blocking-множество `{"error", "critical"}`; в enum Severity `critical` отсутствует. Мёртвая ветка future-proofing — безвредна, но сигнал: множество писалось «на глаз».

### HDX-LINT-01 (LOW): исключения claims-lint воссоздают слепую зону

`scripts/lint_claims.py` покрывает больше файлов, но `_EXCLUDE_PATH_FRAGMENTS` исключает целиком `docs/architecture/`, `docs/ai/`, `docs/roadmap/`, `docs/research/`, `docs/partners/`, `docs/quality/`, `docs/review/`, `docs/gtm/` — там дрейф формулировок снова невидим машинно (остаётся allow-file+реестр как ручной механизм). Для честности стоит: (а) сузить исключения до конкретных файлов, (б) или добавить счётчик «сколько файлов исключено» в вывод линта.

### HDX-VERIF-01 (INFO): неперепроверенное в этом раунде

RU-список маркеров/фраз внутри `lint_claims.py` (выводился только каркас), enforcement `identity_verified` (HD3-BFF-01), дисковая гонка квоты (HD2-UP-01), Redis-job-стор после правок 34ef0b0, новые untracked-инструменты (`run_pnst909_22_scenario_runtime.py` и др.).

## 3. Аудит новой фичи «IFC Acceptance Gate as the only sell path» (47922a9)

Позитив: pivot оформлен по канонам проекта — `claim_boundary` внутри артефакта (`:18-22`), `checkpoint_verdict: "NO_GO"` в каждом выводе, `customer_accuracy: False`, ADR-001 self-check (`:141-146`: `passed != outcome-производная → AcceptanceGateError`), advisory отфильтрован, `require_fixture_gate` запрещает демо-пакету «случайно пройти» (`:191-201`). README/GT-доки переспряжены на новый sell path. Единственный содержательный дефект — HDX-AG-01 выше.

## 4. Вердикт re-audit

Волна исправлений — **исполнена дисциплинированно и без регрессий честности**: все топ-5 приоритетов прошлого аудита закрыты правильно, с тестами и без подмены семантики (fail-closed везде сохранён; ни один фикс не «улучшил» статус молча). Новые находки исходного прохода — одна содержательная (HDX-AG-01) и четыре гигиенические. После §5 закрыты HDX-AG-01/02/03, HDX-LINT-01 (счётчик слепой зоны), HD2-UP-01, HD3-BFF-01. Открытыми остаются HD2-RL-02 (by-design) и хвост HDX-VERIF-01 (Redis-job-стор, untracked CLI). Checkpoint **NO_GO**.

## 5. Remediations (same day, Checkpoint still NO_GO)

| ID | Статус | Что сделано |
|---|---|---|
| HDX-AG-01 | **FIXED** | schema `1.1.0`: `outcome_scope=full_package`, `findings_scope=ifc_ids`, `blocking_outside_projection_count` + compact `outside_projection_blocking` |
| HDX-AG-02 | **FIXED** | `domain/advisory_origin.py` → `is_advisory_issue`; `run_manifest` и Acceptance Gate делят одну функцию |
| HDX-AG-03 | **FIXED** | blocking = `Severity.ERROR` only; ветка `critical` удалена |
| HDX-LINT-01 | **FIXED** (honest, not unblinded) | directory excludes сохранены (иначе CI затопит цитатами); `excluded_by_fragment` печатается в выводе линта |
| HD2-UP-01 | **FIXED** (recheck) | reserve-ahead уже был; pin порядка reserve → write |
| HD3-BFF-01 | **FIXED** (recheck) | lab session fail-closed + Bearer не читает cookie |
| HD2-RL-02 | **BY-DESIGN** | без изменения |
| HDX-VERIF-01 | **PARTIAL** | RU-маркеры в lint_claims покрыты тестом; Redis-job-стор и untracked CLI не в этом диффе |
