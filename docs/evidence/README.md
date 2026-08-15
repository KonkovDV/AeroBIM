<!-- claims-lint: allow-file reason="Evidence index; open-corpus phrases as coverage map, not product accuracy" -->
---
title: "Citeable evidence (jury / FAIR)"
status: active
version: "2.5.3"
last_updated: "2026-08-15"
---

# Evidence fixtures

Only **citeable** snapshots for TechLab review and reproducibility. Phase-command dumps stay under `.local/`. Curated Red Team summaries: [`../quality/`](../quality/).

| File | Role |
|------|------|
| [`aecv-bench-eval-latest.json`](aecv-bench-eval-latest.json) | L1 AECV: publish **`macro_extended=0.4325`** (5 fields = Table 1 metric) + `macro_bench_protocol=0.5064` reference-only; scorer validation vs Table 1 max\|Δ\|≈0.02; B.5 gates; `open_bench_only` |
| [`aec-bench-smoke-latest.json`](aec-bench-smoke-latest.json) | L1 AEC-Bench: 196-task inventory + 196 `gt.json`; Harbor agent NOT_RUN; ≠ RT-001 |
| [`norm-pack-moexp-coverage-2026-08.md`](norm-pack-moexp-coverage-2026-08.md) · [`.json`](norm-pack-moexp-coverage-2026-08.json) | Official GAU MO IDS executed by IfcTester; engine coverage ≠ CIM compliance; `by_kind` = attributes vs classification; does not close RT-002 customer profile |
| [`norm-pack-moscow-agr-coverage-2026-08.md`](norm-pack-moscow-agr-coverage-2026-08.md) · [`.json`](norm-pack-moscow-agr-coverage-2026-08.json) | Official Moscow AGR IDS from stroimprosto; not Samolet; not `moscow_agr` DI port |
| [`norm-pack-spbexp-coverage-2026-08.md`](norm-pack-spbexp-coverage-2026-08.md) · [`.json`](norm-pack-spbexp-coverage-2026-08.json) | Official SPb GAU CGE IDS 1.0; second GAU pack; not Samolet |
| [`vlm-comparison-2026-08.md`](vlm-comparison-2026-08.md) · [`.json`](vlm-comparison-2026-08.json) | Qwen LIVE on fixture; Kimi GATED; `comparison_not_run`. Not a bake-off; not product accuracy |
| [`vertical-slice-demo-live-2026-08-14.md`](vertical-slice-demo-live-2026-08-14.md) | Live `run_demo_vertical_slice` pin: exit 0, `summary.passed=false`, NO_GO; PNG/manifest hashes stable; report/BCF drift via `created_at` |
| [`DATASET_HUNT_LOG_2026_08.md`](DATASET_HUNT_LOG_2026_08.md) | Tracker task-3: hunt + live re-runs 15.08 evening. Open benches ≠ RT-001. Harbor NOT_RUN. PNST 22-scenario CLI absent |
| [`ifc-release-matrix-2026-08.md`](ifc-release-matrix-2026-08.md) · [`.json`](ifc-release-matrix-2026-08.json) | Fixture IFC2X3/IFC4/IFC4X3 kernel: findings 5/4/6, `passed=false`, `clash=skipped`. sha `559dcd91…46391`. Not customer accuracy |
| [`aec-bench-false-pass-2026-08.md`](aec-bench-false-pass-2026-08.md) · [`.json`](aec-bench-false-pass-2026-08.json) | Harbor drawing-reading false-pass **NOT_MEASURED**. Gold-only `null_always_clean`: 134 FP / 50 TN / 184 labeled (0.7283). sha `6133a564…57aa4e` |
| [`solihin-rule-classes-2026-08.md`](solihin-rule-classes-2026-08.md) · [`.json`](solihin-rule-classes-2026-08.json) | Solihin & Eastman 1–4 classification of in-repo rules. Class 4 = not claimed |
| [`ids-audit-2026-08.md`](ids-audit-2026-08.md) · [`.json`](ids-audit-2026-08.json) | `XmlIdsDocumentAuditor` on 50 jurisdiction IDS (MOEXP 24 / AGR 4 / SPb 22). Not buildingSMART IDS-Audit-tool binary. Not customer_pack_hash. Does not close RT-002 |
| [`stale-norm-scan-2026-08.md`](stale-norm-scan-2026-08.md) · [`.json`](stale-norm-scan-2026-08.json) | GOST R 21.101-2020 cited after 2026-04-01 → `AEROBIM-NORM-SUPERSEDED`. Not AGR completeness |
| [`agr-exchange-2026-08.md`](agr-exchange-2026-08.md) · [`.json`](agr-exchange-2026-08.json) | Class-1 AGR exchange shape. Territorial Moscow NPA citation; IDS zip `not_npa`. Not GrK art. 49. Not moscow_agr profile |
| [`open-ifc-stress-2026-08.md`](open-ifc-stress-2026-08.md) · [`.json`](open-ifc-stress-2026-08.json) | Header 224/224 GNI + 15/15 fixtures; IfcOpenShell 223 ok / 1 oversize skip; AR+STR product counts; BIM Whale 6/6. sha `1682899c…c746` |
| [`gni-anonymization-pin-2026-08.md`](gni-anonymization-pin-2026-08.md) · [`.json`](gni-anonymization-pin-2026-08.json) | MIT anonymization scripts pinned; execution SKIPPED (hardcoded paths; Zenodo already anonymized) |
| [`federated-clash-planted-2026-08.md`](federated-clash-planted-2026-08.md) · [`.json`](federated-clash-planted-2026-08.json) | Planted federated IfcClash (walls; pipe vs wall). Engine rehearsal. `closes_rt003=false`, `mep_system_clash=NOT_VERIFIED` |
| [`federated-clash-duplex-2026-08.md`](federated-clash-duplex-2026-08.md) · [`.json`](federated-clash-duplex-2026-08.json) | IFC-Bench duplex ARC vs MEP IfcClash (837 hits). Open bench. `closes_rt003=false` |
| [`ifc-bench-v2-smoke-latest.json`](ifc-bench-v2-smoke-latest.json) · [`ifc-bench-v2-smoke-2026-08-04.md`](ifc-bench-v2-smoke-2026-08-04.md) | Countable subset **25/1026** (12 test / 13 train of those 25). Not 514 false-pass. `output_sha256=64cd4cff…b74ea6` |
| [`moexp-on-gni-sample-2026-08.md`](moexp-on-gni-sample-2026-08.md) · [`.json`](moexp-on-gni-sample-2026-08.json) | Official MOEXP IDS on one GNI student IFC. 389/389 fail. Not CIM compliance |
| [`upstream-validate-overlap-2026-08.md`](upstream-validate-overlap-2026-08.md) | What duplicates bSI validate / Gherkin / ifcbench; keep vs replace. Not a run |
| [`../samples/benchmarks/ifc-bench-v2/IMPORT_PINS.json`](../../samples/benchmarks/ifc-bench-v2/IMPORT_PINS.json) | IFC-Bench **v2** pins (1027 QA, CC BY 4.0 QA; GPLv3 models excluded from MIT tree); checkout not vendored |
| [`checkpoint2-evidence-bundle-latest.json`](checkpoint2-evidence-bundle-latest.json) | P2-04 wall-guid demo bundle pin (fixture GO) |
| [`runtime-baseline-latest.json`](runtime-baseline-latest.json) | Runtime LOC / tests / gates (schema 1.2.0; WP-01 complete required in CI) |
| [`runtime-baseline-wave-a-windows-2026-08-15.md`](runtime-baseline-wave-a-windows-2026-08-15.md) | Local Wave A pytest on HEAD `005b7bc`: 2259 passed / 12 skipped / 0 failed. **Not** CI pin; does not replace 2167 |
| [`samolet-sla-fixture-p95-2026-08-04.json`](samolet-sla-fixture-p95-2026-08-04.json) | Fixture SLA schema **1.4.0**, gate=**p95**; not customer; advisory on/off dual-run still operator |
| [`tracker-baseline-2026-08-07.md`](tracker-baseline-2026-08-07.md) · [`.pdf`](tracker-baseline-2026-08-07.pdf) | К0 tracker baseline (NO_GO; open-bench + fixture + synthetic); commercial counts local-only |
| [`sprint2-synthetic-baseline-2026-08-04.json`](sprint2-synthetic-baseline-2026-08-04.json) | Synthetic detection twin (`synthetic_only`) |
| [`samolet-sla-pilot-moscow-2026-05-21.json`](samolet-sla-pilot-moscow-2026-05-21.json) | Legacy fixture SLA snapshot |
| [`tz-matrix-status-latest.json`](tz-matrix-status-latest.json) | TZ matrix status |
| [`benchmark-report-2026-05-21.md`](benchmark-report-2026-05-21.md) | Academic benchmark snapshot |

Related (not under `docs/evidence/`):

| Path | Role |
|------|------|
| [`../../samples/benchmarks/open-corpora/`](../../samples/benchmarks/open-corpora/) | WP-06 open-corpora profiles (regression/timing only) |
| [`../../samples/xsd/minstroy/SOURCE.md`](../../samples/xsd/minstroy/SOURCE.md) | MinStroy XSD intake; PZ 01.07 / ZnP 01.01 + survey assignment/report; construction-stage catalog gap; not RT-001 |
| [`../quality/RED_TEAM_AECV_LIVE_YANDEX_2026_08_04.md`](../quality/RED_TEAM_AECV_LIVE_YANDEX_2026_08_04.md) | Red Team reading of live AECV numbers |
| [`../quality/RED_TEAM_KT2_HUB_MEP_2026_08_14.md`](../quality/RED_TEAM_KT2_HUB_MEP_2026_08_14.md) | Red Team of Hub IFC-Bench / West Riverside / AEC prefetch (`ca6801d`); RT-HUB-01/02/03 mitigated |
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
