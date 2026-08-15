---
title: "Citation errata — source verification pass"
date: 2026-08-04
status: active
version: "1.0.0"
claim_boundary: >-
  Bibliography hygiene only. Does not change Checkpoint NO_GO.
  Do not cite UNVERIFIED/FABRICATED links. research.md is not in this git tree.
---

# Citation errata — 2026-08-04

**Protocol:** status ∈ {`VERIFIED`, `PARTIAL`, `UNVERIFIED`, `FABRICATED`}.  
**Repo fact:** there is **no** `research.md` and no `представление.txt` in `AeroBIM` git on `main`. External operator docs must still be scrubbed; this errata covers **in-repo** mirrors + known external claims.

## Priority collisions / fabricated twins

| Citation | Where expected | Status | Action |
|---|---|---|---|
| `10.1016/j.aei.2025.103676` | External `research.md` (not in git); cited in Red Team notes | **VERIFIED** DOI / **PARTIAL** if wrong title attached | Keep DOI. Correct title/authors: Shi/Solihin/Yeoh, *…automated code **compliance** of building regulations*, AEI 68(B), BuildThemis — not a bridge-VLM or “code checking in AEC” alias |
| `10.1016/j.aei.2026.103676` | Same twin pattern (year digit only) | **FABRICATED** | **Delete everywhere.** Crossref HTTP **404**. Elsevier article numbers are not reused across years with a year-digit edit |
| `10.1016/j.aei.2026.104735` | `docs/docs.md`, prior errata | **VERIFIED** | Keep. Crossref 2026: Zentgraf/Hagedorn et al., *A BIM-based framework for automated building code extraction…* |

## Non-academic claim (operator materials)

| Claim | Status | Evidence opened |
|---|---|---|
| Structured AI raised **$4.2M** seed ~June 2026 with FCVC lead + YC / 20VC / Cherry / Sequoia Scout | **VERIFIED** | Company post 2026-06-11 https://getstructured.ai/blog/structured-ai-4-2m-seed-round/ ; ENR coverage linked from that post; Dealroom/TheSaaSNews secondary. `представление.txt` not in git — if claim lives only off-repo, sync wording to these sources (include Zero Prime / Transpose if listing full syndicate). |

## Previously PARTIAL → upgraded this pass

| Work | Status | Primary |
|---|---|---|
| Arch-Eval (Wu et al. 2025) | **VERIFIED** | https://doi.org/10.1038/s41598-025-98236-0 · PMC12008193 · Sci Rep 15:13485 |
| IFC-Bench (Hellin) | **VERIFIED** (dataset) / **PARTIAL** (peer venue wording) | GitHub archived v1 https://github.com/sylvainHellin/ifc-bench ; HF v2 https://huggingface.co/datasets/sylvainhellin/ifc-bench ; related paper arXiv:2605.01698. Prefer “Hellin IFC-Bench dataset” over inventing a single journal citation. |
| AECV-Bench | **VERIFIED** (operator prior + re-opened) | arXiv:2601.04819 PDF opened 04.08.2026 |
| AEC-Bench | **VERIFIED** (operator prior; not re-fetched body) | arXiv:2603.29199 |
| MechVQA | **VERIFIED** (operator prior) | arXiv:2605.30794 |
| BRAVO | **VERIFIED** (operator prior) | mediatum.ub.tum.de/doc/1854636 |

## In-repo bibliography sample (Crossref 04.08.2026)

| DOI / id | File(s) | Status |
|---|---|---|
| `10.1109/icdmw69685.2025.00203` | `docs/docs.md`, research baselines | **VERIFIED** |
| `10.3390/electronics14112146` | `docs/docs.md` | **VERIFIED** |
| `10.1061/jcemd4.coeng-18122` | `docs/docs.md` | **VERIFIED** |
| `10.1080/09613218.2026.2637965` | `docs/docs.md`, architecture | **VERIFIED** |
| `10.1016/j.autcon.2026.107043` | `docs/samolet.md` | **VERIFIED** |
| arXiv:2601.04819 / 2603.29199 / 2605.30794 | `docs/docs.md` | **VERIFIED** (abs pages; full PDF for AECV) |

## 309-ФЗ / УКЭП (operator decks)

| Claim | Status | Action |
|---|---|---|
| «309-ФЗ ч.16 ст.55.5-1 = обязательная УКЭП ПД» | **OVERCLAIM** | Primary kremlin text: parts 15–16 = NRS notifications / negative-expertise reporting. Force date **01.03.2026**. |
| УКЭП вместо ИУЛ на экспертизу | **VERIFIED** letter existence | Минстрой **30.01.2026 № 4420-КМ/14** + **63-ФЗ** — cite these, not «309 ч.16 = УКЭП» |

## Concrete file edits


1. **External `research.md` (operator):** remove `…2026.103676`; keep `…2025.103676` with correct title; add AECV/AEC-Bench/MechVQA/BRAVO if still missing (obsolescence, not only fabrication).
2. **`docs/docs.md`:** already uses `104735` (good). Add one-line note that paper AECV mean is **4 fields**; AeroBIM live five-field macro is not the paper’s headline number (see verification report).
3. **`docs/evidence/aecv-bench-eval-latest.json`:** add `macro_exact_match_rate_paper_four_fields` in executive summary (tool update).
4. **`представление.txt` (external):** keep Structured AI claim only with dated source link; do not invent extra investors beyond published lists.
5. **Never** promote March 2026 Минцифры draft “mandatory AI labeling for all content” as enacted law — enacted **243-ФЗ** differs (see report §2.7).

Full narrative: [`SOURCE_VERIFICATION_REPORT_2026_08_04.md`](SOURCE_VERIFICATION_REPORT_2026_08_04.md).
