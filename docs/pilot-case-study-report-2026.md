---
title: "Pilot Case Study Report 2026 (Section 5)"
status: draft
---

# Pilot Moscow — Case Study Report (Section 5)

## Scope

Illustrative case study on one package (N=1). Metrics are anonymized; no customer logos.

## Protocol references

- Pre-pilot gates: [`pilot-pre-pilot-gates-2026.md`](pilot-pre-pilot-gates-2026.md)
- KPI protocol: [`pilot-kpi-protocol-2026.md`](pilot-kpi-protocol-2026.md)
- Deployment: [`pilot-deployment-2026.md`](pilot-deployment-2026.md)
- Weekly log: [`pilot-weekly-log-2026.md`](pilot-weekly-log-2026.md)
- Frozen tag: [`pilot-frozen-tag-protocol-2026.md`](pilot-frozen-tag-protocol-2026.md)
- Execution runbook: [`pilot-execution-runbook-2026.md`](pilot-execution-runbook-2026.md)
- Samolet alignment: [`samolet-techlab-alignment-2026.md`](samolet-techlab-alignment-2026.md)
- CDE handoff: [`pilot-cde-handoff-2026.md`](pilot-cde-handoff-2026.md)
- Compliance scorecard: [`samolet-compliance-scorecard-2026.md`](samolet-compliance-scorecard-2026.md)

Russian interview questions: [`pilot-case-study-report-ru.md`](pilot-case-study-report-ru.md).

## BCF handoff checklist (Gate 3)

Complete before pilot week 1:

| Step | Record here |
|---|---|
| Coordination tool name + version | TBD pilot week 1 (repo: BCF 2.1 export verified — [`evidence/pre-pilot-bcf-handoff-2026-05-21.json`](evidence/pre-pilot-bcf-handoff-2026-05-21.json)) |
| BCF version used (`2.1` default or `3.0` opt-in) | **2.1** (default for pre-pilot evidence) |
| Import succeeded (topics + messages visible) | pending — see [`pilot-cde-handoff-2026.md`](pilot-cde-handoff-2026.md) Scenario A/B |
| Sample screenshot path (internal, not in public repo) | `docs/evidence/internal/cde-import-proof/` |
| Engineer TP/FP labeling process agreed | [`samolet-kpi-adjudication-template-2026.md`](samolet-kpi-adjudication-template-2026.md) |
| Clash semantics agreed (3D vs cross-doc) | TBD week 1 — alignment § Clash policy |

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
| Deterministic replay | Identical issue signature across 2 runs | pass (pre-pilot) | pass |
| Pre-pilot cross-doc on fixture pack | Informational only | 0 issues | n/a |
| Package SLA (Samolet) | Wall-clock analyze, agreed pack | TBD | ≤ 30 min |
| Review hours saved | Manual − assisted (same pack) | TBD | ≥ 20% |

## Publication ethics

Aggregate metrics only; no project-identifying data.
