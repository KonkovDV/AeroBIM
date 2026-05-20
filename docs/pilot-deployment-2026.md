---
title: "AeroBIM Pilot Deployment 2026"
status: active
version: "1.0.0"
last_updated: "2026-05-20"
tags: [aerobim, pilot, deployment]
---

# Pilot Deployment Guide

## Recommended shape

**Standalone Docker or VM** on customer-isolated infrastructure per [ops/standalone-runbook.md](../ops/standalone-runbook.md).

| Component | Pilot default | Post-pilot |
|---|---|---|
| Storage | Local `ObjectStore` + `var/reports` | Postgres index + S3/MinIO |
| Auth | Static bearer / API key | OIDC/JWT (B.3) |
| Jobs | In-process async (`/submit`) | arq + Redis (B.2) |

## Environment

```bash
AEROBIM_STORAGE_DIR=/data/aerobim/reports
AEROBIM_API_BEARER_TOKEN=<pilot-secret>
AEROBIM_CROSS_DOC_SEVERITY=warning
```

Optional ISO 19650 fields are passed per request, not globally.

## False-positive budget (Gate 4)

Before pilot week, capture a `ConflictKind` baseline on the pilot manifest:

```bash
cd backend
python -m aerobim.tools.summarize_conflict_breakdown \
  --pack ../samples/benchmarks/project-package-pilot-moscow-v1.json
```

| Kind | Operator action |
|---|---|
| `unit-mismatch` | Prefer typed `QuantityValue` path; tune severity to `info` if advisory |
| `hard-conflict` | Default blocking candidate when `AEROBIM_CROSS_DOC_SEVERITY=error` |
| `ambiguous-mapping` | Manual review only; do not auto-block |

Recommended pilot default: `AEROBIM_CROSS_DOC_SEVERITY=warning` until TP rate is confirmed in week 1–2.

## Smoke after deploy

```bash
curl -H "Authorization: Bearer $TOKEN" https://<host>/health
python -m aerobim.tools.seed_smoke_report
python -m aerobim.tools.run_live_review_smoke
```

## Data handling

- Pilot IFC/PDF artifacts stay inside `AEROBIM_STORAGE_DIR`
- TTL: optional `AEROBIM_REPORT_TTL_DAYS` for retention policy
- No outbound model calls required for deterministic pilot path

## Support boundary

AeroBIM team supports reproducibility and export defects. Customer owns engineering sign-off and normative interpretation.
