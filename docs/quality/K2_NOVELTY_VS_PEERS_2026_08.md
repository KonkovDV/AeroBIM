<!-- claims-lint: allow-file reason="K2 novelty vs peers; competitor 90% is their claim; ablation fixture-only; NO_GO" -->
---
title: "K2 novelty vs peers — methodology is the wedge, not 90%"
date: "2026-08-29"
last_updated: "2026-08-29"
status: active
version: "1.0.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Competitive honesty for K2. Peer 90% figures stay their claims. Ablation is
  fixture-only. Not product accuracy. Checkpoint NO_GO.
---

# К2: новизна против витрины «90% без методики»

Публичный отбор (08.04.2026) включает **научно-технологическую новизну**.
Тай-брейк системы A новизну **не** использует (К3, затем К4). К2 всё равно
даёт до 20 баллов.

## Чем мы отличимы (и чем нет)

| Ось | AeroBIM | Витрина сверстников (карточки 09.08) |
|---|---|---|
| Verdict | ADR-001: LLM не пишет `summary.passed` | У части не заявлено, кто ставит вердикт |
| Методика | Протокол классов + dual-rater + κ | «>90%» без корпуса и TP/FP |
| Слой | Требования ↔ IFC ↔ листы ↔ ревизии | Нормы PDF / DWG-геометрия / CV-скан |
| Ablation | A0–A3 на фикстуре | Не показано |
| Повторяемость | CI pin `attested_by=ci` | Не показано |

Полная пятиколоночная таблица: [`../demo/KT2_TASK07_COMPARISON_2026_08.md`](../demo/KT2_TASK07_COMPARISON_2026_08.md).
Цифры сверстников не переносить как наши.

Ablation (лаборатория УГТ 4, не точность продукта):
[`../evidence/ablation-study-report.md`](../evidence/ablation-study-report.md).
A0 IDS-only → A2 кросс-док. Это вклад модальностей на фикстуре, не RT-001.

Честный проигрыш остаётся в силе: корпус норм и живой DWG у части сверстников
сильнее **заявлены**. Мы не «лучше Solibri глобально». Клин — измеримость и
openBIM-шов, не магия скана.
