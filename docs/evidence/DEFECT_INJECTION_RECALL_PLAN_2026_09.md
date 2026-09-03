<!-- claims-lint: allow-file reason="Injection recall plan; synthetic not partner corpus; NO_GO" -->
---
title: "Defect-injection recall plan — published seed, not partner metrics"
date: "2026-08-30"
last_updated: "2026-09-03"
status: active
version: "1.1.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Plan for mutation-test recall on an injected pack. Not Samolet accuracy.
  Not product accuracy >90%. Recall on synthetics does not transfer to the
  partner pack. Checkpoint NO_GO.
---

# Recall на инъекциях (синтетика, не партнёр)

Генератор **уже есть**: `python -m aerobim.tools.inject_defects`
(`backend/src/aerobim/tools/inject_defects.py`). Тесты:
`backend/tests/test_inject_defects.py`. Дефолтный seed **20260824**.
Одинаковый seed → одинаковые мутации. Инъекция **ниже** валидатора: не вызывает
analyze API и не пишет `summary.passed`.

Манифест: `injection_manifest.json` (seed, классы, locator, claim_boundary).
Классы: `AREA_MISMATCH`, `LEVEL_MISMATCH`, `PD_RD_DIVERGENCE`, `TZ_UNSATISFIED`,
`MISSING_ELEMENT`, `UNIT_MISMATCH`, `CALC_INCONSISTENCY`, `IDS_VIOLATION`,
`CONTROL`.

Чистый исходный пакет `samples/packs/clean_pd` **в git нет**. Источник — каталог
владельца вне NDA-корней (`samples/customer` и `files/` генератор отвергает).
Городские примеры АГР **запрещены** как source.

## Recall (план; CLI склейки: EXECUTED 2026-09-03)

1. Получить шовно-чистый мини-ПД (не эталон АГР).
2. `inject_defects --source <pack> --output var/injected --seed 20260824`.
3. Прогнать детерминированный analyze на каждом варианте **кроме** чтения
   манифеста движком как подсказки.
4. Сопоставить находки с `variants[]` манифеста (класс + locator).
5. Recall = TP / (TP+FN) по инъецированным дефектам. CONTROL не входит в
   знаменатель recall.
6. Интервал: Wilson (`python -m aerobim.tools.compute_quality_protocol_stats`
   / WP-07). Публиковать **нижнюю** границу, `claim_level=synthetic_only`.

Склейка (03.09.2026): `python -m aerobim.tools.evaluate_injection_recall` —
манифест с выходом analyze через CONTROL-дифф мультимножеств. Прогон:
[`DEFECT_INJECTION_RECALL_RUN_2026_09.md`](DEFECT_INJECTION_RECALL_RUN_2026_09.md).
Не закрывает RT-001. Не шовно-чистый `summary.passed=true`.

Граница: recall на синтетике **не** переносится на комплект Самолёта.
`confirmed_partner_validation_metrics() == False`.

## Precision ~100 находок, два разметчика

Отдельный контур, не recall:

- Выборка ~100 находок движка на том же синтетическом/фикстурном прогоне.
- Два независимых разметчика; схема [`RT001_LABELING_PROTOCOL_RT026_2026_08_03.md`](../quality/RT001_LABELING_PROTOCOL_RT026_2026_08_03.md).
- κ / α: `python -m aerobim.tools.measure_adjudicator_agreement`.
- Precision против адъюдикации: `python -m aerobim.tools.evaluate_detection_precision`.
- Не κ без n. Не >90%. Не корпус партнёра.

Привлечение двух разметчиков — строка владельца, не коммит.

Связь: [`B_FINAL_SCORING_TICKSHEET_2026_09.md`](../quality/B_FINAL_SCORING_TICKSHEET_2026_09.md)
(Б2: протоколы есть, метрики партнёра нет) ·
[`QUALITY_MEASUREMENT_PROTOCOL_2026_08.md`](../pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md).
