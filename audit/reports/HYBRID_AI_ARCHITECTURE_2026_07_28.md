---
title: "AeroBIM Hybrid AI — Architecture & Problem Register (2026-07-28)"
status: active
version: "1.0.0"
last_updated: "2026-07-28"
claim_boundary: "Foundation scaffold design. No product claims. Checkpoint NO_GO until RT-001/002/003."
tags: [aerobim, hybrid-ai, routing, privacy, architecture]
---

# AeroBIM Hybrid AI — архитектура и реестр проблем

> Hybrid AI здесь = **проверяемая система решений о маршруте данных**, а не «локальная
> + облачная модель». Итоговый инженерный вердикт остаётся за детерминированным
> движком (ADR-001). Этот документ — реестр (что есть/чего нет, с уровнем
> доказательности) + целевая архитектура. Companion-доки: routing policy, threat
> model, research review (в этой же папке).

## 1. Краткий вывод

Значимая часть P0-безопасности Hybrid AI **уже существует и покрыта тестами**
(tenant-ACL 404, fail-closed изоляция кэша, prompt-injection, OFF==ON, лимиты,
SSRF, schema-guard). **Отсутствует ядро маршрутизации**: классификация данных,
policy/route engine, типизированный hybrid AuditEvent, privacy guard/маскирование,
раздельные статусы маршрута. Их внедряю поэтапно как **domain-pure, fail-closed
scaffold**, не влияющий на вердикт. **Checkpoint остаётся NO_GO** — Hybrid AI не
закрывает RT-001/002/003.

## 2. Реестр: что уже есть (с уровнем доказательности)

| Возможность (P0-релевантная) | Где | Уровень |
|---|---|---|
| Владение вердиктом только движком | `domain/package_outcome.summary_passed_from_outcome`, ADR-001 | подтверждено кодом + unit-тестом |
| Advisory OFF==ON | `test_advisory_vlm_off_equals_on.py` | подтверждено unit-тестом |
| Tenant object-ACL → 404 (не 403) | `presentation/http/context.assert_*_access`, `test_api_object_acl.py` | код + тест |
| Fail-closed изоляция VLM-кэша (tenant+project) | `di/bootstrap._safe_cache_namespace`, `caching_vlm_reader`, `test_advisory_cache_tenant_isolation.py` | код + тест |
| Prompt-injection: капы/containment/observability | `domain/vlm_grounding` (`control_fields_ignored`), `test_vlm_region_schema.py` | код + тест |
| Строгая schema-валидация ответа (constrained-decoding) | `domain/vlm_response_schema.validate_observations_response`, `test_vlm_response_schema.py` | код + тест |
| SSRF outbound guard (DNS-pin, no-redirect) | `core/security/outbound_url`, `test_rt_remediation_post.py` | код + тест |
| Не логировать секреты | hyperdeep-аудит `RED_TEAM_HYPERDEEP_2026_07_28.md` | подтверждено кодом (аудит) |
| Лимиты размера/памяти (zip/XML-bomb, byte-cap) | uploads + `test_security_bomb_guards.py` | код + тест |
| Finding provenance (finding_id/evidence_refs) | `domain/models`, persist-reject | код + тест |
| Advisory-кэш act-grade replay (реплей ≠ детерминизм модели) | `domain/vlm_cache` | код + тест |

## 3. Реестр: чего НЕТ (целевые слои Hybrid AI)

| Слой | Статус | Уровень |
|---|---|---|
| Data Classification Layer (5 уровней) | отсутствует | запланировано → Wave 2 |
| Trust Policy / Model Router (class×route, fail-closed) | отсутствует | запланировано → Wave 2 |
| Раздельные статусы маршрута (LOCAL/PRIVATE/PUBLIC_MASKED/BLOCKED/HUMAN_REVIEW) | отсутствует | запланировано → Wave 2 |
| Privacy Guard (маскирование/токенизация/re-id-контроль) | отсутствует | запланировано → P1 |
| Типизированный HybridAuditEvent (полный путь, без секретов) | частично (review-events/provenance) | частично реализовано → Wave 3 |
| Local/Private VLM adapters, model-snapshot registry | частично (kimi advisory client) | частично / запланировано → P2 |
| TEE/FHE/MPC/ZK-routing/A2A/MCP/GraphRAG | отсутствует | запланировано → P3 (не начинать до P0) |

## 4. Целевая архитектура (12 слоёв)

```
API-клиент → Local API Gateway → Identity → Tenant/Project ACL → Data Classification
→ Task-type check → Trust Policy Engine → Local Guardrail → Route decision
→ Minimal-context extraction → Privacy Guard (mask/tokenize) → {Local | Private | Public} adapter
→ Response Verification (schema/type/size/unicode/NaN/forbidden-fields/provenance/tenant/project)
→ Evidence match → Deterministic IFC/IDS/norm verdict → HITL → Report + Audit/Replay
```

Слои как отдельные концепты: (1) Data Classification, (2) Trust Policy, (3) Privacy
Guard, (4) Model Router, (5) Local Inference, (6) Private Cloud, (7) Public Cloud,
(8) Response Verification, (9) Provenance, (10) Audit & Replay, (11) Deterministic
Verdict, (12) Human Review. **Только (11) владеет `summary.passed`.**

## 5. Матрица классификации (кратко; SSOT кода — Wave 2)

- **PUBLIC** — открытые fixture/стандарты/обезличенные демо.
- **INTERNAL** — внутренние некритичные документы.
- **CONFIDENTIAL** — IFC проекта, чертежи, расчёты, спецификации, внутренние нормы,
  состав систем, BCF с реальными замечаниями.
- **RESTRICTED** — данные «Самолёта», NDA, закрытые нормопаки, customer corpus, ПДн,
  необезличенные отчёты, исходные IFC/чертежи при запрете проектной политикой.
- **SECRET** — секреты/ключи/токены/пароли/конфиг безопасности/внутренние маршруты.

Классификация применяется к каждому объекту (IFC/PDF/лист/область/OCR/свойство/
нормопак/фрагмент расчёта/ответ модели/кэш/provenance/BCF/audit). **Модель не может
понижать класс.** Детали правил маршрута — в `HYBRID_AI_ROUTING_POLICY_2026_07_28.md`.

## 6. Kimi K3 в контуре

K3 — **один из внешних профилей**, не основа архитектуры. Жёсткие правила: публичный
API только для PUBLIC; customer/NDA/исходные IFC/чертежи/полный лист/комплект —
запрещены; итоговый вердикт запрещён; server-tools/встроенный поиск отключены;
`reasoning_content` не публиковать; ответ — строгой схемой; schema deviation →
деградация; кэш tenant-scoped; внешний вызов → audit; результат advisory-only.
(Детально — `docs/architecture/KIMI_K3_INTEGRATION_STUDY_2026_07_27.md`.)

## 7. Вердикт и гибридный контур (инвариант)

Hybrid AI **не влияет на вердикт напрямую**. Проверяемые свойства (интеграционные
тесты — по мере внедрения маршрутов): VLM OFF==ON (есть); public==local для вердикта;
cache replay==live для вердикта; mask/route/timeout/schema/policy-denial/нет-модели →
**никогда не PASS**; ответ модели не меняет severity/capabilities/engine_issues.

## 8. Связь с «Самолёт»/Техлаб/МИК и RT-001/002/003

Hybrid AI **не закрывает** RT-001 (adjudicated-корпус), RT-002 (нормопак), RT-003
(федеративный MEP). В акт МИК попадает только измеренное/воспроизводимое/привязанное
к корпусу/adjudicated/с provenance/не расширяющее claim. **Checkpoint = NO_GO.**

## 9. План разработки (P0→P3)

- **P0 (Wave 2–3):** классификация; policy engine fail-closed; tenant-scoped route;
  запрет public для CONFIDENTIAL/RESTRICTED/SECRET; (уже есть: object-ACL, изоляция
  кэша, защита секретов, неподменяемый audit — усилить типом; OFF==ON; запрет модели
  менять route/policy; prompt-injection; лимиты).
- **P1:** Privacy Guard + маскирование/токенизация + локальная restore-таблица +
  версионирование policy/mask + полный hybrid provenance + статусы маршрута + интеграционные тесты.
- **P2:** model router + local/private VLM adapters + Kimi profile + сравнительный harness + cost/latency + snapshot registry + replay bundle + claims-матрица.
- **P3 (не начинать до P0 с отрицательными тестами):** TEE/FHE/MPC/ZK/A2A/MCP/GraphRAG/auto-model-select.

## 10. Жёсткий вывод

- **Главная уязвимость (потенциальная, будущая):** появление маршрутизатора, который
  сможет отправить CONFIDENTIAL/RESTRICTED в публичный API — поэтому policy engine
  строится **fail-closed** ПЕРЕД любыми адаптерами.
- **Главный архитектурный риск:** «модель выбирает себе инструменты/маршрут» — запрещено
  по построению (router не читает секреты, не меняет policy/verdict/ACL).
- **Главный риск публичного Hybrid AI:** маскирование сохраняет тайну через структуру/
  геометрию/редкие значения — маска **не** доказывает анонимность.
- **Главный риск Kimi K3:** отправка customer/исходных данных в публичный API — запрещено; K3 только PUBLIC/обезличенное.
- **Главный внешний блокер:** RT-001/002/003 (данные заказчика) — кодом не закрываются.
- **Задача на сутки:** внедрить Data Classification + fail-closed policy engine (domain-pure) + отрицательные тесты (Wave 2).
- **Задача до 4 августа:** Privacy Guard + статусы маршрута + hybrid provenance + интеграционные тесты (P1).
- **Что нельзя начинать:** P3 (TEE/FHE/MPC/ZK/агенты) до подтверждённого P0 отрицательными тестами.
- **Можно ли выпускать:** нет — Checkpoint **NO_GO**; контур — foundation scaffold, не поставляемый продукт.
- **Для NO_GO→GO:** внешние артефакты RT-001/002/003 + их adjudication/provenance; кодом не достигается.
