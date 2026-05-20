---
title: "Post-Pilot Readiness Scaffold 2026"
status: active
target_date: "2026-11"
---

# Post-Pilot Readiness Scaffold (November 2026)

Fill when pilot weeks 1–12 complete. Do not mark **Go** without KPI evidence in [`pilot-case-study-report-2026.md`](../pilot-case-study-report-2026.md).

## Inputs required

| Input | Location |
|---|---|
| Weekly logs W1–Wn | [`pilot-weekly-log-2026.md`](../pilot-weekly-log-2026.md) |
| Frozen baseline | tag `pilot-2026-pre` |
| Final tag (optional) | `pilot-2026-final` on last evidence commit |
| Decision memo | [`post-pilot-go-no-go-memo-2026.md`](../post-pilot-go-no-go-memo-2026.md) |
| Branch choice | [`post-pilot-fork-2026.md`](../post-pilot-fork-2026.md) |

## Re-run on final SHA

```powershell
cd AeroBIM\backend
.\.venv-pilot\Scripts\python.exe -m pytest tests -q
.\.venv-pilot\Scripts\python.exe -m aerobim.tools.evaluate_extraction --min-macro-f1 0.70
.\.venv-pilot\Scripts\python.exe -m aerobim.tools.generate_benchmark_report --output-dir ../docs/evidence
```

Store outputs as `docs/evidence/pilot-2026-final-*` when publishing.

## Decision record (fill November)

| Branch | Selected? | Notes |
|---|---|---|
| A — Enterprise | [ ] | Postgres/OIDC tranche |
| B — Research | [ ] | Publication + bSDD |
| Partial | [ ] | Spatial/quantity hardening only |
| C — Pause | [ ] | Archive pilot artifacts |
