---
title: "Sprint 3 scientific and normative search"
date: 2026-08-07
status: search_note
checked: 2026-08-07
claim_boundary: >-
  Literature inventory only. No product accuracy >90%. Do not transfer
  mechanical-drawing results to AEC without caveat. Checkpoint NO_GO.
---

# Sprint 3 scientific / normative search (checked 2026-08-07)

**Purpose:** Short evidence table for Sprint 3 planning — drawing understanding, symbol spotting, normative IFC, and DWG licensing constraints.  
**Budget assumption:** license spend = **$0** for Sprint 3 (ODA/APS not added to dependencies).

**Caveat:** Results on mechanical drawings, generic VQA, or open-bench fixtures **must not** be transferred to AeroBIM product accuracy or RT-001 closure without customer GT + dual adjudication.

---

## Source table

| Source | Link | Type | Task | Applicability to AeroBIM | Limitation |
|---|---|---|---|---|---|
| **ArchPlanVQA** — CAD floorplan visual QA | [ASCE DOI 10.1061/jccee5.cpeng-7571](https://doi.org/10.1061/jccee5.cpeng-7571) | Peer-reviewed (ASCE) | Floorplan VQA on CAD-derived images | Informs **drawing advisory / HITL** lane — not verdict automation | General VLMs ~**33–38%** on task; **HITL required**; not RU expertise remark GT |
| **AECV-Bench** | [arXiv:2601.04819](https://arxiv.org/abs/2601.04819) | Preprint | Drawing understanding benchmark | OCR-strong baseline for sheet text; spatial reasoning weaker | LLM-as-judge + human edge cases; **not** RT-001; do not cite % as product precision |
| **BlueprintSymVL** (Chalmers) | [research.chalmers.se](https://research.chalmers.se/en/project/blueprintsymvl) | Research project / docs | Blueprint symbol understanding with VLMs | Symbol priors for future hybrid drawing lane | **Not ready for autonomous QA**; advisory scaffold only |
| **ArchCAD-400K** (NeurIPS 2025) | [NeurIPS 2025 proceedings](https://proceedings.neurips.cc/) | Peer-reviewed dataset paper | Large-scale CAD symbol spotting | Potential **pretrain / coverage map** for symbols | **Not RU expertise GT**; license check before vendoring; no >90% product claim |
| **buildingSMART IFC** + **ISO 16739** | [buildingSMART IFC](https://www.buildingsmart.org/standards/bsi-standards/industry-foundation-classes/) · [ISO 16739-1](https://www.iso.org/standard/70303.html) | Normative standard / docs | Open BIM interchange | **Required** analyze-path format; IDS/regression axis | Does not supply expertise remark pairs |
| **ODA Drawings SDK pricing** | [opendesign.com/pricing](https://www.opendesign.com/pricing) | Commercial vendor docs | Native DWG read/write SDK | Documents **paid path** if DWG becomes unavoidable | **Sustaining ~$7 500 / $4 500** renew; **not added to deps** — budget = 0 Sprint 3 |
| **GNU LibreDWG** | [gnu.org/software/libredwg](https://www.gnu.org/software/libredwg/) | OSS (GPL-3) | Partial DWG read/write | **Rejected** for MIT product tree | Incomplete R2010+ objects; **GPL-3 incompatible** with AeroBIM MIT distribution |
| **Autodesk APS Model Derivative** | [aps.autodesk.com](https://aps.autodesk.com/) | Commercial cloud API | Cloud DWG→derivative | **Not pursued** — RF legal + confidentiality | Cloud egress; **not a dependency**; not RF-default path |

---

## Cross-cutting findings

| Theme | Implication for AeroBIM |
|---|---|
| VLMs on plans / blueprints | Useful as **advisory priors** with HITL — not Shared-gate automation |
| OCR vs spatial on drawings | Text extraction stronger than layout/spatial QA — aligns with partial OCR degrade path |
| Symbol spotting datasets | Training signal only; **≠** customer expertise adjudication |
| Normative acceptance | **PDF/A + IFC** per ПП РФ 614 framing — DWG is contractor workflow, not regulator default |
| Paid DWG SDK | ODA Sustaining minimum for SaaS native DWG — **deferred** (license budget 0) |
| GPL DWG libs | **Do not vendor** into MIT tree |

---

## Mechanical drawing → AEC transfer warning

Do **not** cite mechanical-drawing VQA / MechVQA / industrial-drawing benchmark numbers as AeroBIM AEC product accuracy. If referenced in conversation:

> «Mechanical-drawing benchmarks measure a different task class; our Sprint 3 fixture corpus is requirements-extraction GT only, checkpoint NO_GO for product precision.»

---

## Sprint 3 decisions locked by this search

| Decision | Rationale |
|---|---|
| No >90% accuracy claims | ArchPlanVQA / AECV show VLMs far below autonomous QA |
| HITL default on drawings | Peer-reviewed floorplan VQA ~33–38% |
| IFC + PDF/A pilot default | Normative + analyze path |
| Native DWG out of scope | LibreDWG GPL + incomplete; ODA not budgeted |
| LLM advisory-only | Cannot change `summary.passed`; live Kimi/Qwen NOT RUN |
| RT-001 | Requires customer expertise corpus — see [`customer-data-request-2026-08.md`](../datasets/customer-data-request-2026-08.md) |

---

## References (repo)

- [`AECV_BASELINE_COMPARE_2_1_2026_08_04.md`](AECV_BASELINE_COMPARE_2_1_2026_08_04.md)
- [`dwg-blocker-memo-2026-08.md`](../dwg-blocker-memo-2026-08.md)
- [`expertise-corpus-scan-2026-08.md`](../datasets/expertise-corpus-scan-2026-08.md)
- [`kimi-vs-qwen-2026-08.md`](../evidence/kimi-vs-qwen-2026-08.md)
