<!-- claims-lint: allow-file reason="Dataset hunt + live re-run log; counts as open_bench/fixture, not product accuracy; NO_GO" -->
---
title: "Dataset hunt log — 15.08.2026 late evening + 16.08 confirm"
date: "2026-08-16"
claim_boundary: >-
  Inventory and live re-runs of already-downloaded public packs. Open benches
  ≠ RF PD+expertise. Not product accuracy. Harbor agent NOT_RUN. Checkpoint NO_GO.
  closes_rt001: false. closes_rt002: false. closes_rt003: false.
---

# Dataset hunt + re-run log (15.08 late evening)

SSOT for vendored files remains [`../../samples/DATASET_MANIFEST.json`](../../samples/DATASET_MANIFEST.json). This log is the tracker task-3 paste: search, re-run, errors, disposition. Not a customer corpus.

## Hunt (GitHub / Hugging Face / госэкспертизы, 15.08)

| Source | License | On this machine | Disposition |
|---|---|---|---|
| IFC-Bench v2 (HF `sylvainHellin/ifc-bench`, arXiv:2605.01698) | QA CC BY 4.0; models per-file; GPLv3 excluded | `.local/ifc-bench-v2` | Re-run smoke. Do not vendor GPL. Countable subset only |
| AEC-Bench (HF/GitHub `nomic-ai/aec-bench`, arXiv:2603.29199) | Apache 2.0 | `.local/aec-bench` | Inventory + gold. Harbor **NOT_RUN** |
| GNI-BIM (Zenodo 10.5281/zenodo.19722012) | CC BY 4.0 models; MIT anonymization scripts | `.local/gni-bim` | Prior stress 223/224 open; not re-run this pass |
| Renga ПНСТ 909 publisher pack | Vendor ToS (cite GO 05.08) | `.local/renga-pnst909` | Header sample only on disk. Exp A 18/22 snapshot dated 05.08 **kept** |
| Ishigaki-IDS-Bench (HF `ONESTRUCTION/Ishigaki-IDS-Bench`, arXiv:2605.22079) | CC BY 4.0 | `.local/ishigaki-ids-bench/data/test.jsonl` (16.08) | Gold IDS XML processability; **no real IFC**. Not LLM F1 |
| DrawingVQA (HF `S2-MIND/DrawingVQA`, arXiv:2607.15418) | questions **CC BY-NC-SA 4.0**; drawings not public | **not downloaded** | Link-only. Do not vendor into MIT tree |
| buildingSMART IDS TestCases | CC BY-ND 4.0 | git + NOTICE | Open-corpora smoke pins **ok** (7 cases) |
| Official MOEXP / Moscow AGR / SPb GAU IDS | publisher terms | `samples/ids/` | Engine coverage ≠ Samolet profile (RT-002 OPEN) |
| ЕГРЗ / Минстрой повторное применение | N/A | — | **DEAD_CHANNEL** for files |

No new license-clean «ПД РФ + IFC + заключение экспертизы» pair appeared. IDS **1.0** remains the only approved bSI information-contract standard (1.1 is feedback-only). BCF-API 3.0 is stable; v4.0 is a proposal only. World practice for gold IDS (Ishigaki) is document processability, not LLM generation F1 as product accuracy.

## Live re-runs (CPython 3.12.10, this Windows host, 15.08 late)

| Pack | Command | Result | Error → fix |
|---|---|---|---|
| IFC-Bench v2 | `run_ifc_bench_smoke --version v2 --also-docs-evidence` | scored **27/1026** matched 27, mismatched 0, errors 0, pin `e47ccd…` ok. Eval-split of those 27: **12** test / **15** train. `skip_breakdown`: unmapped_nl 634 / non_numeric_gt 66 / incomplete_info 110 / gpl_project_excluded 189. `first_number_on_unmapped=634` is **not** a countable backlog | Added two verified probes (wbdg railings, hub heating systems) + skip taxonomy. GPLv3 dirs stay skipped, not errors |
| AEC-Bench | `run_aec_bench_smoke --also-docs-evidence` (earlier 15.08) | 196 tasks; gold 50 clean / 134 has_issue / 12 qa; Harbor **NOT_RUN**; `null_always_clean` 0.7283 on labeled; sha `6133a564…57aa4e` | Drawing-reading false-pass remains **NOT_MEASURED** |
| Open corpora pins | `run_open_corpora_profiles --mode smoke` | `pins_ok=true`; 7 regression cases | none |
| Renga header probe | `run_renga_export_probe --write-evidence` (earlier 15.08) | MEASURED; FILE_SCHEMA IFC4; originating Renga 8.7; `samolet_export=false` | Not Exp A 18/22 IDS rerun |
| PNST 909 22-scenario IDS | `run_pnst909_22_scenario_runtime` | CLI **in tree**. Frozen pairing [`pnst909-22-scenario-pairing.json`](pnst909-22-scenario-pairing.json). Live pack = header sample only → **`SKIPPED_PACK_INCOMPLETE`** (0/18 paired IDS on disk). Docs snapshot **not** overwritten | Do **not** invent a fresh 18/22. Keep 05.08 measured 18 EXECUTED / 4 NO_IDS_IN_PACK |
| Ishigaki-IDS-Bench | `run_ishigaki_ids_bench_smoke --also-docs-evidence` | **SKIPPED** (no local `*.ids`). Not 166/166. Not LLM F1 | Unpack CC BY 4.0 gold IDS before document audit |

## Confirm 16.08 (same host, CPython 3.12)

Tracker task 3 again: hunt stays as above; re-run what is on disk; do not invent 18/22.

| Pack | Command | Result | Error → fix |
|---|---|---|---|
| IFC-Bench v2 | `run_ifc_bench_smoke --version v2 --also-docs-evidence` | scored **27/1026** matched 27, mismatched 0, errors 0, pin `e47ccd…` ok. `output_sha256=6ca587eb…9477e1` | none |
| Open corpora pins | `run_open_corpora_profiles --mode smoke` | `pins_ok=true`; 7 cases | none |
| PNST 909 22-scenario IDS | `run_pnst909_22_scenario_runtime` | **`SKIPPED_PACK_INCOMPLETE`** (0/18 paired IDS). Docs snapshot **not** written | Keep 05.08 **18/22**. Full extract is not on this machine |
| Ishigaki-IDS-Bench | `run_ishigaki_ids_bench_smoke --also-docs-evidence` | HF `data/test.jsonl` (166 rows, sha `38b73458…3524f831`). Auditor: **166/166** gold XML processable (0 error / 0 warning files). `real_ifc=false` | none — still **not** generation F1, still **not** product accuracy |
| GNI-BIM / Harbor / DrawingVQA | not re-run / not downloaded | Prior GNI stress stands. Harbor **NOT_RUN**. DrawingVQA stays link-only | none |

## Tracker paste (задача 3, Дмитрий)

Поиск в открытых источниках: публичной пары «ПД РФ + заключение экспертизы» нет. DrawingVQA не качали (BY-NC-SA, чертежи не публичные).

Прогон уже скачанного 16.08:

- IFC-Bench v2: **27/1026** countable, pin ok, 0 mismatch. Это не 514 и не точность продукта.
- ПНСТ 909: CLI в дереве, pairing на 22 сценария заморожен. На диске header-sample → `SKIPPED_PACK_INCOMPLETE`. Снимок **18/22 от 05.08** не переписывали.
- Ishigaki: 166 gold XML с HF, document-audit **166/166** well-formed. Нет IFC. Это не F1 из статьи.
- AEC-Bench Harbor по-прежнему **NOT_RUN**.

## Errors found (honesty, not silent pass)

1. Tracker matrix previously said `clash=failed` on tiny walls. After `AEROBIM_CLASH_SKIP_TINY` default-on, live refusals are `clash=skipped`. Not a silent pass: all-skipped clash still fail-closed.
2. IFC4X3 `ids=failed` is fail-closed `ifcVersion` mismatch, not a product defect.
3. Harbor 160 / AEC-Bench agent trial still **NOT_RUN** (needs OpenAI/Anthropic + Docker; Yandex Studio key is a different contour).
4. GPLv3 IFC-Bench project dirs stay out of git and out of the MIT demo path (189 v2 rows classified `gpl_project_excluded`).
5. Full Renga ПНСТ 909 extract is no longer on this machine (only `pnst909-c14-mf-renga-87.ifc`). CLI refuses to overwrite the 05.08 18/22 snapshot with a fake 0/22.
6. Greedy first-number parse on unmapped GT (`first_number_on_unmapped=634`) is **not** 634 extra countable probes.

closes_rt001: false. closes_rt002: false. closes_rt003: false. Checkpoint **NO_GO**.
