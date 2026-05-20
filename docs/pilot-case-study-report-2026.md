---
title: "Pilot Case Study Report 2026 (Section 5)"
status: draft
---

# Pilot Moscow — Case Study Report (Section 5)

## Объём

Иллюстративное кейс-стадио на одном пакете (N=1). Метрики анонимизированы; без логотипов заказчиков.

## Protocol references

- Pre-pilot gates: [`pilot-pre-pilot-gates-2026.md`](pilot-pre-pilot-gates-2026.md)
- KPI protocol: [`pilot-kpi-protocol-2026.md`](pilot-kpi-protocol-2026.md)
- Deployment: [`pilot-deployment-2026.md`](pilot-deployment-2026.md)
- Weekly log: [`pilot-weekly-log-2026.md`](pilot-weekly-log-2026.md)
- Frozen tag: [`pilot-frozen-tag-protocol-2026.md`](pilot-frozen-tag-protocol-2026.md)
- Execution runbook: [`pilot-execution-runbook-2026.md`](pilot-execution-runbook-2026.md)

## BCF handoff checklist (Gate 3)

Complete before pilot week 1:

| Step | Record here |
|---|---|
| Coordination tool name + version | |
| BCF version used (`2.1` default or `3.0` opt-in) | |
| Import succeeded (topics + messages visible) | yes / no |
| Sample screenshot path (internal, not in public repo) | |
| Engineer TP/FP labeling process agreed | |

Export command:

```bash
curl -H "Authorization: Bearer $TOKEN" \
  -o pilot-export.bcfzip \
  "https://<host>/v1/reports/<report_id>/export/bcf?version=2.1"
```

## KPI table (template — fill from production logs)

| KPI | Definition | Pilot value | Target |
|---|---|---:|---|
| Time-to-first-contradiction | Minutes from package ingest to first `cross-document` issue | TBD | < 15 min |
| Confirmed findings rate | Engineer-confirmed BCF issues / total exported | TBD | ≥ 60% |
| Traceability | Issues with element GUID + `source_id` | TBD | ≥ 90% |
| Extraction macro F1 | RU corpus benchmark | ≥ 0.70 | ≥ 0.70 |
| Deterministic replay | Identical issue signature across 2 runs | pass | pass |

## Качественная обратная связь (5–7 вопросов)

1. Были ли междокументные замечания пригодны для работы без ручного поиска в IFC?
2. Устраивал ли обмен через BCF в вашем CDE?
3. Помогали ли поля ISO 19650-lite (стадия, ревизия) сократить переделки?
4. Оцените долю ложных срабатываний (1–5) отдельно для разделов «пожар» и «конструктив».
5. Готовы ли использовать инструмент на этапе внутренней проверки до экспертного подписания?

## Этика публикации

Только агрегированные метрики; без идентифицирующих данных проекта.
