---
title: "Pre-Pilot Gates Evidence 2026-05-21"
status: active
frozen_tag: pilot-2026-pre
---

# Pre-Pilot Gates Evidence (2026-05-21)

Reproducible evidence for gates 1–4 sign-off on commit `db214c9` lineage.

## Gate 1 — Deterministic replay

| Check | Result |
|---|---|
| `pytest tests/test_pilot_deterministic_replay.py -q` | **3 passed** |

## Gate 2 — Evidence rail

| Check | Result |
|---|---|
| `pytest tests -q` | **292 passed**, 2 skipped |
| `export_runtime_baseline` | `verification.status` = **APPROVED** |

Artifact: [`pre-pilot-runtime-baseline-2026-05-21.json`](pre-pilot-runtime-baseline-2026-05-21.json)

## Gate 3 — BCF handoff

| Check | Result |
|---|---|
| `pytest tests/test_bcf_export_and_clash.py tests/test_bcf3_exporter.py -q` | **42 passed** |
| BCF 2.1 export from smoke report | Endpoint `/v1/reports/{id}/export/bcf` (see `seed_smoke_report`) |
| Customer CDE import | **Scheduled pilot week 1** — record tool/version in case study |

## Gate 4 — False-positive budget

| Control | Value |
|---|---|
| `AEROBIM_CROSS_DOC_SEVERITY` | `warning` (pilot default) |
| Scope | fire + structure only |
| Pilot pack cross-doc count | **0** on fixture corpus (not a production claim) |

Artifact: [`pre-pilot-conflict-breakdown-2026-05-21.json`](pre-pilot-conflict-breakdown-2026-05-21.json)

## Extraction gate

Macro F1 = **0.86** (threshold ≥ 0.70). Artifact: [`pre-pilot-extraction-2026-05-21.json`](pre-pilot-extraction-2026-05-21.json)

## Benchmark supplementary

[`benchmark-report-2026-05-20.md`](benchmark-report-2026-05-20.md), [`benchmark-report-2026-05-20.json`](benchmark-report-2026-05-20.json)
