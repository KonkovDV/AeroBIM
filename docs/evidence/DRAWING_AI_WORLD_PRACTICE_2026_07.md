---
title: "Drawing AI / OCR / CV / NLP — world practice memo (July 2026)"
status: active
version: "1.0.0"
last_updated: "2026-07-11"
tags: [aerobim, evidence, cv, ocr, nlp, samolet, tz]
---

# Drawing literacy vs human engineer — July 2026 evidence

**Purpose:** ground AeroBIM / Samolet Task 07 claims about scan recognition, computer vision, NLP, and “AI that reads drawings like a human”.  
**Audience:** pilot scope memo, TechLab jury, engineering roadmap (P2–P3).  
**Product implication:** CV/VLM are **advisory**; OCR+regex may feed MVP; sign-off stays deterministic + HITL.

## 1. Verdict (one screen)

| Question | Answer (July 2026) |
|----------|-------------------|
| Does Samolet Task 07 require “AI reads drawings like a human”? | **No as autonomous sign-off.** Competencies list CV/OCR/AI; sponsor quote keeps the **expert in the loop**. |
| Is full human-parity drawing understanding a realistic 2026 product claim? | **No** for heterogeneous PD/RD packs. |
| What is realistic? | **Hybrid:** domain OCR + narrow CV on agreed sheet types + rules/BIM + human adjudication. |
| What must not be claimed? | Autonomous GIP replacement; VLM “understands any scan”; >90% drawing QA without labeled corpus. |

## 2. Capability ladder (use in scope memo)

| Level | Capability | 2026 realism | AeroBIM phase |
|------|------------|--------------|---------------|
| L0 | Structured 2D annotations / vector text | High | MVP |
| L1 | OCR text from PDF/scans (stamps, dims, notes) | High on clean PDFs; degrades on poor scans | MVP baseline (`RasterDrawingAnalyzer`) |
| L2 | Narrow CV (walls/rooms/doors on **agreed** plan typology) | Medium–high **on own labeled set** | P2 advisory |
| L3 | VLM assistant (“where is the note / count symbols”) | Medium for text QA; **weak** for symbol literacy | P3 advisory + HITL |
| L4 | Full PD/RD “reads like a licensed engineer” | **Not product-ready** as unsupervised sign-off | Out of pilot acceptance |

## 3. External evidence (world)

### 3.1 Multimodal / VLM limits on AEC drawings

**AECV-Bench** (arXiv:2601.04819, 2026) — multimodal models on architectural/engineering drawings:

- OCR / text-centric document QA: strongest (reported up to ~**0.95** accuracy).
- Spatial reasoning: moderate.
- Symbol-centric tasks (reliable door/window counting): often ~**0.40–0.55**; treated as **unsolved**.
- Conclusion in paper: systems work as **document assistants**, lack robust **drawing literacy**; recommend domain representations + tool-augmented **human-in-the-loop** workflows.

Industry synthesis (Kreo / floor-plan recognition practice notes, 2025–2026):

- Floor-plan recognition is a **hybrid** of Intelligent OCR (text layer) + CV (geometry layer); value is linking text ↔ polygons.
- General foundation models remain weak on small symbols (reported door/window accuracies far below engineering QA bars).

### 3.2 Narrow domain CV (high scores ≠ human GIP)

Recent academic pipelines (2025–2026) report **high** precision/recall on **controlled** tasks (e.g. column/beam detection, wall segmentation, CAD reconstruction from scans) — often mid–high 90%s on their datasets.

**Interpretation for Samolet:** such numbers justify a **bounded P2 pilot** on one sheet family after labeling — they do **not** justify claiming universal scan understanding across all PD/RD disciplines and styles.

### 3.3 Incumbent BIM QA posture

**Solibri** (2025 interviews / product positioning): core remains **deterministic rule-based** checking by design (auditable, non-hallucinating). AI is explored for prioritization, localization, and workflow speed — **not** as replacement of the rule engine. Integrations emphasize CDE issue loops (ACC/Procore), not “VLM signs off the model”.

### 3.4 Russian market practice (2025–2026)

Public RU cases (industrial drawing QA, TimDoc-class PD assistants, construction doc platforms) consistently market:

- OCR + structured extraction + norm/RAG assist;
- minutes-scale review acceleration;
- **engineer remains** for disputed / non-standard cases;
- transparent reports (where / which rule), not black-box verdicts.

This matches AeroBIM’s Task 07 sponsor framing.

## 4. Mapping to AeroBIM today

| TZ term | Repo status | Sign-off? |
|---------|-------------|-----------|
| OCR | `RasterDrawingAnalyzer` (PyMuPDF + RapidOCR) — partial | Baseline may feed evidence; capability-gated |
| Computer Vision | Missing (layout/symbol models) | **Never** without HITL; P2 |
| NLP | Regex / narrative synthesizer + templates — partial | Deterministic path yes; LLM stub advisory |
| LLM / “AI” | `ids_assist_boundary` stub | Advisory only; never sets `summary.passed` alone |

SSOT rows: [`tz/TZ_COMPLIANCE_MATRIX_2026.md`](../tz/TZ_COMPLIANCE_MATRIX_2026.md) §1, §4.  
Architecture split: [`tz/TZ_ARCHITECTURE_REQUIREMENTS_2026.md`](../tz/TZ_ARCHITECTURE_REQUIREMENTS_2026.md) §4.

## 5. Recommended Samolet scope wording (copy-paste)

**In scope (MVP / pilot):**

1. OCR extraction from agreed PDF/scan quality classes with explicit `capabilities.raster` status.  
2. Deterministic IFC/IDS/cross-doc/clash path as acceptance gate.  
3. Optional advisory CV on **named** sheet types after a labeled mini-corpus.  
4. Expert adjudication of findings (TP/FP) per [`evaluation/DETECTION_PRECISION_PROTOCOL_2026.md`](../evaluation/DETECTION_PRECISION_PROTOCOL_2026.md).

**Out of scope (pilot acceptance):**

1. Unsupervised “AI reads any drawing like a human”.  
2. CV/VLM alone deciding `passed`.  
3. Published >90% drawing-understanding accuracy without customer adjudication.

## 6. Roadmap implications

| Phase | Action |
|-------|--------|
| P2 | Deepen OCR on Samolet scans; thin DWG; **narrow** CV advisory + capability honesty |
| P3 | VLM/LLM remark or sheet Q&A assist behind flag + HITL audit log |
| P4 | Publish precision only after labeled customer drawing corpus |

Do **not** reorder P2/P3 ahead of customer IFC/IDS intake if that blocks Task 07 SLA/BCF KPIs — drawing AI is parallel, not a substitute for openBIM acceptance criteria.

## 7. Sources

1. AECV-Bench — arXiv:2601.04819 (2026): https://arxiv.org/pdf/2601.04819  
2. Kreo — Floor plan recognition / I-OCR + CV hybrid (industry): https://www.kreo.net/news-2d-takeoff/floor-plan-recognition-technologies  
3. Solibri / aec+tech interview 2025 — deterministic core, AI exploratory: https://www.aecplustech.com/blog/building-better-bim-qa-2025-interview-solibri  
4. Smart Constr. 2026 — YOLO/U-Net scan→BIM (narrow high metrics): https://doi.org/10.55092/sc20260003  
5. Buildings 2026 — hybrid DL + rules for drawing vectorization: https://www.mdpi.com/2075-5309/16/5/1043  
6. RU practice examples (HITL drawing/PD assistants): TimDoc, industrial drawing QA case studies (2025–2026 public blogs)  
7. AeroBIM claim boundary: [`pilot-claim-boundary-2026.md`](../pilot-claim-boundary-2026.md)
