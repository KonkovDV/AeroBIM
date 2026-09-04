---
title: "ADR — dropped / retained approaches (week of 27.07–04.08)"
date: 2026-08-04
status: accepted
adr: ADR-RT-W-03
responds_to: RT-W-03
claim_boundary: Process ADR only. Checkpoint GO; customer_go false unchanged.
---

# ADR: решения об отказе / удержании (неделя 27.07–04.08)

Контекст: Red Team RT-W-03 — функции появлялись и исчезали внутри недели без записи
«почему отвергнуто». На защите вопрос о метрике согласия вероятен.

## Gwet’s AC1 (`gwet_ac` / `gwet_ac1`)

| Решение | **Удержано** как `aerobim.domain.eval_statistics.gwet_ac1` |
|---|---|
| Почему не удалять | RT-026 / WP-07: κ на несбалансированных метках смещён; AC1 — заявленный imbalance-robust коэффициент для dual adjudication |
| Почему имя «дропнули» в диффе | Промежуточный символ `gwet_ac` переименован/схлопнут в `gwet_ac1` + `agreement_artifact`; это не отказ от метрики |
| Альтернативы | Cohen κ / Krippendorff α — остаются в протоколе как дополнительные; публикация RT-001 — lower Wilson + agreement, не point estimate alone |
| Запрещено | Заявлять κ>0.8 выполненным до корпуса заказчика |

## Другие символы из RT-W-03 (`_content_sha`, `_region_plan_sha`, `_clamp`, `build_t`)

Внутренние хелперы stamp/PII волны; отказ/замена — следствие fail-closed hardening
(RT-STAMP-*), не смена научной метрики. Детали — в Red Team stamp notes; отдельный
ADR не требуется, пока символ не был публичным API.

## Правило вперёд

Отказ от подхода, видимого в TZ / Claims Lock / WP-07, оформляется **ADR ≤1 страница**
в тот же день, а не только коммитом-удалением.
