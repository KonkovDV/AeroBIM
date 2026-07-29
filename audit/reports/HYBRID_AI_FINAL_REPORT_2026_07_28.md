---
title: "AeroBIM Hybrid AI — Final Report (2026-07-28)"
status: active
version: "1.0.0"
last_updated: "2026-07-28"
claim_boundary: "P0/P1 foundation, domain-pure, verdict-neutral, not in the verdict path. No product claims. Checkpoint NO_GO."
tags: [aerobim, hybrid-ai, final-report, routing, privacy, audit]
---

# AeroBIM Hybrid AI — финальный отчёт

Итог по внедрению безопасного Hybrid AI-контура (бриф §1–§25). Companion-документы:
[`HYBRID_AI_ARCHITECTURE`](HYBRID_AI_ARCHITECTURE_2026_07_28.md) ·
[`HYBRID_AI_ROUTING_POLICY`](HYBRID_AI_ROUTING_POLICY_2026_07_28.md) ·
[`HYBRID_AI_THREAT_MODEL`](HYBRID_AI_THREAT_MODEL_2026_07_28.md) ·
[`HYBRID_AI_RESEARCH_REVIEW`](HYBRID_AI_RESEARCH_REVIEW_2026_07_28.md).

## 1. Краткий вывод
Построен **P0/P1 фундамент** проверяемой маршрутизации данных: классификация (5 уровней),
fail-closed policy-движок, типизированный secret-safe audit event, Privacy Guard и
композитный `HybridRouteGate`. Всё **domain/application-pure**, **не в пути вердикта**
(OFF==ON), fail-closed. Два независимых Red Team-прохода нашли и закрыли реальные
дефекты (fail-open утечка в аудите; cross-field leak и delimiter-collision в маскировании;
пробелы аудита в гейте). **Checkpoint = NO_GO**; RT-001/002/003 — внешние.

## 2. Как Hybrid AI понимается в AeroBIM
Не «локальная + облачная модель», а система решений о **маршруте данных**: identity →
tenant/project ACL → классификация → policy → guardrail → минимизация/маскирование →
{local|private|public} → верификация ответа → детерминированный вердикт → HITL → аудит.
Модель — источник **кандидатных наблюдений**, не инженерных заключений.

## 3. Что уже есть (подтверждено кодом+тестами)
Вердикт только движком (`summary_passed_from_outcome`, ADR-001); advisory OFF==ON;
object-ACL→404; fail-closed изоляция VLM-кэша; prompt-injection (grounding caps +
schema-guard + injection-observability); SSRF-guard; не-логирование секретов; лимиты
size/bomb; provenance находок. **Новое ядро (эта работа):** `domain/hybrid/*` +
`application/services/hybrid_route_gate.py`.

## 4. Что отсутствует / отложено
Privacy Guard **не подключён** к живому запросному пути (гейт доступен, но не
потребляется вердиктом — как `ADVISORY_VLM_PIPELINE`); нет image-маскирования (crop/DPI —
инфраструктура, P2); нет model-router/local-VLM/private-VLM адаптеров (P2); TEE/FHE/MPC/
ZK/агенты — **P3, не начато** (по §20).

## 5. Архитектура текущего контура
INGESTION → DETERMINISTIC_VALIDATION → AI_ADVISORY → EVIDENCE_REPORTING; вердикт
принадлежит DETERMINISTIC_VALIDATION. Advisory-контур (VLM) существует, но **не
потребляется** use-case вердикта.

## 6. Целевая архитектура Hybrid AI (12 слоёв)
Data Classification · Trust Policy · Privacy Guard · Model Router · Local/Private/Public
Inference · Response Verification · Provenance · Audit&Replay · Deterministic Verdict ·
Human Review. **Только Deterministic Verdict владеет `summary.passed`.** Реализовано P0/P1:
слои 1–3 + композитный гейт + audit; слои 4–7 (роутер/адаптеры) — P2.

## 7. Матрица классификации данных
`PUBLIC < INTERNAL < CONFIDENTIAL < RESTRICTED < SECRET` (`data_classification.py`).
Неизвестный вид → **CONFIDENTIAL** (не PUBLIC); агрегат — `most_restrictive` (никогда не
понижает). IFC/чертежи/расчёты → CONFIDENTIAL; customer/NDA/Самолёт/нормопак/ПДн →
RESTRICTED; ключи/токены → SECRET.

## 8. Матрица маршрутизации
`trust_policy.decide_route` (см. ROUTING_POLICY §1). PUBLIC-egress **BLOCKED** для
CONFIDENTIAL/RESTRICTED/SECRET; SECRET блокируется на всех целях; unknown-tenant →
BLOCKED; CONFIDENTIAL/RESTRICTED→PRIVATE только при `private_mode_confirmed`;
INTERNAL→PUBLIC → HUMAN_REVIEW без согласия владельца. BLOCKED/HUMAN_REVIEW → **нет
external_call**.

## 9. Модель угроз
См. THREAT_MODEL (T1–T10). Покрыто кодом+тестами: injection, cross-tenant, exfil,
verdict-подмена, bomb, secret-логи. Остаточно/P1: re-id после маскирования, egress-
контроль на живом пути.

## 10. Сравнение с мировыми практиками
Проверяемые стандарты: **NIST AI RMF**, **NIST GenAI Profile**, **OWASP LLM Top-10 2025**
(перенесены: Map=классификация, Manage=fail-closed policy, LLM01/02/07). Концепт-подходы
(ComplianceGate/PRISM/SplitAgent/…): первоисточники **верифицировать** перед цитированием
(RESEARCH_REVIEW §2).

## 11. Применимость исследований
Немедленно переносимо — classifier-gated fail-closed routing (ComplianceGate-класс) +
NIST/OWASP-контроли. НЕ переносить без доказательства: privacy-метрики на синтетике;
TEE/FHE/ZK (P3). Никакой подход не снимает RT-001/002/003.

## 12. Анализ Kimi K3
Один из внешних профилей, не основа. Публичный API — **только PUBLIC/обезличенное**;
customer/NDA/исходные IFC/чертежи/лист/комплект/вердикт — запрещены; server-tools/поиск
off; `reasoning_content` не публиковать; строгая схема; deviation→деградация; кэш
tenant-scoped; вызов→audit; результат advisory-only. Детали — `KIMI_K3_INTEGRATION_STUDY`.

## 13. Анализ локального VLM
`RegionRestrictedVlmPipeline` + region-crop + grounding + детерминированный нормализатор +
HITL. Для CONFIDENTIAL/RESTRICTED — только local/private; целый лист/комплект наружу — **нет**.

## 14. Анализ маскирования
`PrivacyGuard` (§8): per-tenant HMAC-токены (length-prefixed, детерминированы внутри
tenant, unlinkable между tenant), локальная tenant-scoped restore-таблица, fail-closed
поля (нелистованное → удаляется), пост-скан на остаточную утечку. **Маскирование снижает
раскрытие, но НЕ доказывает анонимность.** Image-маскирование — P2.

## 15. Анализ маршрутизатора
Model-router (провайдер-независимый, профили `deterministic_text`/`local_ocr`/`local_vlm`/
`private_vlm`/`public_kimi_k3`/`public_control_model`/`human_review`) — **P2** (спека в
ROUTING_POLICY §5). P0 покрывает eligibility (`decide_route`); выбор конкретной модели — P2.

## 16. Анализ кэша
Существующий VLM-кэш tenant/project fail-closed (act-grade key, golden-hash, TTL). Кэш
**не доказывает детерминизм модели** — только повторное воспроизведение сохранённого ответа.

## 17. Анализ tenant isolation
object-ACL→404 (report/IFC/BCF/jobs/preview) + fail-closed изоляция кэша + policy/guard
требуют проверенного tenant (blank→BLOCKED; per-tenant токены/restore). Отрицательные тесты
есть по ACL/кэшу; masked/audit — на уровне доменных тестов.

## 18. Анализ prompt injection
Output-as-data + строгая схема (fail-closed) + капы + игнор+**surfacing** control-полей
(grounding) + токенизация полей в маскировании. Adaptive attacks (Zhan NAACL 2025) →
layered defense + детект, не только блок.

## 19. Анализ итогового вердикта
Hybrid AI **не влияет** на `summary.passed`. Гейт возвращает routing-решение (без вердикта);
`verdict_impact` фиксирован `none` (`init=False`); OFF==ON доказан (`test_advisory_vlm_off_
equals_on`) + гейт не потребляется use-case вердикта (bootstrap-дифф аддитивный).

## 20. Связь с IFC/IDS/BCF/MEP/нормами
Hybrid AI помогает **извлекать/маршрутизировать** доказательства, но вердикт по IFC/IDS/
кросс-докам/clash/нормам — детерминированный. MEP системный clash — NOT_VERIFIED (RT-003);
нормопак — synthetic (RT-002); BCF — структурный, CDE-импорт не проверен.

## 21–23. «Самолёт» / Техлаб / МИК
Hybrid AI **не закрывает** RT-001 (adjudicated-корпус), RT-002 (нормопак), RT-003
(федеративный MEP). В акт МИК — только измеренное/воспроизводимое/adjudicated/с provenance/
не расширяющее claim. Данные заказчика — внешний вход.

## 24. План экспериментов
Спека (не выполнено — нет живой модели/данных заказчика): контрольные варианты 1–17
(local OCR … hybrid route … full-payload только на синтетике) × метрики (precision/recall/
F1, schema-deviation, injection-detection, abstention, HITL, latency, cost, egress-объём,
privacy-leakage, policy-violation, replay). Доверительные интервалы + paired + анализ
отказов; **не** объявлять победителя по одному среднему.

## 25. План разработки
P0 ✅ (классификация, policy, tenant-scoped route, public-block, ACL, кэш-изоляция,
secret-guard, audit-event, OFF==ON, no-model-route-override, injection, лимиты). P1 ✅
(Privacy Guard, маскирование/токенизация, restore-таблица, версии policy/mask, статусы
маршрута + композитный гейт) / ⏳ (живое подключение pre-gate). P2 ⏳ (адаптеры провайдеров/
локальное обнаружение сущностей ✅ `sensitive_entities.py`; маршрутизатор моделей ✅ `model_router.py`; provider-конфиг из Settings ✅; интеграционный стенд ✅; snapshot/replay-bundle ⏳). P3 (по §11): стенд на синтетике/обезличенном **без внешнего выхода** ✅ `bench_hybrid_contour` (метрики контура/restore/egress — не точность продукта); живой тестовый контур + данные заказчика — гейтированы. Крипто/агенты (TEE/FHE/MPC/ZK) — **не начаты**.

## 26. Изменённые/добавленные файлы
`domain/hybrid/{data_classification,trust_policy,audit_event,privacy_guard,sensitive_entities,model_router,__init__}.py`;
`application/services/hybrid_route_gate.py`; `tools/export_hybrid_route_matrix.py`; `tools/bench_hybrid_contour.py`; `core/di/tokens.py` (+HYBRID_ROUTE_GATE);
`infrastructure/di/bootstrap.py` (+регистрация HYBRID_ROUTE_GATE + HYBRID_MODEL_ROUTER); `core/config/settings.py` (+hybrid_provider_config_path); 4 companion-дока; README baseline.

## 27. Добавленные тесты (97 hybrid)
`test_hybrid_trust_policy.py` (13) · `test_hybrid_audit_event.py` (11) ·
`test_hybrid_privacy_guard.py` (16) · `test_hybrid_route_gate.py` (13) ·
`test_hybrid_sensitive_entities.py` (8) · `test_hybrid_model_router.py` (21) ·
`test_hybrid_route_matrix.py` (5) · `test_hybrid_integration_bench.py` (4) ·
`test_bench_hybrid_contour.py` (6) — fail-closed матрица,
never-downgrade, secret-safe audit, leak/re-id/обход маскирования, verdict-neutrality, DI-resolve.

## 28. Созданные артефакты
`audit/evidence/hybrid-routing-policy-tests-2026-07-28.json` (матрица+fail-closed+limitations) +
`audit/evidence/hybrid-route-matrix-2026-07-29.json` (полная матрица class×target×task; external только для PUBLIC; воспроизводимо) +
`audit/evidence/hybrid-contour-bench-2026-07-29.json` (метрики контура на синтетике `samples/benchmarks/hybrid-contour/`; restore-fidelity/egress/latency; без внешнего выхода).
Остальные из §22 (tenant-isolation/prompt-injection/masking/off-equals-on/replay/egress) —
**покрыты тестами**; отдельные JSON — по мере P1-wire на живом пути (честно: пока не materialized).

## 29. Выполненные проверки
ruff/mypy (226 файлов)/pytest 1366 passed, 8 skipped, 144 subtests; runtime-baseline drift OK;
markdown-links OK; **CI зелёный** на каждом шаге; 2 независимых Red Team-прохода (CodeReview).

## 30. Остаточные риски
- Классификация зависит от корректной разметки вида объекта (ошибка → неверный маршрут); дефолт консервативный.
- Маскирование ≠ анонимность (структура/геометрия/редкие значения).
- Гейт **не подключён** к живому egress — до подключения защита действует только там, где вызывается.
- Re-id/egress-контроль на живом пути — P1-wire (не завершено).
- Внешние RT-001/002/003 — не закрываются кодом.

## 31. Обновлённый статус checkpoint
**NO_GO** (без изменений). Hybrid AI-фундамент готов и закалён Red Team, но не является
поставляемым продуктом и не снимает внешних блокеров.

---

## Жёсткий вывод
- **Главная уязвимость:** появление потребителя гейта на живом пути без корректной классификации/маскирования — поэтому всё построено **fail-closed** до подключения.
- **Главный архитектурный риск:** «модель выбирает маршрут/инструмент» — запрещено по построению (гейт не читает секреты, не меняет policy/verdict/ACL).
- **Главный риск публичного Hybrid AI:** маскирование не доказывает анонимность.
- **Главный риск Kimi K3:** отправка customer/исходных данных в публичный API — запрещено (только PUBLIC/обезличенное).
- **Главный риск маскирования:** повторная идентификация; per-tenant токены детерминированы внутри tenant (нужно для движка) — это осознанный компромисс.
- **Главный внешний блокер:** RT-001/002/003 (данные заказчика).
- **Задача на сутки:** подключить `HybridRouteGate` как pre-gate к advisory-контуру (не к вердикту) + интеграционные тесты «сбой→не PASS».
- **Задача до 4 августа:** model-router + local/private VLM-адаптеры + egress-учёт (P2), сохранив OFF==ON.
- **Что нельзя начинать:** P3 (TEE/FHE/MPC/ZK/агенты) до подтверждённого P0 на живом пути.
- **Можно ли выпускать:** нет — **NO_GO**; контур — foundation scaffold.
- **Для NO_GO→GO:** внешние артефакты RT-001/002/003 + adjudication/provenance; кодом не достигается.
