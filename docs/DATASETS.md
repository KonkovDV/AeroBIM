<!-- claims-lint: allow-file reason="Dataset attribution; license names and corpus counts are citations not product claims" -->
---
title: "AeroBIM dataset attribution"
date: "2026-08-14"
claim_boundary: "Attribution and license hygiene. Open corpora ≠ RF PD+expertise corpus. Not product accuracy. GPLv3 IFC stays out of this MIT tree."
---

# Datasets and attribution

AeroBIM is MIT. Third-party corpora stay under their own licenses. This file is the CC BY / Apache attribution surface. Counts below are **upstream published** figures (cite the source), not AeroBIM measurement.

## Do not put in this repository

| Model / artefact | License | Rule |
| --- | --- | --- |
| IFC-Bench models `4351`, `ettenheim_gis`, `hitos`, `samuel_macalister_sample_house` | GNU GPLv3 | Link only. Not in git, not in distro. Pins: `samples/benchmarks/ifc-bench-v2/IMPORT_PINS.json` |
| LibreDWG | GPL-3 | Do not link |

## AEC-Bench

- Authors / org: Nomic AI
- Paper: [arXiv:2603.29199](https://arxiv.org/abs/2603.29199)
- Code: https://github.com/nomic-ai/aec-bench
- Data: https://huggingface.co/datasets/nomic-ai/aec-bench
- License: Apache 2.0
- Published: 196 tasks, 9 families, three coverage levels (intrasheet / intradrawing / intraproject)
- Compliance-judgment slice: Mushkani, Bérard, Koseki, [arXiv:2607.29058](https://arxiv.org/abs/2607.29058) — 160 tasks / 29 projects (126 Does Not Meet, 26 Meets, 8 Missing Information)
- AeroBIM: inventory smoke `docs/evidence/aec-bench-smoke-latest.json`. Harbor agent **NOT_RUN**. False-pass **SKIPPED**. This is **not** RT-001 (RF PD + expertise conclusion).

## IFC-Bench V2

- Authors / org: Sylvain Hellin et al., TUM Georg Nemetschek Institute
- Data: https://huggingface.co/datasets/sylvainHellin/ifc-bench
- Paper: [arXiv:2605.01698](https://arxiv.org/abs/2605.01698)
- License (QA): CC BY 4.0
- Hugging Face card (retrieved 14.08.2026): 22 projects, 51 IFC, 1 027 QA pairs — https://huggingface.co/datasets/sylvainHellin/ifc-bench
- Paper [arXiv:2605.01698](https://arxiv.org/abs/2605.01698) states 1 027 tasks across **37 IFC models / 21 projects**. Do not blend card and paper counts in one sentence.
- Solihin-adapted classes 1–4; eval-split `eval-split-hellin2026.csv` (514 test / 512 train after leak fix)
- Multidisciplinary models used as **pointers**, not vendored: `west_riverside_hospital` (CC BY 3.0, OpenIFC / Wawan Solihin), `sixty5`, `dental_clinic`, `duplex`, `wbdg_office` (CC BY 4.0), `digital_hub` (MIT, RWTH Aachen E3D)
- AeroBIM: pins + gitignored checkout of QA CSV + duplex/dental (GPLv3 dirs never copied). Deterministic smoke **9/1026** scored. Eval-split **514** stays unmapped NL — not a 514 false-pass figure. Hub extra models (`digital_hub`, `west_riverside`) SSL-timeout from this network; inventory SKIPPED. Smoke: `docs/evidence/ifc-bench-v2-smoke-latest.json`

## GNI BIM Dataset

- Authors / org: Zijian Wang et al., TUM Georg Nemetschek Institute
- Zenodo: [10.5281/zenodo.19722012](https://doi.org/10.5281/zenodo.19722012)
- Code: https://github.com/ZijianWang-ZW/GNI-BIM-Dataset
- License: CC BY 4.0 (models); anonymization scripts MIT
- Published: 224 anonymized IFC (223 parsed), paired AR+STR on 7 of 9 team projects
- Caveat (upstream): student models, as-is — measure rule recall/false-omit, not «product accuracy»
- AeroBIM 14.08.2026 (gitignored `.local/gni-bim`, not in git): **224** header-open, **223** IfcOpenShell-open, **1** oversize skip (`model_6_arc.ifc`, 561838129 B — same unloadable architectural file upstream skipped). AR+STR pairs **7**/9. Evidence [`docs/evidence/open-ifc-stress-2026-08.md`](evidence/open-ifc-stress-2026-08.md) · `content_sha256=d9e0519962837fc7248ff7231aefc433f63a9caa19716a6ebfa054dff128fcca`. Anonymization scripts MIT-pinned, not rewritten: [`docs/evidence/gni-anonymization-pin-2026-08.md`](evidence/gni-anonymization-pin-2026-08.md)

## Official examination IDS (GAU MO «Мособлгосэкспертиза»)

- Publisher: ГАУ МО «Мособлгосэкспертиза»
- Page: https://www.moexp.ru/services/tekhnologii-informatsionnogo-modelirovaniya/
- Hashes / retrieval: `samples/ids/moexp/SOURCE.md`
- This is an approved **state examination** IDS pack. It is **not** a Samolet-signed acceptance profile.

## buildingSMART IDS TestCases

- Publisher: buildingSMART
- License: CC BY-ND 4.0 (unmodified vendored files)
- Path: `samples/ids/buildingsmart-testcases/`
- AeroBIM fail-closed divergences (ifcVersion vs FILE_SCHEMA): `AEROBIM_FAIL_CLOSED_DIVERGENCES.json` · evidence `docs/evidence/ids-fail-closed-2026-08.md`

## What is still missing

Public «российский комплект ПД + фактическое заключение экспертизы» does not exist. Samolet project models under NDA are not here. Those two sentences are the remaining RT-001 / customer-corpus deficit. Everything else in this file was available under a free license and is now cited.
