---
title: Detection precision and adjudication protocol
status: active
last_updated: "2026-07-11"
---

# TP/FP/FN protocol для clash и inconsistency findings

Инструмент `aerobim-evaluate-detection-precision` измеряет frozen detection run
против **независимого** набора labels. Он не вычисляет качество extraction OCR/NLP
(для этого остаётся `evaluate_extraction`) и не превращает synthetic fixture в
публичный claim.

## Форматы

- labels schema: [`labels.schema.json`](../../samples/benchmarks/detection-precision/labels.schema.json);
- detections schema: [`detections.schema.json`](../../samples/benchmarks/detection-precision/detections.schema.json);
- synthetic contract fixtures: `labels-synthetic.json` и
  `detections-synthetic.json` в том же каталоге.

Finding identity по policy `exact-v1`:

1. `case_id`;
2. `finding_class`;
3. explicit `match_key`, либо exact composite
   `[rule_id, target_ref, element_guid]`.

Fuzzy matching запрещён. Duplicate identity отклоняется. Пустой target разрешён
только при `element_guid` или explicit `match_key`.

## Метрики

- `TP = expected ∩ detected`;
- `FP = detected − expected`;
- `FN = expected − detected`;
- precision = `TP/(TP+FP)`;
- recall = `TP/(TP+FN)`;
- F1 = harmonic mean;
- выдаются micro, macro, per-class и списки FP/FN.

Labels со статусом `excluded` и `unresolved` не входят в ground truth; число
таких записей публикуется. `--require-publishable` блокирует dataset, пока:

- `dataset_status != adjudicated`;
- нет `scope_reference`;
- нет двух разных adjudicator id;
- `completed_at` не timezone-aware;
- method не `consensus` / `majority-with-resolution`;
- остался хотя бы один `unresolved` label.

Protocol gate проверяет полноту метаданных, но не удостоверяет личности и не
заменяет подписанный customer adjudication log.

## Inter-annotator agreement (July 2026 bar)

Human adjudication is mandatory for publishable PrecisionClaim. Report:

| Adjudicators | Metric | Minimum for publish gate |
|---|---|---|
| 2 | Cohen’s κ on binary verdicts (TP vs not-TP / FP / FN as defined in rubric) | κ ≥ 0.60 (substantial); target ≥ 0.80 |
| ≥3 | Krippendorff’s α (nominal) | α ≥ 0.67; target ≥ 0.80 |

Always publish the **confusion matrix** (or per-class TP/FP/FN counts) alongside
F1 — scalar F1 alone is not enough. Exact-match agreement without chance
correction is forbidden as the sole reliability statistic.

**LLM-as-judge / LLM assist** may draft candidate labels but:

- cannot count toward `adjudicators`;
- cannot satisfy `PrecisionClaim.publishable`;
- cannot replace human κ/α evidence.

## Pilot procedure

1. Заморозить agreed pack, IFC/ПД/РД/TЗ/расчёты и software commit.
2. До просмотра output создать expected labels по списку типовых ошибок.
3. Выполнить AeroBIM один раз; экспортировать frozen detections.
4. Два инженера независимо размечают finding и пропуски.
5. Разногласия разрешаются и фиксируются; `unresolved` должен стать 0.
6. Запустить harness; сохранить JSON report рядом с digest входов.
7. Публиковать >90% только после репрезентативного customer corpus и
   согласованного confidence interval; interim pilot contract остаётся TP rate
   ≥60%.

## CLI / CI

```bash
cd backend
python -m aerobim.tools.evaluate_detection_precision \
  --labels ../samples/benchmarks/detection-precision/labels-synthetic.json \
  --detections ../samples/benchmarks/detection-precision/detections-synthetic.json \
  --min-precision 0.6 \
  --min-recall 0.6 \
  --min-f1 0.6 \
  --output ../artifacts/detection-precision.json
```

Threshold failure возвращает exit code `2`. Для customer evidence добавляется
`--require-publishable`. Synthetic fixture имеет заранее известные
`4 TP / 2 FP / 2 FN`; это тест математики/CI, **не** качество AeroBIM.

## Intake automation (Track A3)

Когда приедет корпус — не писать инфраструктуру, а идти по
[`../ops/intake-precision-runbook-2026.md`](../ops/intake-precision-runbook-2026.md):

- два инженера независимо заполняют
  [`adjudication-template.csv`](../../samples/benchmarks/detection-precision/adjudication-template.csv)
  (verdict `TP`/`FP`/`FN` на finding, привязка по `exact-v1` identity);
- `python -m aerobim.tools.build_detection_labels` сводит вердикты в
  `labels.json` (consensus: agree-real→`confirmed`, agree-FP→`excluded`,
  расхождение→`unresolved`) и **fail-closed** отказывается штамповать
  `adjudicated` без ≥2 adjudicators / scope / tz-`completed_at` / 0 unresolved —
  те же условия, что и `--require-publishable` здесь;
- скелет цели — [`labels-template.json`](../../samples/benchmarks/detection-precision/labels-template.json).

Пороговые значения — процессный gate; в CI пороги применяются **только** к
synthetic fixture. `customer_confirmed` остаётся `0` до подписанного корпуса.

## Claim boundary

До customer corpus разрешено заявлять только:

- «precision harness реализован»;
- «TP/FP/FN считаются reproducibly на exact labels»;
- «есть protocol gate и synthetic contract test».

Запрещено публиковать synthetic precision как clash/inconsistency accuracy или
как доказательство SLA/ROI.

## Drawing AI posture (retained local SSOT)

July 2026: [../evidence/DRAWING_AI_WORLD_PRACTICE_2026_07.md](../evidence/DRAWING_AI_WORLD_PRACTICE_2026_07.md).
