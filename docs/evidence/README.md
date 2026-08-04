---
title: "Citeable evidence (jury / FAIR)"
status: active
version: "2.4.0"
last_updated: "2026-08-04"
---

# Evidence fixtures

Only **citeable** snapshots for TechLab review and reproducibility. Phase-command dumps stay under `.local/`. Curated Red Team summaries: [`../quality/`](../quality/).

| File | Role |
|------|------|
| [`aecv-bench-eval-latest.json`](aecv-bench-eval-latest.json) | L1 AECV: publish **`macro_extended=0.4325`** (5 fields = Table 1 metric) + `macro_bench_protocol=0.5064` reference-only; scorer validation vs Table 1 max\|Δ\|≈0.02; B.5 gates; `open_bench_only` |
| [`aec-bench-smoke-latest.json`](aec-bench-smoke-latest.json) | L1 AEC-Bench: 196-task inventory + prefetch sample; Harbor agent NOT_RUN (no agent key) |
| [`ifc-bench-v1-smoke-latest.json`](ifc-bench-v1-smoke-latest.json) | L1 open-bench: IFC-Bench v1 deterministic countable subset (`claim_level=open_bench_only`; ≠ RT-001) |
| [`../samples/benchmarks/ifc-bench-v2/IMPORT_PINS.json`](../../samples/benchmarks/ifc-bench-v2/IMPORT_PINS.json) | IFC-Bench **v2** pins (1027 QA, CC BY 4.0 QA; GPLv3 models excluded from MIT tree); checkout not vendored |
| [`checkpoint2-evidence-bundle-latest.json`](checkpoint2-evidence-bundle-latest.json) | P2-04 wall-guid demo bundle pin (fixture GO) |
| [`runtime-baseline-latest.json`](runtime-baseline-latest.json) | Runtime LOC / tests / gates (schema 1.2.0; WP-01 complete required in CI) |
| [`samolet-sla-fixture-p95-2026-08-04.json`](samolet-sla-fixture-p95-2026-08-04.json) | Fixture SLA schema **1.4.0**, gate=**p95**; not customer; advisory on/off dual-run still operator |
| [`samolet-sla-pilot-moscow-2026-05-21.json`](samolet-sla-pilot-moscow-2026-05-21.json) | Legacy fixture SLA snapshot |
| [`tz-matrix-status-latest.json`](tz-matrix-status-latest.json) | TZ matrix status |
| [`benchmark-report-2026-05-21.md`](benchmark-report-2026-05-21.md) | Academic benchmark snapshot |

Related (not under `docs/evidence/`):

| Path | Role |
|------|------|
| [`../../samples/benchmarks/open-corpora/`](../../samples/benchmarks/open-corpora/) | WP-06 open-corpora profiles (regression/timing only) |
| [`../quality/OPEN_BENCH_VS_RT001_DECISION_2026_08_04.md`](../quality/OPEN_BENCH_VS_RT001_DECISION_2026_08_04.md) | L1/L2/L3 number levels |
| [`../quality/RED_TEAM_AECV_LIVE_YANDEX_2026_08_04.md`](../quality/RED_TEAM_AECV_LIVE_YANDEX_2026_08_04.md) | Red Team reading of live AECV numbers |
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
