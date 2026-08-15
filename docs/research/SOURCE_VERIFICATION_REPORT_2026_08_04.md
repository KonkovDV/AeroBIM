---
title: "Source verification report — research contour"
date: 2026-08-04
status: active
version: "1.1.0"
claim_boundary: >-
  Verification protocol output. Checkpoint remains NO_GO.
  Live AECV stays open_bench_only. Foreign numbers are not AeroBIM product KPIs.
  C.3 is mandatory and non-empty.
---

# Source verification report — 2026-08-04

**Role:** researcher-verifier. Audit first, then gap-fill.  
**Git scope:** `AeroBIM` `main`. External `research.md` / `представление.txt` are **not** in this tree (confirmed by search); claims about them apply to operator copies.

---

## Part A — bibliography audit

See also: [`CITATION_ERRATA_2026_08_04.md`](CITATION_ERRATA_2026_08_04.md).

| Link / claim | Where | Status | Action |
|---|---|---|---|
| `10.1016/j.aei.2025.103676` | External research notes / RT docs | **VERIFIED** | Keep (BuildThemis / AEI 68) |
| `10.1016/j.aei.2026.103676` | Twin of above | **FABRICATED** | Delete; Crossref 404 |
| `10.1016/j.aei.2026.104735` | `docs/docs.md` | **VERIFIED** | Keep |
| Structured AI $4.2M / FCVC / YC / Sequoia Scout | External `представление.txt` | **VERIFIED** | Keep with primary URL dated 2026-06-11 |
| AECV-Bench arXiv:2601.04819 | `docs/docs.md`, evidence | **VERIFIED** | Keep; opened abs + PDF |
| AEC-Bench arXiv:2603.29199 | `docs/docs.md` | **VERIFIED** (operator + abs id) | Keep |
| MechVQA arXiv:2605.30794 | `docs/docs.md` | **VERIFIED** (operator prior) | Keep |
| BRAVO mediatum 1854636 | operator prior | **VERIFIED** (operator) | Keep |
| Arch-Eval Wu et al. | `docs/docs.md` | **VERIFIED** | DOI 10.1038/s41598-025-98236-0 |
| IFC-Bench Hellin | evidence tools | **VERIFIED** dataset | Prefer HF v2 + GitHub; peer venue wording PARTIAL |
| Perov ICDMW 2025 | `docs/docs.md`, baselines | **VERIFIED** | Crossref OK |
| Madireddy Electronics 2025 | `docs/docs.md` | **VERIFIED** | Crossref OK |
| Wang JCEM 2026 | `docs/docs.md` | **VERIFIED** | Crossref OK |
| Mirhosseini BRI 2026 | `docs/docs.md` | **VERIFIED** | Crossref OK |
| AutCon 2026.107043 | `docs/samolet.md` | **VERIFIED** | Crossref OK |
| НРС «исключение до 2 лет» | prior errata | **UNVERIFIED** | Still do not put on slides |

**File patch list:** remove any `2026.103676`; sync external research pack with VERIFIED AECV/AEC-Bench/MechVQA/BRAVO; fix presentation law wording for 243-ФЗ vs March draft; add four-field AECV compare note in evidence.

---

## Part B — open questions

### 2.1 AECV-Bench baselines (highest priority)

**What was opened:** arXiv PDF https://arxiv.org/pdf/2601.04819 (full text, 04.08.2026).

**Paper numbers (Table 1, object counting, mean over Door/Window/Bedroom/Toilet):**

| Model | Mean EM | Door | Window | Bedroom | Toilet |
|---|---:|---:|---:|---:|---:|
| Gemini 3 Pro | **0.51** | 0.39 | 0.34 | 0.89 | 0.82 |
| GPT-5.2 | 0.49 | 0.28 | 0.27 | 0.91 | 0.76 |
| Claude Opus 4.5 | 0.42 | 0.16 | 0.16 | 0.91 | 0.76 |
| Qwen3-VL-8B Instruct | 0.39 | 0.09 | 0.10 | 0.76 | 0.81 |

Paper abstract: strongest symbol counting often **0.40–0.55** mean EM; OCR QA up to **~0.95**. MAPE Table 2: Gemini mean MAPE **16.0%** (Door 15.0 / Window 20.4).

**AeroBIM live (Yandex `qwen3.6-35b-a3b`, 117 plans):**

| Aggregation | Exact-match |
|---|---:|
| **Five-field macro (Table 1 / upstream `mean_accuracy`)** | **0.4325** |
| Four-field macro (paper prose / heatmap display — reference) | 0.5064 |

Per-field live: Door 0.231 / Window 0.137 / Space 0.137 / Bedroom 0.846 / Toilet 0.812.

**Direct answer (errata):** Table 1 published means align with the **five-field** metric (Space included). Live Qwen **0.4325** sits above Claude Opus 4.5 **0.42** and open GLM **0.39**, below Gemini **0.51** / GPT-5.2 **0.49**. The four-class **0.51** must **not** be compared to Table 1. Door/Window remain weak vs Bedroom/Toilet — **agrees** with the paper’s symbol-vs-text gradient. Scorer reproduces Table 1 within |Δ|≤0.02 on the five-field metric.

**Consequence:** Publish **`macro_extended`** as headline vs Table 1; keep four-class as reference only.

**Not found in paper:** exact pixel resolution / resize policy for their API runs (protocol says unified prompts via OpenRouter; tile policy not specified numerically).

---

### 2.2 Cost / resolution for multimodal

**Measured in-repo (ops v1.9):** full sheet prompt **2184**; long-side 1024/512/256 → **1065/297/105** (≈quadratic). Completion ≈**47** with thinking off.

**Literature (v1.1):** Qwen2-VL arXiv:2409.12191 Table 7 **opened** — dynamic ~1924 tok ≈ top InfoVQA/OCRBench; fixed 64→3136 shows large OCR/InfoVQA swings. Stamp AEC title-block “min readable px” still **UNVERIFIED**.

**Detail:** [`RESEARCH_QUESTIONS_2_2_TO_2_8_2026_08_04.md`](RESEARCH_QUESTIONS_2_2_TO_2_8_2026_08_04.md) §2.2.

---

### 2.3 LLM → machine-readable requirements

**VERIFIED:** Perov et al. ICDMW 2025 DOI `10.1109/icdmw69685.2025.00203` (Crossref OK). Abstract numbers: 138 reqs; with repair **100 %** XML / **94.1 %** XSD / **77.5 %** Solibri-executable; without repair XML/XSD **62.8 % / 59.6 %**. Full IEEE PDF not opened this pass → tables PARTIAL until PDF.

**PARTIAL / prior:** Ishigaki-IDS, Ishigaki-IDS-Bench, P4IR; TUM Li F1 0.976 (thesis).

**Consequence:** Keep `LLM_TO_IDS_BASELINE_2026_08_03.md`; no uniqueness claim. РФ СП/ГОСТ end-to-end compiler still **not found**.

---

### 2.4 Evaluation protocols (hybrid vs dual labeling)

**VERIFIED from AECV PDF:** counting exact-match+MAPE; QA auto + LLM-judge + human edge cases.

**VERIFIED adjacent:** ChartMuseum — judge cost ~**$0.20**/run; human **93 %** vs best model **63 %** (not AEC counting).

**Still UNVERIFIED:** AEC dual-expert κ + hybrid cost ratio → forbid “4× cheaper.”

---

### 2.5 Document / image injection

**PARTIAL→anchored:** MPI 4D taxonomy DOI `10.1109/qpain69676.2026.11545895` (≤75 % dimensional coverage claim; ~7.3 % classes documented). CSA note: typographic IPI peak ASR **64 %** (stealth). ARGUS CVPR 2026 = qualitative steering defense. No AeroBIM-measured ASR.

**Consequence:** HybridRouteGate + stamp crop; no invented defense %.

---

### 2.6 Personal data on drawings

**VERIFIED:** RKN order **140** (19.06.2025) + PP **1154** (01.08.2025) methods/rules for depersonalization (Garant / Denuo / privacy-advocates opened).

**PARTIAL:** title-block FIO as common PD practice; no court case opened for “AR PDF in cloud VLM.”

**Consequence:** Stamp crop = minimization hygiene; not “RKN-approved method for drawings.”

---

### 2.7 RF regulatory contour (priority)

| Topic | Status | Finding |
|---|---|---|
| ПП **331** ТИМ | **VERIFIED** (Garant) | IM required for listed cases |
| ЕСИМ timelines | **PARTIAL** | Secondary only |
| **309-ФЗ** | **VERIFIED** primary kremlin.ru/acts/bank/52239 | Force **01.03.2026**. Art. 55.5-1 parts 15–16 = SRO notifications / negative-expertise reporting — **not** “UKЭП mandate text” |
| УКЭП vs ИУЛ | **VERIFIED** letter existence | Минстрой **30.01.2026 № 4420-КМ/14** (Consultant/Garant): ИУЛ ≠ УКЭП; unsigned PD not accepted as e-document for expertise. Cite **63-ФЗ + letter**, not “309 ч.16 = УКЭП” |
| ИИ law **243-ФЗ** | **VERIFIED** existence | ≠ March draft; marking delayed per prior secondary |
| Реестр + foreign weights on Studio | **PARTIAL** | Do not pitch fully sovereign multimodal |

**Consequence:** Fix blog-derived 309↔UKЭП conflation before KT#3; registry counsel still required.

---

### 2.8 Industrial deployments with measured results

**VERIFIED peer:** MDPI Buildings `10.3390/buildings16040719` — 95.8 % / 98.3 % / −90 % effort (State Grid HITL); domain caveat (CN power; EN transfer 79.2 %).

**PARTIAL:** INFRA-M/Editorum 5240 m² (−72.1 % labor); IJIRMPS SEVEN/ACC (−45 % turnaround).

**VENDOR:** Optellix 85 %, AI-BOB “days→minutes”, Structured AI “400+ issues” — label vendor.

**Detail:** [`RESEARCH_QUESTIONS_2_2_TO_2_8_2026_08_04.md`](RESEARCH_QUESTIONS_2_2_TO_2_8_2026_08_04.md) §2.8.

---

## Part C — summary

### C.1 Changes plan before KT#3 (3–21 Sep)

1. Always report AECV **four-field** macro beside five-field; fix any deck that only shows 0.43 vs “paper 0.51.”
2. Delete FABRICATED DOI `2026.103676` from operator research packs.
3. Legal/positioning note: 243-ФЗ ≠ March draft; registry story must not overclaim foreign-weight Studio.
4. Stamp-crop resolution matrix (engineering) — literature gap remains.
5. Ledger vs billing gap for open-bench CLI (ops already flagged).

### C.2 What confirms existing choices

- Claims Lock / `open_bench_only` — paper itself says counting unsolved at 0.4–0.55.
- Bedroom/Toilet ≫ Door/Window gradient — matches AECV PDF.
- Deterministic sign-off + advisory AI — matches paper’s HITL/tool-augmented recommendation.
- Structured AI fundraise claim — VERIFIED; usable in investor-facing text with citation.
- Thinking-off + region-crop economics — measured in-repo; paper motivates drawing-literacy limits.

### C.3 What contradicts existing choices (**required; non-empty**)

1. **Metric framing:** Publishing five-field **0.43** next to paper means **without** disclosing Space inflation **contradicts** “harness-honest” Claims Lock. Four-field **0.51** is the fair compare — and it **weakens** the narrative that we are far below frontier on the paper’s own axes.
2. **“Russian AI stack” rhetoric vs Qwen-on-Studio:** If materials imply registry-ready sovereign multimodal because the cloud is Yandex, that **overreaches** PARTIAL legal sources: foreign open weights + API dependency remain an expert-review risk. Positioning must separate *core product* from *optional foreign-weight advisory*.
3. **If decks still cite March Минцифры mandatory universal AI labeling:** that **contradicts** enacted **243-ФЗ** as summarized in opened secondary + pravo publication record. Update before mentor/investor sends.
4. **LLM→IDS “greenfield” tone:** Perov/Ishigaki existence **contradicts** any uniqueness claim; baselines must be cited.
5. **Size-gate myth for AECV 400s:** earlier “≲10 KB rejected” **contradicted** by WEBP-as-JPEG finding — already corrected in code/docs; any leftover ops text must not revive the false gate.
6. **309-ФЗ «ч.16 = УКЭП»:** industry blogs **contradict** kremlin primary text (parts 15–16 = NRS notifications). UKЭП posture = **63-ФЗ + Минстрой 4420-КМ/14**, co-timed with 01.03.2026 force date — not the wording of 55.5-1(16).

---

## Limits respected

- Checkpoint **NO_GO**; RT-001/002/003 unchanged by literature.
- No product accuracy uplift from foreign benches.
- Empty C.3 forbidden — filled above.
