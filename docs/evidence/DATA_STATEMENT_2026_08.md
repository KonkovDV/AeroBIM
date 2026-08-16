<!-- claims-lint: allow-file reason="Data availability statement; corpus counts as citations not product accuracy; NO_GO" -->
---
title: "Data availability statement — AeroBIM corpora (16.08.2026)"
status: active
version: "1.0.0"
last_updated: "2026-08-16"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Availability of fixtures and public benches. Not a customer PD+expertise corpus.
  Not product accuracy. Harbor NOT_RUN. Checkpoint NO_GO.
---

# Data availability statement

Academic gap from Grand Jury 16.08: the project cited the world; it did not have a single **data statement**. This file is that statement. It does **not** create a Samolet corpus.

License/attribution SSOT: [`../DATASETS.md`](../DATASETS.md). File-level pins: [`../../samples/DATASET_MANIFEST.json`](../../samples/DATASET_MANIFEST.json). Hunt + live re-runs: [`DATASET_HUNT_LOG_2026_08.md`](DATASET_HUNT_LOG_2026_08.md).

## 1. What is in the public git tree

| Class | Where | License / terms | May be used as |
|---|---|---|---|
| Synthetic fixtures (IFC, IDS, packs, drawings-as-text) | `samples/` | repo MIT unless a file says otherwise | engine regression; **never** customer evidence |
| Official examination / AGR IDS + MinStroy XSD | `samples/ids/`, `samples/xsd/minstroy/` | publisher terms; SOURCE.md next to packs | engine coverage; **not** Samolet `pack_hash` |
| buildingSMART IDS TestCases (pins) | open-corpora profiles | CC BY-ND 4.0 | smoke pins |
| Evidence JSON/MD of **our** runs | `docs/evidence/` | repo MIT + cited upstream | FAIR snapshots of **this** lab |

`DATASET_MANIFEST.json` (generated 2026-08-14): **873** listed files, **15** vendored; `corpus_kind=fixture`; `production_use: fixture only; never customer evidence`.

## 2. What lives only on the operator machine (gitignored `.local/`)

Not in GitHub. Not a substitute for RT-001.

| Pack | License | What we measured | What we did not |
|---|---|---|---|
| IFC-Bench v2 | QA CC BY 4.0; models per-file; GPLv3 **excluded from git** | countable **27/1026** `open_bench_only` | 514 eval-split as product accuracy |
| AEC-Bench | Apache 2.0 | 196-task inventory; gold-only floor 0.7283 | Harbor agent (**NOT_RUN**) |
| GNI-BIM | CC BY 4.0 models | prior stress 224 header / 223 IfcOpenShell | student models as customer PD |
| Renga ПНСТ 909 publisher pack | vendor ToS | **18/22 snapshot 05.08**; live extract truncated | a fresh 18/22 on this host |
| Ishigaki-IDS-Bench | CC BY 4.0 | 166/166 gold XML processable; **no real IFC** | paper LLM F1 as product accuracy |
| DrawingVQA | questions CC BY-NC-SA 4.0; drawings not public | **not downloaded** | MIT-tree vendoring |

GPLv3 IFC-Bench projects may be read locally with `--samolet-demo-copyleft`. They are **not** redistributed.

## 3. What is not available (and must not be invented)

| Missing object | Status | Closes |
|---|---|---|
| RF PD/RD + IFC + expertise conclusion, same revision | **not found** in public hunt 15–16.08 | RT-001 stays OPEN |
| Samolet-signed IDS / rule pack + `approval_ref` / `pack_hash` | unsigned v0.1 only | RT-002 stays OPEN |
| Dual-expert TP/FP labels on that pack | protocol ready (`plan_adjudication_corpus` n=111 for interim 0.60); **zero labeled points** | efficiency = not measured |
| Federated MEP system-clash on customer IFC | public inventory exists; `mep_system_clash=NOT_VERIFIED` | RT-003 stays OPEN |
| Independent external reproduction of our benches | all runs are author-lab | academic gap (б) |

Ask to obtain (1)–(4): [`../partners/_08_15.md`](../partners/_08_15.md).

## 4. Ethics / PII

Stamp/title-block pixels are not sent to cloud VLM (PII clip). Customer files, if they arrive, stay under NDA / `.local/` — not this git tree.

## 5. How to reproduce what **is** public

```text
cd backend
python -m aerobim.tools.run_open_corpora_profiles --mode smoke
python -m aerobim.tools.run_ifc_bench_smoke --version v2 --also-docs-evidence
python -m aerobim.tools.run_pnst909_22_scenario_runtime
```

IFC-Bench / GNI / full ПНСТ extracts require a local checkout under `.local/` (not vendored). PNST CLI returns `SKIPPED_PACK_INCOMPLETE` when the live pack is a header sample — that skip is the honest result.

Checkpoint **NO_GO**.
