<!-- claims-lint: allow-file reason="Deterministic kernel vs advisory overlay; ADR-001; not accuracy; NO_GO" -->
---
title: "Детерминированное ядро против advisory — один слайд"
date: "2026-09-04"
last_updated: "2026-09-04"
status: active
version: "1.0.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Architecture note. Lab tests ≠ customer SSO. Not product F1.
  Checkpoint GO; customer_go false.
---

# Аналогия антифрода

Детерминированные правила — основа скоринга. LLM — advisory-слой текста.
Решение по Shared-gate — не у модели. Человек подтверждает находку (HITL),
но **не** переписывает `summary.passed` сам по себе (ADR-001).

```
IFC + IDS + cross-doc + capabilities
        → EvidenceAssembler → summary.passed / outcome
LLM/VLM ──сбоку──→ черновик замечания
                   маркер «Синтетический контент (ИИ)»
                   expert_confirmation_required
```

`call_tool` / `change_verdict` — запрещённые действия провайдера.
Реестр инструментов: `can_change_verdict=False`, иначе `validate_invocation`
бросает. Overlay меняет только `remark`, не severity/origin.

## Доказательство не договорённостью

| Проверка | Файл |
|---|---|
| Злой черновик не меняет severity/origin | `backend/tests/test_adr001_advisory_cannot_write_verdict.py` |
| Advisory ERROR не поднимает error_count; не зеленивает ERROR движка | тот же + DeterminismGate |
| `llm_advisory` SKIPPED/FAILED не блокер pass | capability_policy |
| Профили заказчика: `llm_local_ready()` / `vlm_advisory_ready()` = false даже при флаге | Settings |
| UI не присваивает `summary.passed` | `test_ui_expert_workplace_triage.py` |

Это архитектурный тест. Политика профиля «не звонить наружу» — отдельно;
она **не** аппаратный запрет, и так и говорим.

## Fail-closed

Capability `failed` / required-not-OK роняет вердикт. Тишина ≠ успех.
Исключение, которое обязаны сказать: **llm_advisory не в списке блокеров
pass** — иначе падение модели красило бы комплект. Clash/IDS — в списке.

## Идемпотентность

Одинаковый вход → одинаковый `passed` (движок + политика). Находка без
`finding_id` / `source_id` / `evidence_refs` в персистенс не проходит
(provenance gate).

## Пределы (не RPS)

Нагрузка 5–10 комплектов/день — не масштаб. Узкое место: **1,5 ГБ приём**
против **256 МиБ SPF-анализа** (порядок buildingSMART Validation Service).
Тяжёлая конвертация на бэкенде. В браузере гигабайты не парсятся.
`apiBearerToken` в браузере — `undefined`.

## Наблюдаемость

`request_id` на прогоне; capability-таблица; HybridRouteGate trace с
`verdict_impact`. Полноценный distributed tracing / стоимость токенов на
комплект заказчика: **нет данных**.

## IDS-рынок (К2 на языке воспроизводимости)

Один IDS в разных валидаторах даёт разный результат (MDPI Buildings, 2025).
Наша ставка — fail-closed и сверка с IfcTester, не «мы умнее Solibri».
