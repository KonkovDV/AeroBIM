# Контур развёртывания — где лежат файлы ПД во время проверки (2026-08-09)

**claim_level:** architecture_fact · **closes_rt001:** false  
**Дата:** 2026-08-09

Один вопрос без оценок: *где физически находятся файлы проектной документации, пока идёт проверка?*

| Архитектура | Где лежат файлы ПД во время проверки | Доказательство у AeroBIM |
|---|---|---|
| Облачный SaaS с внешним LLM | у провайдера модели / в его регионе | профиль `samolet_pilot`: внешний egress fail-closed |
| Гибрид (облако + on-prem) | частично у оператора, частично у провайдера | `HybridRouteGate` + PrivacyGuard; OFF==ON для вердикта |
| Закрытый контур заказчика | только в периметре заказчика | `offline_bundle closed-contour --smoke`; Docker image-track |
| Bare-metal air-gap | на машине без сети | **DEFERRED** (не заявляется как ready) |

## Что доказывается кодом (не слайдом)

1. Негативные тесты egress / SSRF (`outbound_url`, hybrid pre-gate) — см. `backend/tests/test_wp02_hybrid_advisory_pre_gate.py`, security suite.  
2. `python -m aerobim.tools.offline_bundle closed-contour --smoke` в CI job `offline-bundle-smoke`.  
3. Capability honesty: `GET /v1/system/capabilities` не маскирует `FAILED`/`NOT_VERIFIED` как OK.

## Чего здесь нет

- Утверждений «мы безопаснее NormaChecker/WAIVE/…».  
- Product SLA / accuracy.  
- Bare-metal offline-ready.

`claim_boundary`: eng / fixture evidence only · Checkpoint GO; customer_go false until RT-001/002/003.
