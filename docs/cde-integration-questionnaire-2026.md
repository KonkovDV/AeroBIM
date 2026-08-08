<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
---
title: "CDE / СОД integration questionnaire — Samolet 10D"
status: active
version: "1.0.0"
date: "2026-07-31"
claim_boundary: "«Интеграция с 10D» запрещена до T5 (Claims Lock). Этот документ — интейк, не заявление."
---

# Опросник интеграции с СОД заказчика (10D / S.Project / иная CDE)

Лестница уровней (Claims Lock v3):

| Tier | Что доказано | Evidence |
|---|---|---|
| T0 | BCF ZIP структурно валиден | XSD + структурная проверка |
| T1 | BCF открывается ≥2 независимыми клиентами | dual-consumer artifact (есть: 2026-07-25) |
| T2 | BCF импортируется в тестовую среду заказчика | import-log + screenshot + hashes (**NOT_VERIFIED**) |
| T3 | Issue корректно связывается с IFC GUID / viewpoint | side-by-side проверка в CDE |
| T4 | Lifecycle туда-обратно (обновление существующего issue) | round-trip лог |
| T5 | Production integration approved by customer | подписанное подтверждение |

## Вопросы заказчику (Самолёт)

1. Целевая СОД: 10D СОД / S.Project / Pilot-BIM / иная? Версия?
2. Версия BCF (2.1 / 3.0)? Импорт через ZIP или BCF API (OpenCDE)? Версия API?
3. Пример реального issue (экспорт из вашей СОД) — эталон полей.
4. Sample IFC из вашего контура + правила стабильности IFC GUID между ревизиями.
5. Допустимые координатные системы / базовые точки для viewpoints.
6. Workflow-статусы issue, роли, assignee, priority, due date — словарь значений.
7. Схема авторизации (OIDC-провайдер? сервисные токены? mTLS?).
8. Ограничения размера вложений и retention-политика.
9. Требования к audit trail на стороне СОД.
10. Тестовый tenant/контур: как получить доступ, кто владелец (спонсор пилота)?
11. Требования к УКЭП на документы, попадающие в СОД (см. границу QUALIFIED_SIGNATURE_VALIDATION = missing).
12. Требования к размещению данных (on-prem / контур заказчика / air-gapped)?
13. NDA и критерии успеха пилота для интеграционного трека.

## Что AeroBIM НЕ заявляет до evidence

- «integrated with 10D» — до T5;
- «BCF-ready for CDE» / «CDE interoperable» — до T2;
- «S.Project integration» — до официального подтверждения заказчика.
