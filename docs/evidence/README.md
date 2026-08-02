---
title: "Citeable evidence (jury / FAIR)"
status: active
version: "2.3.0"
last_updated: "2026-08-02"
---

# Evidence fixtures

Only **citeable** snapshots for TechLab review and reproducibility. Phase-command dumps stay under `.local/`. Curated Red Team summaries: [`../quality/`](../quality/).

| File | Role |
|------|------|
| [`checkpoint2-evidence-bundle-latest.json`](checkpoint2-evidence-bundle-latest.json) | P2-04 wall-guid demo bundle pin (fixture GO) |
| [`runtime-baseline-latest.json`](runtime-baseline-latest.json) | Runtime LOC / tests / gates (schema 1.2.0; WP-01 complete required in CI) |
| [`samolet-sla-pilot-moscow-2026-05-21.json`](samolet-sla-pilot-moscow-2026-05-21.json) | Fixture SLA (not customer) |
| [`tz-matrix-status-latest.json`](tz-matrix-status-latest.json) | TZ matrix status |
| [`benchmark-report-2026-05-21.md`](benchmark-report-2026-05-21.md) | Academic benchmark snapshot |

Related (not under `docs/evidence/`):

| Path | Role |
|------|------|
| [`../../samples/benchmarks/open-corpora/`](../../samples/benchmarks/open-corpora/) | WP-06 open-corpora profiles (regression/timing only) |
| [`../pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md`](../pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md) | WP-07 quality protocol |

## Reproducible package evidence bundle

```bash
cd backend
python -m aerobim.tools.export_evidence_bundle \
  --pack ../samples/benchmarks/project-package-wall-guid-demo.json \
  --output ../artifacts/evidence-bundle/checkpoint2-wall-guid
```

P2-04 pin (annotation `ifc_guid` presence): see [`checkpoint2-evidence-bundle-latest.json`](checkpoint2-evidence-bundle-latest.json).

Legacy techlab demo:

```bash
python -m aerobim.tools.export_evidence_bundle \
  --pack ../samples/benchmarks/project-package-techlab-demo.json \
  --output ../artifacts/evidence-bundle/techlab-demo
```

Artifacts: `manifest.json`, `report.json`, `findings.json`, `capability_coverage.json`, `report.html`, `timings.json`, `logs_snippet.txt`, `README.md`.

See [`../PROJECT_STATUS_AUDIT_2026.md`](../PROJECT_STATUS_AUDIT_2026.md) · [`../ENGINEERING_STATUS_2026_08.md`](../ENGINEERING_STATUS_2026_08.md) · [`../benchmark-evidence-2026.md`](../benchmark-evidence-2026.md) · [`../pilot-protocol-samolet-2026.md`](../pilot-protocol-samolet-2026.md).

Audit honesty: [`../../audit/evidence/`](../../audit/evidence/) · Claims Lock: [`../../audit/reports/CLAIMS_LOCK_2026_07_17.md`](../../audit/reports/CLAIMS_LOCK_2026_07_17.md).
