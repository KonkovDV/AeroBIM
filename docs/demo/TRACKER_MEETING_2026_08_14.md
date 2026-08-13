<!-- claims-lint: allow-file reason="Tracker 14.08 one-pager; NO_GO and forbidden phrases as non-claims" -->
---
title: "Встреча с трекером 14.08.2026 08:00"
date: "2026-08-13"
claim_boundary: "Fixture demo. Checkpoint NO_GO. Not customer accuracy. Not DWG-ready."
---

# Трекеру, 14 августа 08:00 — одна страница

## Что показать за 3 минуты

1. Команда: `cd backend && python -m aerobim.tools.run_demo_vertical_slice`
2. Открыть `artifacts/vertical-slice-demo/report.html` — лист, замечание, `finding_id` / `evidence_refs`, вердикт **не PASS**.
3. Рядом PNG оверлея и `findings.bcfzip` (структурный ZIP, **не** CDE-ready).

Сценарий: **штамп / экспликация / толщина стены на текстовом слое PDF**. Не счёт дверей и окон.

## Честный статус

| Вопрос Сигиневича | Ответ |
| --- | --- |
| Checkpoint | **NO_GO**. RT-001: нет корпуса «ПД РФ + заключение экспертизы» (AEC-Bench — другой контур, ложные пропуски не замерены). RT-002: нет профиля приёмки «Самолёта»; **официальные IDS МОГЭ есть** ([покрытие](../evidence/norm-pack-moexp-coverage-2026-08.md)). RT-003: MEP |
| IDS МОГЭ | Три домена с [moexp.ru ТИМ](https://www.moexp.ru/services/tekhnologii-informatsionnogo-modelirovaniya/). Цифры — только из прогона IfcTester, не «ЦИМ сдан» |
| IFC 2x3 / 4 / 4x3 | Таблица с прогона: [`docs/evidence/ifc-release-matrix-2026-08.md`](../evidence/ifc-release-matrix-2026-08.md) — fixture, не точность |
| Kimi vs Qwen | **LIVE на Qwen** (~1.6 с, 1 регион, нашёл WALL-01 / 150 на open fixture). Kimi на Yandex Studio **закрыт гейтом**. Не точность продукта. [`../evidence/vlm-comparison-2026-08.md`](../evidence/vlm-comparison-2026-08.md) |
| DWG | Жёсткий **FAILED**, вердикт комплекта false. Зелёного DWG не будет. ADR 17.08 |
| CV | Heuristic регионы + text layer. Это не обученный CV |
| Что нужно от «Самолёта» | Комплект моделей + 2 разметчика + **утверждённый профиль приёмки**. Норм-пакет экспертизы МО мы уже нашли сами |

## Что сознательно не делаем до 20.08

Новые порты/DI, Iteration B.x, демо «посчитай двери», перекрас GO.

План 7 дней: [`../pilot/KT2_7DAY_PLAN_2026_08_13.md`](../pilot/KT2_7DAY_PLAN_2026_08_13.md)
