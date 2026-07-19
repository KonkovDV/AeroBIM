---
title: "Citeable evidence (jury / FAIR)"
status: active
version: "2.2.0"
last_updated: "2026-07-19"
---

# Evidence fixtures

Only **citeable** snapshots for TechLab review and reproducibility. Phase-command dumps stay under `.local/`.

| File | Role |
|------|------|
| [`runtime-baseline-latest.json`](runtime-baseline-latest.json) | Runtime LOC / test baseline |
| [`samolet-sla-pilot-moscow-2026-05-21.json`](samolet-sla-pilot-moscow-2026-05-21.json) | Fixture SLA (not customer) |
| [`tz-matrix-status-latest.json`](tz-matrix-status-latest.json) | TZ matrix status |
| [`benchmark-report-2026-05-21.md`](benchmark-report-2026-05-21.md) | Academic benchmark snapshot |

## Reproducible package evidence bundle

```bash
cd backend
python -m aerobim.tools.export_evidence_bundle \
  --pack ../samples/benchmarks/project-package-techlab-demo.json \
  --output ../artifacts/evidence-bundle/techlab-demo
```

See [`../PROJECT_STATUS_AUDIT_2026.md`](../PROJECT_STATUS_AUDIT_2026.md) · [`../benchmark-evidence-2026.md`](../benchmark-evidence-2026.md) · [`../pilot-protocol-samolet-2026.md`](../pilot-protocol-samolet-2026.md).

Audit honesty: [`../../audit/evidence/`](../../audit/evidence/) · Claims Lock: [`../../audit/reports/CLAIMS_LOCK_2026_07_17.md`](../../audit/reports/CLAIMS_LOCK_2026_07_17.md).
