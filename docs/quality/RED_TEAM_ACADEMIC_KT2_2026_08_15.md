<!-- claims-lint: allow-file reason="Academic Red Team; forbidden phrases as validity threats/non-claims; Checkpoint NO_GO" -->
---
title: "Academic Red Team — construct validity, ISO 19650, Solihin classes, KT#2"
date: "2026-08-16"
status: active
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Adversarial validity argument, not a product score. Checkpoint NO_GO.
  Fixture evidence is Messick content/substantive, not criterion validity.
  Not product accuracy. Not MEP delivered. Not CDE-ready. Not native DWG.
  Local pytest count is not the CI pin (N-26).
---

# Academic Red Team (KT#2 window, refreshed 16.08.2026)

**Object:** IUA freeze [`f9389bf`](https://github.com/KonkovDV/AeroBIM/commit/f9389bf) (construct-validity object). Hygiene on 17.08 (readable links, 27/1026 pin, kitchen unpublished) does not reopen the IUA or close RT-001/002/003.  
**Literature companion:** [`ACADEMIC_LITERATURE_TRIAGE_2026_08.md`](ACADEMIC_LITERATURE_TRIAGE_2026_08.md) — August 2026 papers, IDS 1.1 status, ISO 19650-6, LLM-as-judge, clash FP.  
**Question:** which *inferences* from current artefacts are licensed, and which are construct-invalid if spoken at KT#2, to Task 07, or to a seed associate?  
**Checkpoint:** **NO_GO**. `closes_rt001: false`. `closes_rt002: false`. `closes_rt003: false`.

This pass is not another feature list. It is an **interpretation/use argument** (Kane, 2013) over the scores the repository already emits.

## 0. Verdict

Engineering readiness improved (Wave A substitutes, live vertical slice, fail-closed IDS version). **Customer readiness did not change.** Fixture GO ≠ checkpoint GO.

| Lane | Result |
|---|---|
| Construct validity of *customer* claims | **FAIL** — no L3 corpus (OPEN_BENCH_VS_RT001) |
| Construct validity of *fixture* claims | **PASS if labelled fixture_only** |
| ISO 19650 authorization (5.7) | Expert still owns accept/reject; ADR-001 holds |
| Solihin class 4 (“proof of solution”) | **NOT_IMPLEMENTED** (SP 63 = class-1 template) |
| Fundraise / SAFE | **NOT READY** (no entity, no paid pilot) |
| KT#2 speech | Survivable iff NO_GO is first and Wave A is not sold as CLOSED |

## 1. Theoretical frame (what “academic” means here)

Validity is not a property of a tool. It is a property of **an inference from a score to a use** (Messick, 1995; Kane, 2013).

| Source | Claim we take as binding |
|---|---|
| Messick, S. (1995). *Am. Psychol.* 50(9), 741–749. [doi:10.1037/0003-066X.50.9.741](https://doi.org/10.1037/0003-066X.50.9.741) | Six aspects: content, substantive, structural, generalizability, external, consequential. Using a score for a decision it does not support is a validity failure even if the number is reproducible. |
| Kane, M. T. (2013). Validating the interpretations and uses of test scores. *J. Educ. Meas.* 50(1), 1–73. | An Interpretation/Use Argument (IUA) must state the *use*. Our IUA for L1/L2 stops at “engine regression”. The IUA for Task 07 success criteria (precision ≥0.60, time saved ≥20%, CDE-visible BCF) is **not yet licensed**. |
| Cronbach, L. J., & Meehl, P. E. (1955). Construct validity in psychological tests. *Psychol. Bull.* 52(4), 281–302. | Nomological net: 50 IDS / 0 document issues sits in the net of *document well-formedness*, not *Samolet acceptance*. |
| Goodhart, C. (1975/1984); Campbell, D. T. (1979) | When a measure becomes a target it ceases to be a good measure. `tests_passed`, `50/0`, a local pytest count, `macro_f1=0.86` are targets-in-waiting. |
| Saltzer, J. H., & Schroeder, M. D. (1975). The protection of information in computer systems. *Proc. IEEE* 63(9). | Fail-safe defaults: SKIPPED IDS under pilot/production → FAILED. This is a *control* property, not an accuracy property. |
| Leveson, N. (2011). *Engineering a Safer World*. MIT Press (STAMP/STPA). | Safety is a control constraint. `summary.passed` is a Shared-gate constraint (ADR-001), not “the package is fit to build”. |
| ISO 19650-2:2018 cl. 5.6–5.7 | Review / authorize / accept the information model is an **organizational** act. Automated checking may support 5.6.3; it does not replace 5.7 authorization. |
| Solihin, W., & Eastman, C. (2015). Classification of rules for automated BIM rule checking. *Autom. Constr.* 53, 69–82. | Class 1 = explicit data; 2 = derived; 3 = extended structure; 4 = proof of solution. SP 63 template ≠ class 4. |
| Cohen, J. (1960). A coefficient of agreement for nominal scales. *Educ. Psychol. Meas.* 20(1), 37–46; Krippendorff, K. (2018). *Content Analysis* (4th ed.). | RT-001 requires ≥2 adjudicators and κ/α. No κ is computable without a labelled customer corpus. |
| Mehrbod, S. et al. (2019). Beyond the clash. *ITcon* 24, 33–57. | Automated clash tools produce large false-positive mass; κ=0.88 was for *human coding of issues*, not for software precision. |
| Hu, Y., Castro-Lacouture, D., & Eastman, C. M. (2019). Holistic clash detection improvement. *Autom. Constr.* 105, 102832; Lin & Huang (2019) *Appl. Sci.* 9(24), 5324. | Majority of software clashes can be irrelevant. Fixture clearance ≠ MEP coordination. |
| Kondratenko et al., AECV-Bench, [arXiv:2601.04819](https://arxiv.org/abs/2601.04819) §6 | Public floor-plan corpus, raster-only, four classes. Door EM ~0.39 / window ~0.34 even for strong MMLMs. **Demo must not count doors/windows.** |
| buildingSMART IDS 1.0 (1 June 2024) | IDS *checking* = IFC against IDS. IDS *audit* = the `.ids` document itself. XmlIdsDocumentAuditor is the latter. |
| Teece, D. J. (1986). Profiting from technological innovation. *Res. Policy* 15(6), 285–305. | Appropriability: MIT + no entity ⇒ complementary assets (services, labelled pack, HITL) are the only current rent. Not a SKU. |

Internal SSOT: [`OPEN_BENCH_VS_RT001_DECISION_2026_08_04.md`](OPEN_BENCH_VS_RT001_DECISION_2026_08_04.md), [`../evidence/tz-proxy-rehearsal-2026-08.md`](../evidence/tz-proxy-rehearsal-2026-08.md), ADR-001, Claims Lock, [`RED_TEAM_FUNDING_ATTACKS_KT2_2026_08_15.md`](RED_TEAM_FUNDING_ATTACKS_KT2_2026_08_15.md), [`ACADEMIC_LITERATURE_TRIAGE_2026_08.md`](ACADEMIC_LITERATURE_TRIAGE_2026_08.md).

## 2. Interpretation/Use Argument (Kane)

**Claimed score uses that ARE licensed today**

1. “This command produces a non-PASS finding with overlay, provenance, and a structural BCF ZIP on a **fixture** pack.”  
2. “IDS `ifcVersion` vs `FILE_SCHEMA` is fail-closed (BSI case 0101).”  
3. “Capability states that are SKIPPED/MISSING/NOT_VERIFIED do not silently pass.”  
4. “Document-level audit of 50 official `.ids` files found 0 XML/schema issues under AeroBIM’s IDS 1.0 XSD auditor.”

**Claimed score uses that are NOT licensed**

| Intended use (Task 07 / jury / VC) | Why the IUA breaks |
|---|---|
| Product accuracy >90% / TP/(TP+FP)≥0.60 on Samolet | No L3 labels, no dual raters, no `customer_pack_hash` |
| Customer SLA ≤30 min | Fixture wall-clock ≠ agreed pack; Wilson n not defined |
| Time saved ≥20% | No baseline T from named experts |
| “BCF ready for CDE” | File ingest ≠ ISO 19650 information exchange into a named CDE |
| “IDS certified / Samolet profile” | Audit ≠ checking; MOEXP ≠ EIR of the appointing party |
| “MEP delivered” | No signed clearance matrix; HVAC fixture has no tessellation |
| “SP 63 verified” | Template is Solihin class 1 on a covering pset, not class 4 proof |
| “local pytest count ⇒ HEAD fully verified in README” | N-26: CI pin remains 2455 @ `acac02bd` |
| Checkpoint GO | RT-001/002/003 OPEN by construction |

## 3. Messick six aspects × Wave A (substitution map)

Wave A is **content/substantive evidence for the engine**. Treating it as **external/criterion evidence for the customer** is the central academic kill shot (construct-irrelevant substitution).

| Wave A artefact | Messick aspect it *can* support | Aspect it is *sold as* if speech slips | Status |
|---|---|---|---|
| MinStroy survey/geological XSD | Content (intake format exists) | External: “electronic expertise” | **threat** |
| 50 IDS / 0 document issues | Structural (document well-formedness) | External: Samolet profile / IDS 1.1 cert | **threat** |
| Clearance ~30 mm extra-method | Substantive (IfcClash clearance mode runs) | Generalizability: MEP on federated customer IFC | **threat** |
| Clash → our BCF → consume | Substantive (T1 ZIP round-trip) | External: CDE import / ISO 19650 exchange | **threat** |
| SP 63 cover template | Content (a rule-pack *shape*) | Class 4 proof of reinforcement | **threat** |
| local pytest count (not the CI pin) | Structural (code regression on this machine) | Consequential: “production-ready” | **threat** |
| extraction F1 0.86 | External on **fixture corpus only** | External on customer drawings | **threat** |
| Vertical slice overlay | Content + substantive (text-layer path) | Drawing literacy (AECV symbol task) | **mitigated if doors/windows forbidden** |

**Consequential validity:** publishing L1/L2 as customer accuracy would be an unethical *use* of the score (Messick’s consequential aspect), not a marketing preference. Claims Lock exists to block that use.

## 4. ISO 19650 / IDS: process vs artefact

ISO 19650-2 distinguishes:

- **EIR** — appointing party information requirements (Samolet). **Absent.** RT-002.  
- **BEP** — appointed-party delivery plan. **Absent.**  
- **5.6.3 QA check** — may be partly automated (IDS checking of IFC). **Fixture only.**  
- **5.7 authorize/accept** — human. ADR-001: VLM cannot set `summary.passed`.

buildingSMART’s own split: **IDS checking** (IFC ⊨ IDS) vs **IDS audit** (the `.ids` file is a valid specification). `XmlIdsDocumentAuditor` is audit. IfcTester on MOEXP 389/389 executable **0 pass** is checking against a *public organ* spec on a *fixture* IFC — still not the appointing-party EIR.

Public MOEXP IDS = information requirements of an expertise body. That is closer to a *third-party* IR than to Samolet’s EIR. ISO 19650 does not license the substitution.

## 5. Solihin–Eastman classes (what we actually implemented)

| Class | Meaning | AeroBIM now | Honest sentence |
|---|---|---|---|
| 1 | Explicit properties / existence | IDS exists/pset, wall width quantity, SP 63 20 mm covering pset | Implemented on fixtures |
| 2 | Simple derived values | Bounded quantity algebra | Fixture-only |
| 3 | Extended structure / topology | Planted clash + clearance extra-method; Analyze still `detect()` self-clash | Engine rehearsal |
| 4 | Proof of solution | Independent calc / reinforcement / fire engineering | **NOT_IMPLEMENTED** |

Saying “проверка по СП 63” maps a class-1 template onto a class-4 construct. That is construct underrepresentation (Messick content aspect fails).

## 6. Measurement theory: why RT-001 is not a search problem

Pilot protocol already pre-registers Wilson intervals, dual adjudication, and κ/α ([`../pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md`](../pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md)). Until two named adjudicators label a frozen pack:

- Precision/recall are **undefined**, not “low”.  
- Cohen’s κ and Krippendorff’s α cannot be computed.  
- Held-out FN is not identified.  
- Unit of analysis (finding vs sheet vs section vs project) is not locked with the customer.

Open benches (AEC-Bench inventory 196, GNI 224/223, IFC-Bench smoke 27/1026) occupy Messick *content* of “there exist IFC files”. They do not occupy the *criterion* of “Russian PD/RD + expertise remarks”. AECV-Bench §6 states the corpus limits in the paper itself.

Clash literature is the same pattern: detection recall of *geometric overlap* ≠ precision of *coordination-relevant issues* (Mehrbod 2019; Lin & Huang 2019; Hu et al. 2019). Duplex AABB 654 pairs are inventory, not clashes.

## 7. Fail-closed as control, not as quality

Saltzer–Schroeder fail-safe defaults and Leveson STAMP agree on one point: the safe state when a check cannot run is **do not authorize**. AeroBIM maps that onto `summary.passed=false` when IDS is SKIPPED under pilot/production, and when IFC4X3 meets an IFC4 IDS.

This **increases** false FAIL relative to a silent skip. That is the opposite of a product-accuracy boast. Jury speech: “we refuse to turn missing evidence into green.” Not: “we catch all errors.”

IFC4X3 row of the release matrix (`ids=failed`, extra `AEROBIM-IDS-IFC-VERSION`) is the exhibit. Do not alias `IFC4`↔`IFC4X3`↔`IFC4X3_ADD2`.

## 8. Appropriability and GTM (Teece, not a pitch)

LICENSE = MIT. Complementary assets that could capture value: labelled customer pack, dual-rater protocol, HITL workflow, closed-contour operations. None of these are in git as customer artefacts. Default speech until a paid pilot: **MIT + services**. Open-core (ADR-002) is a boundary discussion, not a current SKU. Asking for a round with no entity fails Teece *and* ordinary corporate law.

Zacua ConTech 2026 (n=140): team 83%, differentiation 50%, traction 48%. Traction cell = 50 cold / 0 slots. Academic reading: adoption constraint, not a missing port.

## 9. Attack tree (validity threats)

IDs continue the funding series so speech packs stay aligned.

| ID | Threat (Messick/Kane) | Exhibit in repo | Brake |
|---|---|---|---|
| RT-ACAD-01 | Construct substitution: IDS audit → certified profile | 50/0 document issues; `customer_pack_hash=null` | FAQ + Wave A RT |
| RT-ACAD-02 | Construct substitution: clearance → MEP | extra-method; HVAC no tessellation | `mep_system_clash=NOT_VERIFIED` |
| RT-ACAD-03 | Construct substitution: XSD intake → expertise | MinStroy survey/geological only | `closes_rt001: false` |
| RT-ACAD-04 | Construct substitution: BCF ZIP → ISO 19650 exchange | own consume; `cde_import=NOT_VERIFIED` | HTML “Not a CDE import” |
| RT-ACAD-05 | Construct underrepresentation: SP 63 class 1 as class 4 | covering pset 20 mm | `calculation_correctness=NOT_IMPLEMENTED` |
| RT-ACAD-06 | Goodhart: pytest count as quality | local pytest ≠ CI pin | N-26; do not copy |
| RT-ACAD-07 | Generalizability: fixture F1 0.86 as product | extraction eval corpus | claim_level fixture |
| RT-ACAD-08 | Task contamination: AECV doors/windows as demo | arXiv:2601.04819 Table 1 | rehearsal forbids it |
| RT-ACAD-09 | Consequential: hide NO_GO | pitch 05.08 | pitch 15.08 leads with NO_GO |
| RT-ACAD-10 | IUA overreach: Harbor 160 as false-pass % | inventory 196; NOT_RUN | SKIPPED until 17.08 |
| RT-ACAD-11 | Ecological: wall-guid HTML as overlay demo | no `#kt2-overlay` | live CLI slice |
| RT-ACAD-12 | ISO 19650 5.7: model sets Published | ADR-001 | VLM cannot flip passed |
| RT-ACAD-13 | Inter-rater: invent κ | no dual labels | protocol exists, numbers do not |
| RT-ACAD-14 | Clash FP: AABB/inventory as delivered clash | duplex 654 | NOT_VERIFIED |
| RT-ACAD-15 | Appropriability: MIT = nothing to sell | LICENSE | services speech, not SAFE |
| RT-ACAD-16 | Consequential: GitHub reads as LLM dump | README «План ИИ»; executor prompt; Cursor UUIDs | **MITIGATED 15–16.08** — session dumps off public tree; product VLM/ADR-001 kept; `closes_rt*` unchanged |
| RT-ACAD-17 | Construct substitution: IFC-Bench QA → expertise act | Hellin et al. 2026 (arXiv:2605.01698); 27/1026 smoke | `open_bench_only`; RT-001 OPEN |
| RT-ACAD-18 | Construct substitution: AEC-Bench inventory → agent reads Samolet PD | Mankodiya et al. 2026 (arXiv:2603.29199); Harbor NOT_RUN | Do not name inventory as a run |
| RT-ACAD-19 | VLM-as-judge replaces dual raters | arXiv:2606.19544 κ-deflation | `PrecisionClaim.publishable` only |
| RT-ACAD-20 | Stakes signaling on advisory prompts | arXiv:2604.15224 | Model text must not say the pilot depends on the model |
| RT-ACAD-21 | Geometric hit → coordination issue | *Buildings* 16(13):2623 (2026) | `mep_system_clash=NOT_VERIFIED` |
| RT-ACAD-22 | IDS 1.1 / «certified» as current standard | bSI feedback May 2026; IDS 1.0 remains final | Audit ≠ checking ≠ Samolet EIR |
| RT-ACAD-23 | «ISO 19650 compliant» without part number | ISO 19650-6:2025 is H&S sharing, not 5.7 | ADR-001; Part 6 not implemented |
| RT-ACAD-24 | Planner n=111 spoken as measured 0.60 | Wilson / Brown–Cai–DasGupta 2001 | `protocol_planning` only |
| RT-ACAD-25 | BCF ZIP → OpenCDE Foundation + named CDE | BCF-API 3.0 requires Foundation | T2 `NOT_VERIFIED` |

## 10. Tracker (Dmitry) mapping — academic reading of the six tasks

| # | Tracker ask | Validity-correct delivery | Invalid delivery |
|---|---|---|---|
| 1 | Product to KT#2 20.08 | Live slice + NO_GO + limits | Wall-guid as overlay; GO language |
| 2 | IFC2x3/4/4X3 table | Elements, fired rules, p50/p95, refusals, `passed=false` | Timing as SLA; findings as accuracy |
| 3 | Datasets | Smoke + documented skips; RT stay OPEN | Open F1 as RT-001 CLOSED |
| 4 | Burnaev demo link | CLI + claim boundary; academic questions | “AI understands drawings” |
| 5 | 3–5 scheduled demos | KPI restated; git demos = 0 | 50 more cold emails |
| 6 | Open-source monetization | MIT + services until paid pilot | Invent SKU / SAFE |

## 11. What this pass changes in the repo

- IFC matrix renderer: `summary.passed`, suite n/python, tracker-paste table (Dmitry #2).  
- Honesty lock test on **this file** (`closes_rt001: false` etc.).  
- Live re-run of the schema-suite on CPython 3.12.10, n=20: IFC2X3 findings 5 / IFC4 4 / IFC4X3 6; all `summary.passed=false`. Clash on these wall fixtures is **failed** (`AssertionError` from IfcClash geom init) — listed as a refusal, not a silent pass.  
- Open-corpora **smoke** (SHA pins `pins_ok=true`, 7 regression cases), not Harbor 160.  
- Voice hygiene 15.08: strip meta-agent prompts and Cursor review UUIDs. Do **not** treat that as closing RT-001. Product advisory VLM stays.

## 12. Human-only (cannot be closed by coding)

Legal entity; paid pilot / LOI; Samolet pack + two adjudicators; Renga IFC as-is; named CDE import target; video 19.08; bSI Validation account; Burnaev/Mikhail minutes; domain-founder CV. Inventing any of these is a consequential-validity failure.

## 13. One sentence for the jury

> We have a fail-closed, evidence-linked checker whose *fixture* scores are reproducible; we do not yet have a Kane-licensed argument that those scores mean Task 07 success on a Samolet package. August 2026 literature (AEC-Bench, ifc-bench v2, LLM-as-judge, clash-management reviews) **tightens** that boundary rather than relaxing it. Checkpoint stays **NO_GO** until the labelled pack exists.

Formula: not more functions → more evidence → narrower scope → real pack → measured effect → then integration.

## 14. Literature refresh (16.08)

Full map, citations, and P0–P2 triage: [`ACADEMIC_LITERATURE_TRIAGE_2026_08.md`](ACADEMIC_LITERATURE_TRIAGE_2026_08.md). That pass does **not** close RT-001/002/003 and does **not** treat Harbor-not-run as a score.
