---
title: "Pilot harness + live demo evidence runbook"
status: active
version: "1.0.0"
last_updated: "2026-07-24"
claim_boundary: "Fixture metrics ≠ customer precision. Publish customer numbers only with adjudicated corpus + approved pack."
---

# Harness размеченного среза и живой демо-прогон

## A. Демо-прогон + evidence-бандл (поток 2)

### Стабильный комплект

| Предпочтение | Путь / заметка |
|--------------|----------------|
| Инженерный fixture | `samples/` + pack JSON из CI / eng fixtures |
| Customer (когда появится) | `samples/customer/` **local only, never git** |
| Env / профиль | [`SAMOLET_PILOT_ENV_RUNBOOK_2026_07.md`](SAMOLET_PILOT_ENV_RUNBOOK_2026_07.md) |

### Полный контур (чек)

- [ ] IFC / IDS  
- [ ] Cross-document  
- [ ] Clash (generic; MEP system-aware — только если scope + matrix)  
- [ ] OCR / raster (если в профиле)  
- [ ] Provenance на findings  
- [ ] HITL path (хотя бы один review-event в бандле или документированный skip)  
- [ ] BCF 2.1 ZIP  
- [ ] Явные `passed` / `failed` / `skipped` / `missing` в capability coverage  

### Воспроизводимый запуск

```bash
cd backend
python -m aerobim.tools.export_evidence_bundle \
  --pack ../samples/<agreed-or-fixture-pack>.json \
  --output ../artifacts/pilot-evidence/<run-id>
```

Бандл обязан содержать: хэши входов, report JSON/HTML, findings, capability coverage, timings, code version / commit, reproduction README.

**Критерий:** повторный запуск на том же комплекте → сопоставимый итог (golden / hash policy из eng gates).

### Обязательная оговорка при показе MEP на fixture

Федеративный MEP-граф на инженерной фикстуре выглядит «живым», но capability
`mep_system_clash` при этом **not_verified** (правильно и намеренно — RT-003 OPEN).
Ведущий демо обязан проговорить (и слайд обязан содержать) дословно:

> «Это инженерная фикстура, не данные заказчика. Системно-семантический
> MEP-анализ остаётся not_verified до федеративного IFC и подписанной матрицы
> заказчика; демонстрируется методика, не готовая возможность.»

Без этой оговорки показ MEP-сценария на fixture запрещён (Claims Lock:
«MEP delivered» — запрещённая формулировка). Сверка: `GET /v1/system/capabilities`
покажет текущий статус прямо во время демо — можно показать жюри/заказчику.

## B. Harness оценки (поток 4)

### Разделение данных

| Split | Назначение | Запрет |
|-------|------------|--------|
| `train` / tune | Настройка правил | Не публиковать как pilot KPI |
| `held_out` / `test` | Оценка | Единственный publishable precision |
| Fixture / synthetic | CI | `claim_labels` / dataset_status ≠ customer evidence |

### Команды

```bash
cd backend

# 1) Согласие экспертов
python -m aerobim.tools.measure_adjudicator_agreement \
  --csv ../samples/benchmarks/detection-precision/<pilot>-adjudication.csv

# 2) Precision / recall / F1 / FP-rate (exact match TP/FP/FN)
python -m aerobim.tools.evaluate_detection_precision \
  --labels ../samples/benchmarks/detection-precision/<labels>.json \
  --detections ../artifacts/pilot-evidence/<run-id>/detections.json \
  --output ../artifacts/pilot-evidence/<run-id>/precision-report.json
```

Шаблоны: `samples/benchmarks/detection-precision/`  
(`labels-customer-protocol-template.json`, `adjudication-template.csv`, `agreement-template.json`).

### Обязательные метрики в отчёте одного запуска

| Метрика | Источник |
|---------|----------|
| TP, FP, FN | `evaluate_detection_precision` |
| Precision, recall, F1, FP-rate | то же, в т.ч. по discipline / class |
| Cohen’s κ / Krippendorff’s α | `measure_adjudicator_agreement` |
| Размер корпуса, config, code version | evidence-бандл + precision report |
| Ошибки по категориям | breakdown по `finding_class` |
| Wall-clock полного прогона | evidence timings |
| Time-to-first-finding | зафиксировать в run notes (если нет автополя — вручную в README бандла) |

### Interim порог пилота

**TP/(TP+FP) ≥ 0.60** на held-out после adjudication — только при корпусе заказчика и согласованной разметке.  
Fixture synthetic precision **не** подставлять в пилотный отчёт Самолёту.

**Размер корпуса — не из воздуха** (`aerobim.tools.plan_adjudication_corpus`, якоря:
Wilson 1927 / Brown–Cai–DasGupta 2001 / Miller 2024 arXiv 2411.00640). При плановом
ожидании 0.75, α=0.05, power=0.8: **≥62** размеченных находок для доказательства
порога (критерий ≥44/62), **рекомендация 111** для CI-полуширины ≤0.08
(при 83/111 нижняя граница Wilson ≈ 0.66 > 0.60). Пересчитать одной командой
при согласовании других параметров с заказчиком.

### nDCG (ранжирование)

В ТЗ v2 заявлен nDCG (graded 0/1/2). **Статус кода (2026-07-26): реализован** —
`aerobim.tools.evaluate_ranking_quality` (tie-aware expected nDCG@5/10/full,
McSherry–Najork 2008; exponential gain 2^rel−1; cluster-bootstrap CI среднего;
case с IDCG=0 исключается и считается явно). Вход — артефакт
`ranking_quality_labels` (per-case: `finding_id`, `priority_score`, `relevance` 0/1/2).

```bash
# 3) nDCG ранжирования (graded labels после adjudication)
python -m aerobim.tools.evaluate_ranking_quality \
  --labels ../samples/benchmarks/detection-precision/<ranking-labels>.json \
  --output ../artifacts/pilot-evidence/<run-id>/ranking-report.json
```

Fixture-вердикты не публикуются как качество ранжирования продукта (RT-001);
nDCG не влияет на `summary.passed`.

## C. Связка с Checkpoint #2

| Дата | Done when |
|------|-----------|
| 1–3 авг | Fixture демо-бандл + harness dry-run на synthetic labels |
| 4–10 авг | Intake customer pack; baseline часов |
| 11–20 авг | Промежуточный прогон + precision draft (если labels готовы) |
| 3–21 сен | Публикуемый отчёт только с adjudicated + approved pack |
