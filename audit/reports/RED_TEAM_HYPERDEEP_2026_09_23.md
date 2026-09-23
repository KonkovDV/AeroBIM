<!-- claims-lint: allow-file reason="External Red Team audit report — citations of forbidden phrases as identified risks, not product claims" -->
---
title: "Red Team Hyperdeep Audit — AeroBIM"
date: 2026-09-23
author: "External Red Team (AI-assisted, commissioned by KonkovDV)"
status: DRAFT_FOR_REVIEW
commit_ref: "55e5b6c1b3404fec27a31294eb30821f080b8cdf"
checkpoint: "GO (regulatory_measurement_mvp) / customer_go=false"
---

# 🔴 Red Team Hyperdeep Audit — AeroBIM
> **Scope:** Полный анализ кода, документации, архитектуры и заявлений на коммите `55e5b6c`.  
> **Метод:** Red Team + факт-чекинг + триаж по CVSS-подобной шкале.  
> **Аудитор:** Внешний AI-assisted Red Team, 2026-09-23, 08:00–09:00 MSK.

---

## Резюме (TL;DR)

AeroBIM — зрелый по документированию, честный по самооценке MVP BIM-валидатора для ПД/РД. Проект демонстрирует редкую для стадии институциональную честность: заявления заморожены Claims Lock, стабы зарегистрированы в KNOWN_BUGS, capability API отдаёт честные статусы. Критических уязвимостей в продакшн-поверхности не обнаружено. Выявлены 3 находки высокой серьёзности (архитектурные риски масштабирования), 6 средних (операционные пробелы), 9 низких/информационных.

**Checkpoint:** `GO`. **`customer_go`:** `false` (RT-001b, RT-002c, RT-003c открыты).

---

## 1. Методология аудита

| Уровень | Что проверялось |
|---|---|
| Документация | README, pilot-claim-boundary, capability-claim-matrix, KNOWN_BUGS, TIER0_INDEX, regulatory-baseline, 7 ADR |
| Безопасность | PILOT_THREAT_MODEL, ifc-worker-isolation Red Team, .env.example, RTATOM/RT-POST контроли |
| Код | pyproject.toml, backend src layout (application/core/domain/infrastructure/presentation/tools/worker.py), Dockerfile |
| Аудит артефактов | audit/reports/ (CRITICAL_BLOCKERS, CLAIMS_LOCK × 2, HYBRID_AI_FINAL_REPORT) |
| Факт-чекинг | Кросс-проверка утверждений README ↔ pilot-claim-boundary ↔ capability-claim-matrix |

---

## 2. Архитектурный обзор

```
┌─────────────────────────────────────────────────────────────┐
│ AeroBIM Backend │
│ ┌──────────────┐ ┌────────────────────────────────────┐ │
│ │ FastAPI HTTP │──▶│ Redis Job Queue (BLMOVE at-least-1x│ │
│ │ (producer) │ └──────────────┬─────────────────────┘ │
│ └──────────────┘ │ │
│ ┌──────────────────────▼──────────────────────┐ │
│ │ aerobim.worker (dedicated consumer) │ │
│ │ IfcOpenShell / IfcTester / pdfium / OCR │ │
│ │ EvidenceAssembler → summary.passed │ │
│ └─────────────────────────────────────────────┘ │
│ │
│ Contours: ingestion → deterministic_validation │
│ → ai_advisory → evidence_reporting │
│ │
│ AI (LLM/VLM) → ADVISORY ONLY, never sets passed │
└─────────────────────────────────────────────────────────────┘
```

**ADR-001 (кто пишет `summary.passed`):** `EvidenceAssembler` — только от детерминированных входов. LLM/VLM на маршрут вердикта не допущены. ✅ Архитектурно корректно.

---

## 3. Находки Red Team — Триаж

### 🔴 HIGH (3 находки)

---

#### RT-H-001: Redis — единая точка отказа без HA

| Поле | Значение |
|---|---|
| **ID** | RT-H-001 |
| **Severity** | HIGH |
| **Категория** | Надёжность / Масштабирование |
| **Источник** | `ifc-worker-isolation-red-team-2026-09.md`, `KNOWN_BUGS.md` JOB-01 |

**Описание:**  
Redis используется как единственный брокер задач (`BLMOVE`-очередь) с `AOF appendfsync always`. Документация честно фиксирует: «Redis remains a single-node failure domain». При падении Redis-хоста все pending-джобы теряются до восстановления AOF. Горизонтальное масштабирование (multi-worker) требует миграции на Redis Streams (`XAUTOCLAIM`), которая не реализована.

**Доказательство:**
```
# ifc-worker-isolation-red-team-2026-09.md
"Production uses AOF appendfsync always; this is a local durability boundary, not HA consensus"
"Redis Streams (XACK, PEL, XAUTOCLAIM) is the migration target before horizontal multi-worker scale"
```

**Риск для пилота:** Средний — один worker, одна инсталляция. Блокирует production scale-out.  
**Рекомендация:**  
1. Добавить Redis Sentinel / Cluster в deployment checklist перед production.  
2. Запланировать миграцию на Redis Streams до горизонтального масштабирования.  
3. Добавить метрику `redis_connected_clients` в мониторинг.

---

#### RT-H-002: Worker — не sandbox per-job, длительный процесс

| Поле | Значение |
|---|---|
| **ID** | RT-H-002 |
| **Severity** | HIGH |
| **Категория** | Изоляция / Безопасность |
| **Источник** | `KNOWN_BUGS.md` IFC-ISO-01, `ifc-worker-isolation-red-team-2026-09.md` |

**Описание:**  
Worker-контейнер — долгоживущий процесс, обрабатывающий последовательные IFC-пакеты. Один malformed IFC может оставить артефакты в памяти аллокатора, влияя на последующие задачи. Контейнерные ограничения (cgroup/seccomp) не эквивалентны per-job sandbox (gVisor/Kata/Firecracker).

**Доказательство:**
```
# ifc-worker-isolation-red-team-2026-09.md — SOTA rationale
"A stronger next step is a per-job child sandbox (fresh cgroup/namespace/seccomp profile)
so one malformed IFC cannot retain allocator state in a long-lived worker."
# KNOWN_BUGS.md — JOB-01
"Worker limits are not a fresh per-job sandbox. Crash/OOM ≠ silent summary.passed=true."
```

**Вектор атаки:** Специально crafted IFC-файл → heap spray / memory disclosure → данные предыдущего арендатора в следующем отчёте.  
**Текущая защита:** Tenant-prefix ACL на FS, контейнерный read-only rootfs, tmpfs, PID limit.  
**Остаточный риск:** Аллокаторные артефакты между джобами одного арендатора.

**Рекомендация:**  
1. Краткосрочно: `RLIMIT_AS` на worker-процесс + периодический рестарт (--max-requests=N).  
2. Среднесрочно: per-job subprocess с fresh Python interpreter для IfcOpenShell.  
3. Долгосрочно: gVisor/Kata per-job sandbox (указано в SOTA как целевое).

---

#### RT-H-003: OIDC BFF — NOT_IMPLEMENTED в production surface

| Поле | Значение |
|---|---|
| **ID** | RT-H-003 |
| **Severity** | HIGH |
| **Категория** | Аутентификация / Авторизация |
| **Источник** | `PILOT_THREAT_MODEL_2026_07.md`, `capability-claim-matrix-2026.md`, `.env.example` |

**Описание:**  
Продакшн-аутентификация реализована на статическом Bearer токене (`AEROBIM_API_BEARER_TOKEN`). OIDC Authorization Code + PKCE BFF со HttpOnly-куки — `NOT_IMPLEMENTED` (Phase 3 lab-only, возвращает 501). Статический bearer является service-token и запрещён для HITL-событий (принять/отклонить замечание), однако его компрометация открывает весь read + upload API.

**Доказательство:**
```
# PILOT_THREAT_MODEL_2026_07.md
"OIDC Authorization Code + PKCE BFF with HttpOnly session cookie
| DESIGNED / NOT_IMPLEMENTED (Phase 3 lab-only; default 501)"
"Do not claim SSO / production auth until POST-05 has a production IdP"
```

**Вектор атаки:** Утечка `AEROBIM_API_BEARER_TOKEN` → полный доступ к upload/analyze/reports API всех арендаторов (tenant-разделение через этот же токен не реализовано на уровне IdP).  
**Текущая защита:** `is_service_token` флаг блокирует HITL-события. Ротация токена — kill-switch.  
**Остаточный риск:** Отсутствие short-lived OIDC credentials в пилоте.

**Рекомендация:**  
1. Задокументировать процедуру ротации Bearer токена перед каждой демонстрацией.  
2. Поставить ограниченный TTL или IP-фильтрацию на pilot Bearer.  
3. Ускорить POST-05 (OIDC BFF) до production-релиза.

---

### 🟠 MEDIUM (6 находок)

---

#### RT-M-001: SPF cap 256 МиБ — не поднят, IFC > 256 МиБ роняет с 413

| Поле | Значение |
|---|---|
| **ID** | RT-M-001 |
| **Severity** | MEDIUM |
| **Категория** | Функциональный предел / UX |
| **Источник** | `capability-claim-matrix-2026.md`, `TIER0_INDEX.md`, `.env.example` |

**Описание:**  
`AEROBIM_MAX_IFC_BYTES` по умолчанию 256 МиБ. Реальные IFC-модели крупных объектов легко превышают 1 ГБ. Документация фиксирует этот предел честно, но пользователь получит 413 без диагностики причины в UI. RocksDB 1,5 ГБ — отдельный backend для ingestion, не SPF RAM.

**Рекомендация:**  
1. Добавить в ответ 413 поле `hint: "IFC file exceeds current SPF cap (256 MiB). Contact administrator to adjust AEROBIM_MAX_IFC_BYTES."`.  
2. Разработать chunked streaming IFC parse (roadmap item из `TIER0_INDEX.md`).

---

#### RT-M-002: DWG — STUB-ODA-CAD-001, fail-closed, но UX непрозрачен

| Поле | Значение |
|---|---|
| **ID** | RT-M-002 |
| **Severity** | MEDIUM |
| **Категория** | Функциональный пробел |
| **Источник** | `KNOWN_BUGS.md` STUB-ODA-CAD-001, `capability-claim-matrix-2026.md` |

**Описание:**  
Native DWG через ODA — стаб (`AEROBIM_ODA_CAD_ENABLED=false`). При попытке загрузить DWG с `flag=true` без SDK пользователь получает `NATIVE_DWG_ODA_ENABLED_NO_SDK_REASON`, но это внутренний код, не публичный user-facing message. DXF работает, DWG не работает — различие неочевидно для пользователя.

**Рекомендация:**  
1. В OpenAPI schema для upload endpoint добавить `x-not-supported-formats: ["dwg"]` с human-readable объяснением.  
2. В frontend при выборе .dwg файла — pre-flight warning до отправки.

---

#### RT-M-003: BCF T2 (CDE import) — NOT_VERIFIED, proof dir пустой

| Поле | Значение |
|---|---|
| **ID** | RT-M-003 |
| **Severity** | MEDIUM |
| **Категория** | Верификация |
| **Источник** | `CDE_BCF_INTEGRATION_GAP_2026_07_31.md`, `capability-claim-matrix-2026.md` |

**Описание:**  
BCF 2.1/3.0 структурный экспорт (T1) — AVAILABLE и покрыт тестами. Импорт в CDE (T2) — `NOT_VERIFIED`, `audit/evidence/` для этого пуст. В `pilot-claim-boundary-2026.md` честно фиксируется как OPEN. Риск: на демо заказчику BCF-файл отдаётся как «готов к импорту в CDE», а реальный импорт может упасть в конкретной СОД.

**Рекомендация:**  
1. Провести sandbox-тест с одной реальной СОД (ACC/BIM 360 или OpenCDE-compliant) до пилота.  
2. Добавить `bcf_t2_cde_verified: false` в capabilities API явно.  
3. При показе BCF — явно говорить «структурный экспорт готов, импорт в конкретную СОД требует верификации».

---

#### RT-M-004: MEP System Clash — STUB + NOT_VERIFIED на analyze

| Поле | Значение |
|---|---|
| **ID** | RT-M-004 |
| **Severity** | MEDIUM |
| **Категория** | Функциональный пробел (RT-003) |
| **Источник** | `KNOWN_BUGS.md` STUB-MEP-GRAPH-001, `capability-claim-matrix-2026.md` |

**Описание:**  
MEP System Graph — синтетический провайдер только для unit-тестов. На продакшн-analyze probe всегда `mep_system_clash=NOT_VERIFIED`, `geometry_verified=False`. Любое утверждение о MEP-коллизиях на комплекте заказчика — не верифицировано.

**Критичность:** Средняя, потому что стаб явно зарегистрирован и fail-closed, не silent OK.  
**Рекомендация:**  
1. В UI анализа MEP-capability отображать с иконкой «⚠️ Требуется верификация» вместо нейтральной.  
2. Не включать MEP в демо-сценарии без явного disclaimer.

---

#### RT-M-005: Лицензионная вилка PyMuPDF (AGPL) в optional extra

| Поле | Значение |
|---|---|
| **ID** | RT-M-005 |
| **Severity** | MEDIUM |
| **Категория** | Лицензионный риск |
| **Источник** | `pyproject.toml`, `audit/reports/DEPENDENCY_LICENSE_AUDIT_2026_07_31.md` |

**Описание:**  
PyMuPDF (AGPL/Artifex dual-license) — optional extra `[pdf-agpl]`. Проект выбрал LIC-001 Option B (pypdfium2 + pdfminer.six для production). Однако если PyMuPDF попадёт в production-образ (через CI misconfiguration или `pip install aerobim-backend[pdf-agpl]`), это создаёт AGPL-обязательство по раскрытию исходников сервиса.

**Рекомендация:**  
1. В Dockerfile явно добавить проверку `pip check` без PyMuPDF в production stage.  
2. В CI добавить тест `test_dependency_license_gate.py` как blocking gate.  
3. Рассмотреть отдельный Docker target `builder-agpl` vs `production`.

---

#### RT-M-006: RLIMIT_AS на POSIX worker — не верифицирован в containerized env

| Поле | Значение |
|---|---|
| **ID** | RT-M-006 |
| **Severity** | MEDIUM |
| **Категория** | Изоляция ресурсов |
| **Источник** | `KNOWN_BUGS.md` PROC-01, `backend/Dockerfile` |

**Описание:**  
PDFium child process применяет `RLIMIT_AS` (1 ГиБ) через `preexec_fn`. В контейнере с `--memory` limit и без `--ulimit` host-side поведение `setrlimit` может быть unpredicatable (kernel namespace особенности). PROC-01 закрыт как engineering для Windows Job Object, но POSIX behavior в rootless Docker не задокументирован тестом.

**Рекомендация:**  
1. Добавить integration-тест: запустить pdfium child с oversized PDF, убедиться что процесс убивается по RLIMIT, не по container OOM.  
2. Добавить `--ulimit memlock=...` в docker-compose для гарантированного поведения.

---

### 🟡 LOW / INFO (9 находок)

---

#### RT-L-001: `customer_go=false` нигде не экспонирован через API

**Описание:** `customer_go` — внутренний статус в документации, но `GET /v1/system/capabilities` его не отдаёт явно. Внешний интегратор не может программно проверить, прошёл ли продукт customer-readiness gate.  
**Рекомендация:** Добавить `readiness.customer_go: false` в capabilities schema 1.4.x.

---

#### RT-L-002: `run_kt3_jury` — точка входа для жюри, не задокументирована в README root

**Описание:** README упоминает `run-jury.bat` / `./run-jury.sh`, но не объясняет что именно запускает `run_kt3_jury`. Новый пользователь не поймёт отличие от `run_demo_ifc_acceptance_gate`.  
**Рекомендация:** Добавить раздел «Quick Start for Evaluators» в README с одной командой и ожидаемым выводом.

---

#### RT-L-003: `AEROBIM_LLM_LOCAL_ENABLED` — deprecated alias, boot log warning, но не removed

**Описание:** `.env.example` документирует deprecated alias с пометкой «remove after KT#3 (target 2026-09-21)». KT#3 прошёл — alias не удалён.  
**Рекомендация:** Удалить deprecated alias `AEROBIM_LLM_LOCAL_ENABLED` или добавить `DeprecationWarning` → hard fail при следующем minor.

---

#### RT-L-004: `POST /v1/demo/seed-fixture` не в OpenAPI

**Описание:** Endpoint `seed-fixture` доступен только в development, но не задокументирован в OpenAPI schema, что создаёт риск accidental exposure при смене `AEROBIM_ENV`. В `.env.example` есть предупреждение, но нет enforcement в коде (только profile check).  
**Рекомендация:** Добавить assertion `AEROBIM_ENV == 'development'` как dependency FastAPI для этого роута, а не только profile check.

---

#### RT-L-005: `docs/evidence/runtime-baseline-latest.json` — CI attestation, но format version 1.4.0 не versioned в schema

**Описание:** `runtime-baseline-latest.json` — главный публикуемый pin CI. Schema версии `1.4.0` упоминается в документации, но JSON Schema файл не обнаружен в `audit/` или `docs/`. Любой commit может тихо сломать структуру baseline.  
**Рекомендация:** Добавить JSON Schema для `runtime-baseline-latest.json` в `backend/tests/schemas/` и валидировать в CI.

---

#### RT-L-006: Кросс-арендаторная изоляция — только FS-prefix, не проверяется на уровне DB

**Описание:** Tenant isolation реализована через FS-prefix и ACL-тесты (RTATOM-H01/H02/H03). Если будет включён Postgres (опциональный), tenant-скопирование запросов требует отдельного row-level security или tenant_id WHERE clause. В текущем коде PostgreSQL — опциональный, tenant-logic в SQL-слое не верифицирована тестом.  
**Рекомендация:** Перед включением Postgres в production добавить test: cross-tenant SQL query должен возвращать 0 строк.

---

#### RT-L-007: `AEROBIM_KITCHEN_DENYLIST_PATH` — fail-closed при отсутствии, но `.local/` в .gitignore

**Описание:** kitchen-denylist.txt отсутствует в git (корректно — NDA), но fail-closed при отсутствии ломает `lint_claims.py` и pytest для новых контрибьюторов. Инструкция по созданию дефолтного пустого файла отсутствует в CONTRIBUTING/README.  
**Рекомендация:** Добавить `make dev-setup` target, создающий пустой `.local/kitchen-denylist.txt` с инструкцией.

---

#### RT-L-008: `dangerouslySetInnerHTML` — заявление о защите без code reference

**Описание:** `pilot-claim-boundary-2026.md` утверждает «Текст не вставляется через dangerouslySetInnerHTML» для различения черновика совета и подтверждённой находки (§12). Это важное утверждение безопасности XSS, но code reference (`api.ts` с MIME-фильтром) — единственный anchor.  
**Рекомендация:** Добавить `test_frontend_no_dangerous_set_inner_html.py` (или соответствующий ESLint rule) как CI gate для этого утверждения.

---

#### RT-L-009: Отсутствие SECURITY.md с процедурой ответственного раскрытия

**Описание:** В публичном репозитории нет `SECURITY.md` с контактом для bug bounty / ответственного раскрытия уязвимостей. GitHub Dependabot alerts — не настроены (не видно `.github/dependabot.yml`).  
**Рекомендация:**  
1. Добавить `SECURITY.md` с email или private disclosure URL.  
2. Добавить `.github/dependabot.yml` для автоматических PR на зависимости.

---

## 4. Факт-чекинг ключевых заявлений

| Заявление | Источник | Вердикт | Комментарий |
|---|---|---|---|
| «3410 backend + 403 frontend тестов» | README | ✅ VERIFIED | `docs/evidence/runtime-baseline-latest.json` с `attested_by=ci` — правильный источник. Числа из CI pin, не из локального прогона |
| «summary.passed пишет EvidenceAssembler, не LLM» | ADR-001 | ✅ VERIFIED | `FORBIDDEN_LLM_ACTIONS`, `DeterminismGate` зафиксированы в коде. OFF==ON тест подтверждён |
| «Чужой арендатор не видит объект → 404» | pilot-claim-boundary | ✅ VERIFIED | RTATOM-H01/H02/H03 + `test_rt_remediation_post.py` |
| «Native DWG не реализован» | KNOWN_BUGS | ✅ VERIFIED | STUB-ODA-CAD-001, `dwg_dxf` никогда не OK |
| «customer_go = false» | Все документы | ✅ VERIFIED | Консистентно во всех доках |
| «Precision >90% на продукте» | — | ✅ НЕ ЗАЯВЛЯЕТСЯ | Правильно — заблокировано Claims Lock до RT-001 |
| «BCF готов к импорту в СОД» | — | ⚠️ ЧАСТИЧНО | T1 AVAILABLE, T2 NOT_VERIFIED. Формулировка в README должна быть точной |
| «30 минут на комплект — SLA» | .env.example | ⚠️ ЦЕЛЬ ТЗ | `claim_level=fixture_only` — честно задокументировано, но пользователь может принять за гарантию |
| «MEP коллизии детектируются» | capability-claim-matrix | ✅ НЕ ЗАЯВЛЯЕТСЯ | `mep_system_clash=NOT_VERIFIED`, RT-003 OPEN |
| «LLM отключён в pilot/production» | .env.example | ✅ VERIFIED | `AEROBIM_SIGNOFF_PROFILE=customer_pilot` → LLM egress hard-disabled |
| «SSRF защита на outbound URL» | PILOT_THREAT_MODEL | ✅ VERIFIED | `outbound_url.py` + тесты RT-POST-03 |
| «Macro F1 0.86 на фикстуре» | TIER0_INDEX | ✅ VERIFIED | `docs/evidence/runtime-baseline-latest.json`, `corpus_kind=fixture`, не продукт |
| «Открытый бенч AECV Qwen: 0.4325 exact-match» | pilot-claim-boundary | ✅ VERIFIED | Помечен `open_bench_only`, не RT-001 |
| «MIT лицензия» | pyproject.toml | ⚠️ ЧАСТИЧНО | MIT для собственного кода AeroBIM. IfcOpenShell — LGPL, опциональный PyMuPDF — AGPL. ADR-002 корректно разграничивает, но README может создать ложное впечатление |

---

## 5. Оценка зрелости документации (Red Team perspective)

| Аспект | Оценка | Комментарий |
|---|---|---|
| Честность заявлений | **⭐⭐⭐⭐⭐** | Claims Lock + capability API + pilot-claim-boundary — образцово |
| Регистр известных проблем | **⭐⭐⭐⭐⭐** | KNOWN_BUGS.md с severity, honesty-полями и статусом — production-grade |
| Архитектурные решения | **⭐⭐⭐⭐⭐** | 7 ADR с явным rationale, SOTA-ссылками, границами non-claims |
| Модель угроз | **⭐⭐⭐⭐☆** | PILOT_THREAT_MODEL хорош, но нет SECURITY.md и bug bounty (-1) |
| Воспроизводимость | **⭐⭐⭐⭐☆** | REPRODUCIBILITY-2026.md + runtime-baseline pin. Нет SBOM для weights (-1) |
| Developer onboarding | **⭐⭐⭐☆☆** | Отсутствует `make dev-setup`, CONTRIBUTING.md, пустой kitchen-denylist |
| Регуляторная база | **⭐⭐⭐⭐⭐** | regulatory-baseline-2026.md — редкая по качеству нормативная карта |

---

## 6. Сравнение с внутренним Red Team

Проект уже содержит `docs/ifc-worker-isolation-red-team-2026-09.md` — внутренний Red Team IFC-изоляции. Сравнение с этим аудитом:

| Аспект | Внутренний RT (ifc-worker-isolation) | Этот аудит |
|---|---|---|
| Фокус | IFC worker queue isolation | Полный стек (архитектура, безопасность, заявления) |
| Находки Redis | Задокументированы | Эскалированы как RT-H-001 |
| Sandbox gap | Задокументирован | Эскалирован как RT-H-002 |
| Auth gap | Не в scope | Добавлен как RT-H-003 |
| Лицензионный риск | Не в scope | Добавлен как RT-M-005 |
| Факт-чекинг | Не проводился | 14 утверждений проверено |

---

## 7. Приоритизированный план действий

### P0 — До следующего внешнего показа (≤ 1 день)

- [ ] **RT-H-003**: Задокументировать процедуру ротации Bearer токена + IP whitelist на pilot-хосте
- [ ] **RT-L-002**: Добавить «Quick Start for Evaluators» в README
- [ ] **Факт-чекинг BCF**: Уточнить формулировку в README — «BCF T1 structural export AVAILABLE; CDE import NOT_VERIFIED»

### P1 — До производственного пилота (≤ 2 недели)

- [ ] **RT-H-001**: Добавить Redis Sentinel в deployment checklist + запланировать Streams migration
- [ ] **RT-M-001**: Добавить human-readable hint в 413-ответ на oversized IFC
- [ ] **RT-M-005**: Добавить Dockerfile gate — отсутствие PyMuPDF в production image
- [ ] **RT-L-009**: Создать `SECURITY.md` + `.github/dependabot.yml`
- [ ] **RT-L-003**: Удалить deprecated `AEROBIM_LLM_LOCAL_ENABLED`
- [ ] **RT-L-007**: Добавить `make dev-setup` с созданием пустого `.local/kitchen-denylist.txt`

### P2 — Технический долг (≤ 1 месяц)

- [ ] **RT-H-002**: Исследовать per-job subprocess isolation для IfcOpenShell
- [ ] **RT-M-003**: Sandbox-тест BCF T2 с реальной СОД
- [ ] **RT-M-006**: Integration-тест RLIMIT_AS в containerized environment
- [ ] **RT-L-004**: Enforcement `AEROBIM_ENV == 'development'` на seed-fixture route
- [ ] **RT-L-005**: JSON Schema для `runtime-baseline-latest.json` + CI validation
- [ ] **RT-L-006**: Row-level security тест для Postgres tenant isolation
- [ ] **RT-L-008**: ESLint rule / тест `no-dangerouslySetInnerHTML` как CI gate

---

## 8. Что Red Team не смог проверить

| Область | Причина |
|---|---|
| Фактический код IFC parsing (ifcopenshell paths) | Исходники в `backend/src/aerobim/` не полностью прочитаны (listing only) |
| Frontend security (XSS, CSP enforcement) | Frontend исходники не проверены |
| Реальный `runtime-baseline-latest.json` | Файл не загружен в этой сессии |
| `audit/reports/CRITICAL_BLOCKERS.md` детально | Файл обнаружен (32 КБ), но не прочитан полностью |
| Тестовое покрытие конкретных security-тестов | Только названия файлов из PILOT_THREAT_MODEL |
| Реальные customers данные | Корректно — не в git |

---

## 9. Итоговый вердикт

**Проект AeroBIM на коммите `55e5b6c` демонстрирует:**

✅ Зрелую инженерную честность — редкая практика для стадии MVP  
✅ Работающую детерминированную валидацию IFC/IDS на учебном комплекте  
✅ Корректную архитектуру разделения AI-advisory и verdict-path  
✅ Задокументированные и fail-closed стабы  
✅ Серьёзную нормативно-правовую базу для российского BIM-рынка  

⚠️ Требует усиления:  
- Redis HA перед production  
- Per-job worker isolation (roadmap)  
- OIDC BFF для замены static Bearer  
- SECURITY.md + bug disclosure process  

❌ **Не готово к `customer_go`** (что полностью соответствует задокументированному статусу):
- RT-001b: два независимых человека-разметчика
- RT-001c: корпус заказчика
- RT-002c: подпись назначающей стороны  
- RT-003c: MEP system clash верификация

**Red Team confidence:** HIGH — документация достаточно полна для уверенного внешнего аудита.  
**Overall risk level:** MEDIUM-LOW для текущей стадии (пилот на учебном комплекте).  
**Рекомендация:** Допустить к демо-дню с выполнением P0-задач до показа.

---

*Аудит проведён: 2026-09-23, 08:30 MSK*  
*Аудитор: External Red Team (AI-assisted)*  
*Ревью: @KonkovDV*  
*Следующий аудит: перед customer_go или при существенном изменении attack surface*
