<!-- claims-lint: allow-file reason="Dataset attribution; license names and corpus counts are citations not product claims" -->
---
title: "AeroBIM dataset attribution"
date: "2026-08-16"
claim_boundary: "Attribution and license hygiene. Open corpora ≠ RF PD+expertise corpus. Not product accuracy. GPLv3 IFC stays out of this MIT tree."
---

# Datasets and attribution

AeroBIM is MIT. Third-party corpora stay under their own licenses. This file is the CC BY / Apache attribution surface. Counts below are **upstream published** figures (cite the source), not AeroBIM measurement.

**Data availability (Grand Jury gap г):** [`evidence/DATA_STATEMENT_2026_08.md`](evidence/DATA_STATEMENT_2026_08.md) — what is in git, what is `.local/`, what does not exist (RT-001/002 OPEN).

## Do not put in this repository

| Model / artefact | License | Public MIT tree | Samolet local demo |
| --- | --- | --- | --- |
| IFC-Bench `4351`, `ettenheim_gis`, `hitos`, `samuel_macalister_sample_house` | GNU GPLv3 | Not in git, not in distro | Allowed under `.local/` with `--samolet-demo-copyleft` |
| LibreDWG | GPL-3 | Do not link | Do not link (DWG still FAILED; show IFC/PDF) |

## AEC-Bench

- Authors / org: Nomic AI
- Paper: [arXiv:2603.29199](https://arxiv.org/abs/2603.29199)
- Code: https://github.com/nomic-ai/aec-bench
- Data: https://huggingface.co/datasets/nomic-ai/aec-bench
- License: Apache 2.0
- Published: 196 tasks, 9 families, three coverage levels (intrasheet / intradrawing / intraproject)
- Compliance-judgment slice: Mushkani, Bérard, Koseki, [arXiv:2607.29058](https://arxiv.org/abs/2607.29058) — 160 tasks / 29 projects (126 Does Not Meet, 26 Meets, 8 Missing Information)
- AeroBIM: inventory smoke `docs/evidence/aec-bench-smoke-latest.json` (196 tasks, 196 `gt.json`). Harbor agent **NOT_RUN**. Drawing-reading false-pass **NOT_MEASURED**. Gold-only `null_always_clean` floor: **134** FP / **50** TN on **184** labeled tasks (rate **0.7283**, observation unit = task). [`docs/evidence/aec-bench-false-pass-2026-08.md`](evidence/aec-bench-false-pass-2026-08.md) · sha `6133a564…57aa4e`. This is **not** RT-001 (RF PD + expertise conclusion).

## IFC-Bench V2

- Authors / org: Sylvain Hellin et al., TUM Georg Nemetschek Institute
- Data: https://huggingface.co/datasets/sylvainHellin/ifc-bench
- Paper: [arXiv:2605.01698](https://arxiv.org/abs/2605.01698)
- License (QA): CC BY 4.0
- Hugging Face card (retrieved 14.08.2026): 22 projects, 51 IFC, 1 027 QA pairs — https://huggingface.co/datasets/sylvainHellin/ifc-bench
- Paper [arXiv:2605.01698](https://arxiv.org/abs/2605.01698) states 1 027 tasks across **37 IFC models / 21 projects**. Do not blend card and paper counts in one sentence.
- Solihin-adapted classes 1–4; eval-split `eval-split-hellin2026.csv` (514 test / 512 train after leak fix)
- Multidisciplinary models used as **pointers**, not vendored: `west_riverside_hospital` (CC BY 3.0, OpenIFC / Wawan Solihin), `sixty5`, `dental_clinic`, `duplex`, `wbdg_office` (CC BY 4.0), `digital_hub` (MIT, RWTH Aachen E3D)
- AeroBIM: pins + gitignored checkout of QA CSV + non-GPL IFC (`duplex`, `dental_clinic`, `digital_hub`, `sixty5`, `wbdg_office`, `west_riverside_hospital`). GPLv3 dirs never enter git; Samolet-local demo may copy them into `.local/` with `--samolet-demo-copyleft` ([`pilot/SAMOLET_DEMO_COPYLEFT_LANE_2026_08_14.md`](pilot/SAMOLET_DEMO_COPYLEFT_LANE_2026_08_14.md)). Deterministic smoke **27/1026** scored (`output_sha256=0a1679f8…9bfa35`). Of those 27, eval-split has **12** test / **15** train — not a 514 false-pass figure. `skip_breakdown` (gpl 189 / incomplete 110 / non_numeric 66 / unmapped_nl 634) is the honest denominator, not extra accuracy. `west_riverside` is on disk for federated MEP inventory; it has **0** rows in the v2 QA CSV. Smoke: `docs/evidence/ifc-bench-v2-smoke-latest.json`

## GNI BIM Dataset

- Authors / org: Zijian Wang et al., TUM Georg Nemetschek Institute
- Zenodo: [10.5281/zenodo.19722012](https://doi.org/10.5281/zenodo.19722012)
- Code: https://github.com/ZijianWang-ZW/GNI-BIM-Dataset
- License: CC BY 4.0 (models); anonymization scripts MIT
- Published: 224 anonymized IFC (223 parsed), paired AR+STR on 7 of 9 team projects
- Caveat (upstream): student models, as-is — measure rule recall/false-omit, not «product accuracy»
- AeroBIM 14.08.2026 (gitignored `.local/gni-bim`, not in git): **224** header-open, **223** IfcOpenShell-open, **1** oversize skip (`model_6_arc.ifc`, 561838129 B — same unloadable architectural file upstream skipped). AR+STR pairs **7**/9 with product counts (e.g. `model_1` 34268 / 328). MIT BIM Whale extra: **6/6** IFC2X3. Evidence [`docs/evidence/open-ifc-stress-2026-08.md`](evidence/open-ifc-stress-2026-08.md) · `content_sha256=1682899c2eed89810708cd0999d5a98b5b4a7ecfaaf46c3f241fabafc2c5c746`. Anonymization scripts MIT-pinned, not rewritten: [`docs/evidence/gni-anonymization-pin-2026-08.md`](evidence/gni-anonymization-pin-2026-08.md)

## Official examination IDS (GAU MO «Мособлгосэкспертиза»)

- Publisher: ГАУ МО «Мособлгосэкспертиза»
- Page: https://www.moexp.ru/services/tekhnologii-informatsionnogo-modelirovaniya/
- Hashes / retrieval: `samples/ids/moexp/SOURCE.md`
- This is an approved **state examination** IDS pack. It is **not** a Samolet-signed acceptance profile.

## Official Moscow AGR IDS (ДГП / «СтроимПросто»)

- Publisher: knowledge base stroimprosto.mos.ru (article [cim-agr](https://stroimprosto.mos.ru/knowledge/article/cim-agr/))
- Pack: `samples/ids/moscow-agr/` (4 IDS from public `IDS.zip`)
- Related XML: `samples/agr/dgp/` (`AGR_TEO.xml`, `Vedomost_AGR_VED_NEW.xsd`)
- This is a **city AGR** IDS pack. It is **not** a Samolet-signed acceptance profile and **not** the frozen `moscow_agr` DI port.

## Official SPb GAU «ЦГЭ» IDS 1.0

- Publisher: СПб ГАУ «Центр государственной экспертизы»
- Page: https://www.spbexp.ru/bim/docs/
- Pack: `samples/ids/spbexp/` (22 IDS from ОКС 3.1.0 + РИИ 1.1.0 zips)
- This is a **state examination** IDS pack. It is **not** a Samolet-signed acceptance profile.

## Official MinStroy XML schemas (EGRZ / ECPE intake)

- Catalog: https://minstroyrf.gov.ru/tim/xml-skhemy/
- Pack: `samples/xsd/minstroy/` (PZ 01.07, ZnP 01.01, conclusion 01.03, survey assignment 01.00, geological report 01.00)
- Honesty: [`samples/xsd/minstroy/SOURCE.md`](../samples/xsd/minstroy/SOURCE.md)
- Product function: `egrz_intake_precheck`. Empty fixtures fail XSD. **No pass fixture.** Construction-stage schemas from the 07.08.2026 news were not on the 14.08 catalog scrape.
- This is **intake format**, not a remark corpus and **not** RT-001 CLOSED.

## buildingSMART IDS TestCases

- Publisher: buildingSMART
- License: CC BY-ND 4.0 (unmodified vendored files)
- Path: `samples/ids/buildingsmart-testcases/`
- AeroBIM fail-closed divergences (ifcVersion vs FILE_SCHEMA): `AEROBIM_FAIL_CLOSED_DIVERGENCES.json` · evidence `docs/evidence/ids-fail-closed-2026-08.md`

## Ishigaki-IDS-Bench

- Authors / org: ONESTRUCTION
- Data: https://huggingface.co/datasets/ONESTRUCTION/Ishigaki-IDS-Bench
- Paper: [arXiv:2605.22079](https://arxiv.org/abs/2605.22079)
- License: CC BY 4.0
- Published: 166 gold IDS (JA/EN). **No real IFC** in the upstream set.
- World practice: document processability of gold IDS (IDS-Audit-tool class), not LLM generation F1 as product accuracy.
- AeroBIM: `python -m aerobim.tools.run_ishigaki_ids_bench_smoke` reads HF `data/test.jsonl` (sha `38b73458…3524f831`, 166 rows). Document auditor: **166/166** gold XML well-formed + IDS 1.0 XSD + structural facets. **Not** the paper's generation F1. **No IFC.** Evidence `docs/evidence/ishigaki-ids-bench-smoke-latest.json`. Do not quote 166/166 as product accuracy.

## DrawingVQA

- Data: https://huggingface.co/datasets/S2-MIND/DrawingVQA
- Paper: [arXiv:2607.15418](https://arxiv.org/abs/2607.15418)
- License: questions **CC BY-NC-SA 4.0**; drawings are **not public**.
- AeroBIM: **link-only**. Do not vendor into this MIT tree. VLM stays advisory (ADR-001).

## Renga ПНСТ 909-2024 (publisher pack)

- Source: rengabim.com/shablons (ознакомительные цели ≠ OSS). ToS cite **GO** 2026-08-05 for aggregated metrics.
- AeroBIM: header probe MEASURED (IFC4 / Renga 8.7, not Samolet). 22-scenario pairing frozen at [`docs/evidence/pnst909-22-scenario-pairing.json`](evidence/pnst909-22-scenario-pairing.json). Runtime **18/22** snapshot dated **2026-08-05**. CLI `python -m aerobim.tools.run_pnst909_22_scenario_runtime` is in tree; live extract on this machine is a header sample only (`SKIPPED_PACK_INCOMPLETE`). Do not invent a fresh 18/22.

## What is still missing

Public «российский комплект ПД + фактическое заключение экспертизы» does not exist. Samolet project models under NDA are not here. Those two sentences are the remaining RT-001 / customer-corpus deficit. Everything else in this file was available under a free license and is now cited.
