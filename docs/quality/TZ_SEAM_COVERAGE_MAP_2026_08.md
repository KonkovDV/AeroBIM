<!-- claims-lint: allow-file reason="Coverage map + literature IUA; TZ 90%/SLA/MEP/RT CLOSED as blocked inferences; Checkpoint NO_GO" -->
---
title: "TZ seam coverage map — local NDA rehearsal × literature 2026-08-26"
date: "2026-08-26"
last_updated: "2026-08-26"
status: active
version: "1.0.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: coverage_map_only
detected_count: 0
claim_boundary: >
  Kane IUA over a local owner-disk NDA rehearsal. Entity/property counts are
  not customer findings. Open 2026 benches do not close RT-001/002/003.
  Not product accuracy. Not customer SLA. Not MEP delivered. Not CDE-ready.
  Checkpoint NO_GO. LLM/VLM never write summary.passed (ADR-001).
---

# TZ seam coverage map (26.08.2026)

**Question.** What may a local owner-disk NDA package license for Samolet TechLab Task PD/RD verification, given the August 2026 literature, and what must not be said.

**Method.** Messick (1995) aspects + Kane (2013) Interpretation/Use Argument. Rule classes: Solihin & Eastman (2015). Pack facts are `coverage_map_only` (entity/property presence), not TP/FP. NDA binaries, GUIDs, remark text, and file hashes are not in git.

**Checkpoint:** **`NO_GO`**. `closes_rt001/002/003: false`. `detected_count: 0`.

## 0. Verdict

The pack **supplies carriers** for a coverage map (IFC AR+KR, PD PDFs, EIR/LOD workbook, expertise-remark workbook, calculation binaries). It does **not** supply criterion validity: no dual raters, no κ, no signed appointing-party IDS, no federated MEP IFC, no reinforcing bars, no `NetFloorArea` on IfcSpace. Science from May–August 2026 **tightens** that stop, it does not loosen it.

| Priority | Finding | Licensed speech | Forbidden speech |
|---|---|---|---|
| **P0** | 6 AR IFC, **10 599** `IfcSpace`, **0** with `Qto_SpaceBaseQuantities.NetFloorArea`; sister whole-building AR: **1 339** spaces, **0** area | Export has rooms as objects; area checks are not runnable | «Площади сверены с ТЭП»; TZ tasks 3–4 done |
| **P0** | **62 033** `IfcWall` on those 6 AR; FireRating filled on **3 538** (5.7 %), observed class **EI 45 only**; KR walls sampled: FireRating token **0** | Property often empty; when present it is EI 45, not design-TZ class II / C0, not fixture REI60 | «Огнестойкость проверена»; demo IDS findings = customer defects |
| **P0** | EGCC (arXiv:2607.29058): false-pass **41–52 %**; authors: unsuitable for autonomous approval | Fail-closed + HITL is the licensed architecture | Autonomous approve; EGCC % as AeroBIM score |
| **P0** | LLM-as-judge (arXiv:2606.19544): agreement ≠ Cohen’s κ | Dual human raters remain the gate | «Модель подтвердила findings» |
| **P1** | Ishigaki-IDS-Bench (arXiv:2605.22079): zero-shot Content-pass **27.7–33.1 %**. Ishigaki-IDS-8B (arXiv:2606.08545): validator-pass **0.651**, still a **draft** aid | Human-reviewed IDS draft only | `customer_approved` from an LLM |
| **P1** | DrawingVQA (arXiv:2607.15418): professionals **94.9 %** vs Gemini-2.5-pro **71.7 %**; QTO is a known weak family | VLM advisory; no sheet sign-off | TZ comparison task 1 closed |
| **P1** | buildingSMART IDS **1.0** final (1 June 2024). IDS **1.1** still feedback as of 26.08.2026 | Checking vs audit split | «IDS 1.1 / certified Samolet profile» |
| **P2** | Filename inventory of PD volumes: conventional labels 1–9, 11, 13 on loose PDFs; label **10** in a primary archive; label **12 unseen**. Engine completeness keys `section_code` before `discipline` — numeric `3` is not AR | Structural completeness is a declared-inventory check, not statutory PP-87 | «Комплект по 87-ПП сертифицирован» |

## 1. Construct (what the sponsor asked)

Public TZ v2 remains ТР-1…62 (assistant, DeterminismGate, IFC+IDS, cross-doc, clash, HITL). The sponsor comparison brief (seven intra-project tasks) is closer to AEC-Bench *intra-project* / EGCC constraint checking than to IfcTester-on-a-wall-fixture:

1. PD/RD ↔ AGR sheets (plans, façades, TEP)
2. PD ↔ typical albums / catalogues
3. Layouts OPR / PD / RD (axes, spaces, doors)
4. Layouts ↔ IRD / design TZ / STU
5. AR / KR / fire / technology / MEP sections vs each other
6. Resubmission ↔ outstanding remarks
7. Reinforcement on drawings ↔ calculation maps (Solihin class 4)

Design TZ for the two residential houses states fire resistance **not below II**, constructive class **C0**, TEP areas, and K0/K1/K2 coefficients **without a signed numeric KPI for space-efficiency**. Deterministic RU-AEC extractors scored **0** hits on that table prose (patterns expect REI60 / millimetre walls). Fixture IDS (`FireRating=REI60`) is a **different construct**.

## 2. Pack facts (no project names, no hashes)

Local owner-disk NDA tree, gitignored. Analyze cap **256 MiB** unchanged. 14 IFC analysed with **fixture** IDS/rules; 1 AR IFC over cap = entity inventory only. `summary.passed` observed false. Fixture `issue_count` is **not** a Samolet defect list.

| Carrier | Count (this rehearsal) | Engine consequence |
|---|---|---|
| IFC | 15 (IFC2x3); 1 over analyze cap | Ingest ≠ native RVT/NWD |
| IfcSpace on 6 AR of one PD package | 10 599; **0** NetFloorArea; sampled pset = `Pset_SpaceCommon.Reference` only | SAM-TYP-008 has nothing to read; K0/K1/K2 not measurable |
| IfcSpace on one sister AR | 1 339; **0** NetFloorArea | Same gap |
| IfcWall FireRating (6 AR) | 3 538 / 62 033 nonempty, class EI 45 | Not II/C0; not REI60 |
| IfcReinforcingBar (15 IFC) | **0** | Class 4 / TZ task 7 blocked; wall pset *pitch* ≠ bars |
| MEP IFC (duct/pipe/cable) | **0** | RT-003 OPEN; EIR LOD sheets for OV/VK/EOM exist as **text** |
| `.lir` calculation binaries | present (not parsed) | `calculation_correctness=NOT_IMPLEMENTED` |
| PD filename labels 1–13 | 12 unseen; 10 only in archive members | Not statutory completeness |
| PD «after expertise» | two zip containers (letters + volumes), not a loose PDF tree | Stem-identity revision compare does not apply |
| OEP remarks | one xlsx, discipline tabs | One internal judge; not dual-rater gold |
| EIR appendix 01 LOD | workbook present (AR/KR + MEP disciplines) | Draft predicates possible; **not** `customer_approved` |

Completeness engine, pairing off, discipline codes PZ/AR/KR: **structural pass**. Pairing on: **fail** (this pack is PD; design TZ stage 2 is RD). Default mandatory **KZH** ≠ pack **KR**.

## 3. Seven comparison tasks × Solihin × 2026 benches

| # | Task | Class | 2026 bench | Pack carrier | AeroBIM now | RT |
|---|---|---|---|---|---|---|
| 1 | PD/RD ↔ AGR | 3 + document | DrawingVQA; AEC-Bench intra-project; EGCC | PDF drawings present | Overlay on **fixture**; native DWG missing | 001 open |
| 2 | PD ↔ catalogues | 1–3 | — | Standard / EIR on disk | No native RVT | 002b open |
| 3 | Layouts across stages | 2–3 | AEC-Bench spec–drawing | AR spaces; KR spaces=0; no RD IFC | No area QTO | 001 open |
| 4 | Layouts ↔ IRD / TZ | document | EGCC | Design TZ extracted as notes; engine hits **0** | Cross-doc on fixture | 002 open |
| 5 | AR/KR/PB/MEP | 3 + document | *Buildings* 16(13):2623 | AR+KR IFC; MEP = PDF | Generic clash optional; MEP-CLASH-001 fail-closed | **003 OPEN** |
| 6 | Resubmit ↔ remarks | process | AEC-Bench submittal-like | OEP xlsx + expertise letters in zip | HITL exists; no gold map | 001 open |
| 7 | Rebar ↔ calc maps | **4** | no open RU bench; LIRA BIM is commercial | `.lir` on disk; **0** bars | Declared-source match only | honesty |

## 4. Literature used (August 2026 window)

Only items that change the IUA. Blogs without method are out.

| ID | Work | What it measures | Transfer | Forbidden transfer |
|---|---|---|---|---|
| L-MES | Messick (1995); Kane (2013) | Validity = use of a score | Coverage map ≠ criterion validity | Green tests ⇒ GO |
| L-SOL | Solihin & Eastman (2015) | Rule classes 1–4 | Task 7 is class 4 | Pset pitch = proof of solution |
| L-EGCC | arXiv:2607.29058 | Four-state constraint check; FP 41–52 % | Fail-closed + Missing/Uncertain | Autonomous approval |
| L-DVQA | arXiv:2607.15418; CVPR Findings 2026 | 33 IFC drawings, 92 QA; humans 94.9 % / model 71.7 % | Sheet literacy gap; QTO weak | Those % as AeroBIM |
| L-AEC | arXiv:2603.29199 | 196 agent tasks; Harbor | Inventory only; Harbor **NOT_RUN** | «Closed AEC-Bench» |
| L-IDS-B | arXiv:2605.22079 | NL → IDS XML; Content-pass ≤33 % | Human draft | Approved Samolet IDS |
| L-IDS-M | arXiv:2606.08545 | Verifier-aware 8B; audit-pass 0.651 | Faster drafts, still review | Skip expert |
| L-J1 | arXiv:2606.19544 | LLM-judge ≠ κ | Dual raters | Model as rater |
| L-CLASH | *Buildings* 16(13):2623 (2026) | Detection mature; filter is human | AR↔KR clash rehearsal ≠ delivered | MEP delivered |
| L-IDS-std | bSI IDS 1.0 (2024-06-01); 1.1 feedback (Tomczak 2026-05-14; GitHub milestone 1.1) | Standard vs wishlist | Checking = IfcTester 1.0 | IDS 1.1 final |
| L-CORE | CORENET X IFC-SG Model Checker **[П]** | State pre-check on IFC | Analog: city AGR IDS = RT-002a | Appointing-party EIR is RVT/NWD |
| L-AGR | Moscow CIM AGR self-check mandatory since 29.06.2026 **[П]** | City portal, free | Not our SKU | Sell AGR-check to Samolet |

OSINT for speech (not a pitch): NKP **A.ru / stable** as of **20.03.2026** **[П]** (`ratings.ru` Samolet-RA-200326). Do not say the February «неопределённый» forecast as current. Developer volume rankings (ERZ vs RBC, August 2026) disagree on the square-metre snapshot — **UNVERIFIED**, not used as a score.

## 5. Adversarial triage (KILL / HOLD)

| ID | Attack | Verdict | Brake |
|---|---|---|---|
| RT-SEAM-01 | 10 599 spaces ⇒ area check works | **KILL** | 0 NetFloorArea |
| RT-SEAM-02 | FireRating present ⇒ fire delivered | **KILL** | 5.7 % filled; class EI 45 ≠ II/C0 ≠ REI60 |
| RT-SEAM-03 | Cite the 8/4635 block as the pack rate | **KILL** | Other AR blocks are 5–7 % filled; always EI 45 |
| RT-SEAM-04 | Completeness pass ⇒ PP-87 done | **KILL** | Numeric `section_code`; label 12 unseen; not statutory |
| RT-SEAM-05 | EIR LOD has OV/VK ⇒ MEP delivered | **KILL** | No MEP IFC; RT-003 |
| RT-SEAM-06 | Wall reinforcement pset ⇒ task 7 done | **KILL** | 0 `IfcReinforcingBar`; `.lir` unparsed |
| RT-SEAM-07 | Fixture `issue_count` = Samolet defects | **KILL** | Demo IDS/rules |
| RT-SEAM-08 | LLM IDS from design TZ | **KILL** | Extractor 0 hits; Ishigaki Content-pass ≤33 % |
| RT-SEAM-09 | OEP xlsx = gold | **KILL** | One judge; κ needs two names |
| RT-SEAM-10 | Files on disk = RT-001 CLOSED | **KILL** | Intake `BLOCKED_NO_CUSTOMER_DATA`; no pack_hash in git |
| RT-SEAM-11 | EGCC/DrawingVQA % = product | **KILL** | Different unit, language, illocution |
| RT-SEAM-12 | Ishigaki-IDS-8B audit-pass 0.651 = approved EIR | **KILL** | Draft aid; no `approval` object |
| RT-SEAM-13 | Zip «after expertise» = revision-closed | **HOLD** | Different container shape; not run as closure |
| RT-SEAM-14 | Raise 256 MiB because one AR is over cap | **KILL** | Owner flag only; default stays |

## 6. What this pass does not do

Does not close RT. Does not commit NDA. Does not run Harbor. Does not compute κ. Does not parse RVT/NWD/LIRA. Does not change `AEROBIM_MAX_IFC_BYTES`. Does not set `customer_approved`. Does not write `summary.passed`.

Checkpoint stays **`NO_GO`**.
