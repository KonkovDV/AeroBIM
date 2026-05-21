---
title: "Samolet KPI Adjudication Template 2026"
status: active
version: "1.0.0"
last_updated: "2026-05-21"
tags: [aerobim, samolet, kpi]
---

# KPI adjudication (Wave 2)

Per [`pilot-kpi-protocol-2026.md`](pilot-kpi-protocol-2026.md). Engineer labels each exported BCF topic.

## Per-issue log

| BCF topic / rule_id | Severity | Engineer verdict (TP/FP/TN/FN) | Notes |
|---------------------|----------|-------------------------------|-------|
| | | | |

## Weekly rollup

| Week | Exported | TP | FP | Confirmed rate | Manual hours | Assisted hours | Savings % |
|------|----------|---:|---:|---------------:|-------------:|---------------:|----------:|
| W5 | | | | | | | |
| W10 | | | | | | | |

**Confirmed rate** = TP / (TP + FP). Target ≥ **0.60**.

## Traceability audit

```powershell
cd AeroBIM\backend
.\.venv-pilot\Scripts\python.exe -m aerobim.tools.audit_issue_traceability --report-id <id> --output ..\docs\evidence\internal\traceability-audit.json
```

Target ratio ≥ **0.90**.
