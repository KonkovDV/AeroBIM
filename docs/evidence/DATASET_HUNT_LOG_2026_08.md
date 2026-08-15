<!-- claims-lint: allow-file reason="Dataset hunt + live re-run log; counts as open_bench/fixture, not product accuracy; NO_GO" -->
---
title: "Dataset hunt log — 15.08.2026 evening"
date: "2026-08-15"
claim_boundary: >-
  Inventory and live re-runs of already-downloaded public packs. Open benches
  ≠ RF PD+expertise. Not product accuracy. Harbor agent NOT_RUN. Checkpoint NO_GO.
  closes_rt001: false. closes_rt002: false. closes_rt003: false.
---

# Dataset hunt + re-run log (15.08 evening)

SSOT for vendored files remains [`../../samples/DATASET_MANIFEST.json`](../../samples/DATASET_MANIFEST.json). This log is the tracker task-3 paste: search, re-run, errors, disposition. Not a customer corpus.

## Hunt (GitHub / Hugging Face / госэкспертизы, 15.08)

| Source | License | On this machine | Disposition |
|---|---|---|---|
| IFC-Bench v2 (HF `sylvainHellin/ifc-bench`, arXiv:2605.01698) | QA CC BY 4.0; models per-file; GPLv3 excluded | `.local/ifc-bench-v2` | Re-run smoke. Do not vendor GPL |
| AEC-Bench (HF/GitHub `nomic-ai/aec-bench`, arXiv:2603.29199) | Apache 2.0 | `.local/aec-bench` | Inventory + gold. Harbor **NOT_RUN** |
| GNI-BIM (Zenodo 10.5281/zenodo.19722012) | CC BY 4.0 models; MIT anonymization scripts | `.local/gni-bim` | Prior stress 223/224 open; not re-run 15.08 |
| Renga ПНСТ 909 publisher pack | Vendor ToS (cite GO 05.08) | `.local/renga-pnst909` | Header probe MEASURED. Exp A 18/22 snapshot dated 05.08; no 22-scenario CLI in tree |
| buildingSMART IDS TestCases | CC BY-ND 4.0 | git + NOTICE | Open-corpora smoke pins **ok** (7 cases) |
| Official MOEXP / Moscow AGR / SPb GAU IDS | publisher terms | `samples/ids/` | Engine coverage ≠ Samolet profile (RT-002 OPEN) |
| DrawingVQA (arXiv:2607.15418) | research paper | **not downloaded** | Link-only; VLM advisory fixture already inspired by it |
| ЕГРЗ / Минстрой повторное применение | N/A | — | **DEAD_CHANNEL** for files |

No new license-clean «ПД РФ + IFC + заключение экспертизы» pair appeared. IDS 1.0 remains the only approved bSI information-contract standard (1.1 is feedback-only). BCF-API 3.0 is stable; v4.0 is a proposal only.

## Live re-runs (CPython 3.12.10, this Windows host, 15.08)

| Pack | Command | Result | Error → fix |
|---|---|---|---|
| Schema-suite IFC2X3 / IFC4 / IFC4X3 n=20 | `python -m aerobim.tools.export_ifc_release_matrix` | findings 5 / 4 / 6; `passed=false`; p50 ≈ 28–36 ms; refusals `clash=skipped` (+ IFC4X3 `ids=failed`) | Tiny-skip made clash **skipped** not geom-init failed. Note in exporter updated. Fail-closed IDS on IFC4X3 is BSI 0101, not a defect |
| IFC-Bench v2 | `run_ifc_bench_smoke --version v2 --also-docs-evidence` | scored **25/1026** matched 25, mismatched 0, errors 0, pin `e47ccd…` ok | none this pass. Rate is countable subset only, `open_bench_only` |
| AEC-Bench | `run_aec_bench_smoke --also-docs-evidence` | 196 tasks; gold 50 clean / 134 has_issue / 12 qa; 43 PDFs on disk / 1340 manifest URLs; Harbor **NOT_RUN**; `null_always_clean` 0.7283 on labeled | none. Drawing-reading false-pass remains **NOT_MEASURED** |
| Open corpora pins | `run_open_corpora_profiles --mode smoke` | `pins_ok=true`; 7 regression cases | none |
| Renga header probe | `run_renga_export_probe --write-evidence` | MEASURED; FILE_SCHEMA IFC4; originating Renga 8.7; `samolet_export=false` | none. Not Exp A 18/22 IDS rerun |
| PNST 909 22-scenario IDS | — | Pack still on disk. Runtime snapshot [`pnst909-22-scenario-runtime-latest.json`](pnst909-22-scenario-runtime-latest.json) dated 2026-08-05 (18 EXECUTED / 4 NO_IDS_IN_PACK) | **No CLI in tree** to regenerate the 22-scenario axis. Do not invent a fresh 18/22. Disposition: keep snapshot; do not claim a 15.08 rerun |

## Errors found (honesty, not silent pass)

1. Tracker matrix previously said `clash=failed` on tiny walls. After `AEROBIM_CLASH_SKIP_TINY` default-on, live refusals are `clash=skipped`. Markdown note updated. Not a silent pass: all-skipped clash still fail-closed.
2. IFC4X3 `ids=failed` is fail-closed `ifcVersion` mismatch, not a product defect.
3. Harbor 160 / AEC-Bench agent trial still **NOT_RUN** (needs OpenAI/Anthropic + Docker; Yandex Studio key is a different contour).
4. GPLv3 IFC-Bench project dirs stay out of git and out of the MIT demo path.

closes_rt001: false. closes_rt002: false. closes_rt003: false. Checkpoint **NO_GO**.
