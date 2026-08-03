---
title: "Source verification report — research contour"
date: 2026-08-04
status: active
version: "1.0.0"
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

**What was opened:** arXiv PDF https://arxiv.org/pdf/2601.04819 (full text this session).

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
| Five-field macro (Door/Window/**Space**/Bedroom/Toilet) | **0.4325** |
| **Four-field macro (paper-comparable)** | **0.5064** |

Per-field live: Door 0.231 / Window 0.137 / Space 0.137 / Bedroom 0.846 / Toilet 0.812.

**Direct answer:** On the paper’s four classes, live Qwen **0.51** sits with Gemini 3 Pro’s published **0.51** mean — harness is **not** obviously broken. The headline **0.43** is lower mainly because AeroBIM averages a fifth field (**Space**, exact 0.137) that Table 1 does not use. Door/Window remain weak vs Bedroom/Toilet — **agrees** with the paper’s symbol-vs-text gradient. Residual gaps vs published Gemini Door/Window (0.39/0.34 vs our 0.23/0.14) are model/prompt/resolution, not “invalid scoring.”

**Consequence:** Always publish **both** macros; never defend 0.43 as “paper mean.” Update slides/evidence (`macro_exact_match_rate_paper_four_fields`).

**Not found in paper:** exact pixel resolution / resize policy for their API runs (protocol says unified prompts via OpenRouter; tile policy not specified numerically).

---

### 2.2 Cost / resolution for multimodal

**Measured in-repo (ops v1.9):** full sheet prompt **2184**; long-side 1024/512/256 → **1065/297/105** (≈quadratic). Completion ≈**47** with thinking off.

**Literature this pass:** Qwen-VL tile/tokenization papers **not opened** here → stamp readability vs px remains **UNVERIFIED** in literature; engineering answer stays empirical (next: stamp-crop matrix at 512/1024).

**Consequence:** Document measured tokens in grant ops (done). Do not claim a literature “minimum readable stamp px” without a VERIFIED source.

**Not found:** peer-measured “stamp text readable at N px” for AEC title blocks.

---

### 2.3 LLM → machine-readable requirements

**VERIFIED:** Perov et al. ICDMW 2025 DOI `10.1109/icdmw69685.2025.00203` (Crossref) — tool-augmented LLM→IDS style pipeline; prior errata quotes 138 reqs / high XML validity / repair-loop ablation (numbers from earlier baseline note — re-confirm abstract before deck use if citing exact %).

**PARTIAL / prior:** Ishigaki-IDS arXiv:2606.08545, Ishigaki-IDS-Bench 2605.22079, P4IR 2606.22402 (listed in 2026-08-03 errata; bodies not re-opened this session).

**Direct answer:** Peer pipelines with numbers exist; AeroBIM must not claim uniqueness. Russian СП/ГОСТ/СанПиН-specific published end-to-end compilers: **none verified this pass** → gap is real and should be stated as such for RT-002 honesty.

**Consequence:** Keep `LLM_TO_IDS_BASELINE_2026_08_03.md`; TZ wording = advisory + HITL + compare to Perov/Ishigaki, not “first compiler.”

---

### 2.4 Evaluation protocols (hybrid vs dual labeling)

**VERIFIED from AECV PDF:** automatic match + LLM-as-a-judge + human adjudication on edge cases for QA; counting uses exact-match + MAPE.

**Not opened:** head-to-head studies of hybrid vs dual-expert κ with cost ratios for AEC counting → **UNVERIFIED**.

**Cohen κ in AEC object counting:** no primary source opened this pass → do not invent thresholds.

**Consequence:** WP-07 may keep Wilson + dual expert for RT-001; LLM-judge stays triage-only (already Claims Lock). Cost claim “4× cheaper” **forbidden** until VERIFIED study.

---

### 2.5 Document / image injection

**Not opened** primary papers this session → mitigations with measured efficacy remain **UNVERIFIED**.

**Consequence:** Keep fail-closed HybridRouteGate + stamp crop as engineering controls; do not cite fictional ASR numbers.

---

### 2.6 Personal data on drawings

**GOST 2.104** FIO in title block: domain knowledge; Roskomnadzor methods / court precedents for cloud PD on PD packages: **UNVERIFIED** this pass (no official method page opened).

**Consequence:** Stamp-region crop remains product necessity for PII; cite GOST practice, not invented RKN “approved method.”

---

### 2.7 RF regulatory contour (priority)

| Topic | Status | Finding |
|---|---|---|
| ПП **331** ТИМ | **VERIFIED** (Garant text opened via fetch) | IM required for listed cases; housing/shared-construction expansions via later acts (2357 etc.) — use Garant/official text, not blogs alone |
| ЕСИМ timelines | **PARTIAL** | Secondary industry articles only this pass |
| ФЗ-309 / УКЭП for PD | **UNVERIFIED** this pass | Do not invent |
| ИИ law | **VERIFIED** existence | **243-ФЗ** published 26.07.2026 on publication.pravo.gov.ru (doc 0001202607260003). Secondary analyses (opened): **not** universal mandatory labeling of all AI text; audio/visual warning *possibility* for large platforms; main force **01.09.2026**, art. 8–10 / marking delayed (**01.03.2027** per consultant draft text). March Минцифры longer draft ≠ enacted law |
| Реестр российского ПО + foreign open weights on RF cloud | **PARTIAL** | Consulting/legal explainers (opened): OSS allowed if exclusive rights Russian and no critical foreign proprietary dependency; Yandex Cloud helps localization but does **not** auto-qualify. **No** opened Минцифры FAQ that explicitly blesses “foreign Qwen weights via Studio API” as registry-safe |

**Direct answer for positioning before KT#3:**  
(1) Do not pitch “fully sovereign AI” if runtime depends on foreign foundation weights through a cloud API — that is a **registry risk**, not a code bug.  
(2) Prefer: *deterministic AeroBIM core (MIT) + optional advisory LLM; RF hosting; on-prem Studio path for CONFIDENTIAL; open weights as replaceable adapter.*  
(3) Marking: AeroBIM’s `ai_generated` remark marking is **good product hygiene** and aligns with spirit of transparency, but do **not** claim it is mandated by 243-ФЗ for all B2B JSON.

**Consequence:** Update decks that still echo the March draft; legal memo before KT#3 on registry path (PARTIAL → counsel).

---

### 2.8 Industrial deployments with measured results

**Not opened** independent measured case studies this pass. Structured AI blog claims “400+ issues in a 1,000-page set” — **vendor claim**, methodology not peer-reviewed → label **PARTIAL/vendor**.

**Consequence:** No competitor-named accuracy slides for organizers; practice comparison only.

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

---

## Limits respected

- Checkpoint **NO_GO**; RT-001/002/003 unchanged by literature.
- No product accuracy uplift from foreign benches.
- Empty C.3 forbidden — filled above.
