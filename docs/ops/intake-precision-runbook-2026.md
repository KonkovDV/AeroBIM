---
title: "Intake precision & SLA runbook — when the corpus arrives"
status: active
last_updated: "2026-07-17"
tags: [aerobim, ops, precision, intake, samolet, track-a3]
---

# Runbook: «когда приедет корпус Самолёта»

Цель — прогнать precision + SLA **за сутки**, не строя инфраструктуру. Вся
машинерия уже в репозитории (Track A1–A3): section pairing, norm packs, harness,
adjudication compiler. Ниже — последовательность шагов и точные команды.

> Claim boundary: до adjudicated customer corpus публикуется **только** «harness
> реализован». Interim contract — TP ≥ 60%. «>90%» — только после
> репрезентативного корпуса и согласованного CI. Synthetic scores ≠ product
> quality. `customer_confirmed` в typical-errors остаётся `0`.

## 0. NDA / хранение (не коммитить корпус)

- Клиентские файлы кладём в gitignored путь (например `samples/customer/…` или вне
  репозитория) — **никогда** не в публичный git. Проверить `.gitignore`.
- Пакет норм и ПД/РД — через storage jail; пути передаём как storage-relative.

## 1. Заморозка входов

Зафиксировать и снять SHA-256:

- approved norm/rule pack (`status: approved`, `approval.*` заполнены);
- IFC (federated при наличии), ПД/РД section JSON, ТЗ, расчёты;
- software commit (git rev) + версии зависимостей.

## 2. Подключить пакет: manifest или env (Track A2)

- **Manifest:** передать `norm_rule_pack_paths` в теле analyze.
- **Env:** `AEROBIM_NORM_RULE_PACK=<storage-relative>.json` как fallback.
- Отсутствующий сконфигурированный пакет → `capabilities.norm_rule_packs=failed`
  (fail-closed, не silent). Проверить, что capability = `ok` перед прогоном.

## 3. Один прогон анализа → frozen detections

Выполнить AeroBIM один раз на замороженных входах (sync `POST
/v1/analyze/project-package` или job). Сохранить `report_id` и report JSON.

Экспорт detections в схему harness (`detections.schema.json`): собрать
`cases[].findings[]` из findings отчёта, где каждый finding = `{finding_class,
rule_id, target_ref | element_guid | match_key}`. Идентичность — политика
`exact-v1` (см. `docs/evaluation/DETECTION_PRECISION_PROTOCOL_2026.md`). Схему
детекций валидировать перед adjudication.

## 4. Независимая разметка двумя инженерами (Track A3)

Каждый инженер **независимо** заполняет копию
[`adjudication-template.csv`](../../samples/benchmarks/detection-precision/adjudication-template.csv):

- одна строка на (finding × adjudicator);
- `verdict` ∈ `TP` (детектнутый реальный дефект) / `FP` (ложный) / `FN`
  (реальный дефект, пропущенный инструментом);
- обязательны `case_id, finding_class, rule_id, adjudicator_id, verdict` и хотя бы
  один из `target_ref | element_guid | match_key`;

После независимой разметки:

1. Посчитать **Cohen’s κ** (2 инженера) или **Krippendorff’s α** (≥3):
   `python -m aerobim.tools.measure_adjudicator_agreement --csv <adjudication.csv>`
2. Сохранить confusion matrix + κ/α рядом с labels digest.
3. LLM assist **не** заменяет human adjudicator и **не** открывает
   `PrecisionClaim.publishable`.
- `notes`, `timestamp` — для аудита.

## 5. Компиляция labels.json (thin wrapper)

```bash
cd backend
python -m aerobim.tools.build_detection_labels \
  --adjudication ../samples/customer/adjudication-combined.csv \
  --output ../samples/customer/labels.json \
  --dataset-id <customer-dataset-id> \
  --scope-reference <signed-scope-memo-ref> \
  --dataset-status draft
```

Согласование вердиктов: оба «real» (TP/FN) → `confirmed`; оба `FP` → `excluded`;
расхождение → `unresolved`. Разрешить все `unresolved`, затем перекомпилировать с
`--dataset-status adjudicated --method consensus --completed-at <tz-ISO>`. Компилятор
**fail-closed** откажется выдавать `adjudicated`, пока нет ≥2 adjudicators,
`scope_reference`, timezone-aware `completed_at` и `unresolved==0` — те же
условия, что и publishable-gate harness.

## 6. Precision harness

```bash
cd backend
python -m aerobim.tools.evaluate_detection_precision \
  --labels ../samples/customer/labels.json \
  --detections ../samples/customer/detections.json \
  --require-publishable \
  --min-precision 0.6 --min-recall 0.6 --min-f1 0.6 \
  --output ../artifacts/detection-precision-customer.json
```

- `--require-publishable` блокирует не-adjudicated наборы.
- Пороговые значения (>0.6 interim) — **процессный gate**, не CI. В CI пороги
  применяются **только** к synthetic fixture (`test_evaluate_detection_precision`).
- Exit code `2` = порог не пройден.

## 7. SLA ≤ 30 мин на agreed pack

```bash
cd backend
python -m aerobim.tools.measure_package_sla \
  --pack ../samples/customer/project-package-<id>.json \
  --max-minutes 30 --iterations 1 \
  --output ../artifacts/package-sla-customer.json
```

## 8. Redacted KPI export

Публикуем **только** агрегаты, без содержимого корпуса:

- micro/macro precision/recall/F1 + per-class из отчёта harness;
- SLA wall-time vs 30 мин;
- confirmed rate = TP/(TP+FP) (interim target ≥ 0.60);
- ссылки на digests входов и scope memo, **без** сырых ПД/РД/IFC.

KPI weekly rollup — в
[`../samolet-kpi-adjudication-template-2026.md`](../samolet-kpi-adjudication-template-2026.md);
traceability audit ≥ 0.90 — `aerobim.tools.audit_issue_traceability`.

## 8b. I6 — agreement + intake gate (2026-07-17)

```bash
# Dual/multi-human κ + α
aerobim-measure-adjudicator-agreement \
  --csv adjudication-combined.csv \
  --output agreement.json

# Precision with agreement gate (publishable only if customer + κ/α)
aerobim-evaluate-detection-precision \
  --labels labels.json \
  --detections detections.json \
  --agreement-json agreement.json \
  --require-publishable \
  --output detection-precision-customer.json

# Customer SLA (never use fixture default for customer packs)
aerobim-measure-package-sla \
  --pack samples/customer/<pack>.json \
  --corpus-kind customer \
  --max-minutes 30 \
  --output docs/evidence/samolet-sla-customer-<date>.json

# Intake gate must stay honest
aerobim-validate-customer-intake-gate
```

Checkpoint remains **NO_GO** until `audit/evidence/customer-intake-gate.json` flips with evidence.

**κ thresholds (honesty):** publishable gate in tooling is **κ≥0.60** / **α≥0.67** when agreement is present. Literature often cites κ≥0.80 as aspirational dual-expert quality — that is a **customer protocol stretch**, not a silent raise of the Claims Lock gate. See [`RESEARCH_ALIGNMENT_AEC_AI_2025_2026_07.md`](../architecture/RESEARCH_ALIGNMENT_AEC_AI_2025_2026_07.md).

## 9. Go/No-go

- `capabilities.*` = ok для required (нет silent skip);
- `passed ⇒ no ERROR ∧ required capabilities ok` (soundness);
- interim: TP ≥ 60%, −20% review time vs baseline, BCF в CDE, typical-errors ≥ 20.
- «>90%» — только после adjudication на репрезентативном корпусе.

## Артефакты, создаваемые по пути

| Шаг | Артефакт | Схема / контракт |
|-----|----------|------------------|
| 3 | `detections.json` | `detections.schema.json` |
| 4 | `adjudication-combined.csv` | `adjudication-template.csv` |
| 5 | `labels.json` | `labels.schema.json` |
| 6 | `detection-precision-customer.json` | harness report + agreement |
| 6b | `agreement.json` | adjudicator_agreement 1.1.0 (κ+α) |
| 7 | `package-sla-customer.json` | SLA report (`corpus_kind=customer`) |
| 8 | intake gate validation | `customer_intake_gate_validation` |
