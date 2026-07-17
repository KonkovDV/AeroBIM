---
title: "Research Alignment — AI for AEC document checking (2025–2026-07)"
status: active
version: "1.0.0"
last_updated: "2026-07-17"
tags: [aerobim, research, literature, roadmap]
claim_boundary: >
  Literature alignment only. Does not claim product GO, >90% accuracy, MEP delivery,
  CDE-ready BCF, or customer SLA. Checkpoint remains NO_GO (RT-001/002/003).
provenance: >
  Operator synthesis dated 2026-07-17; key citations spot-checked via arXiv
  (Blueprint 2602.13345, IfcLLM 2605.13236). Remaining items inherited from synthesis
  and must be re-verified before citation in public claims.
---

# Research → AeroBIM alignment (2025 — July 2026)

Parent: [`TARGET_HYBRID_ARCHITECTURE_TZ_2026.md`](TARGET_HYBRID_ARCHITECTURE_TZ_2026.md) · Claims: [`CLAIMS_LOCK_2026_07_17.md`](../../audit/reports/CLAIMS_LOCK_2026_07_17.md)

## Thesis (industry + AeroBIM)

| Industry 2026 consensus | AeroBIM posture (I0–I7) |
|-------------------------|-------------------------|
| Region-first VLM (detect → crop → VLM), not whole-sheet GPT-4V | **Partial:** `DrawingRegionRef` + OCR degrade; **no** YOLO/VLM yet (`cv_human_level=MISSING`) |
| LLM interprets norms; **numerics stay deterministic** | **Aligned:** DeterminismGate + IDS compiler advisory; engine owns `summary.passed` |
| IFC via Graph/relational backends, not raw IFC in context | **Gap:** IfcOpenShell validators; no GraphRAG / IfcLLM port |
| Cross-doc = attribute/semantic alignment + HITL escalate | **Partial:** SectionDiff, quantity/load сверка; no VLM 2D↔3D map |
| κ / dual experts before publishable metrics | **Aligned (tooling):** κ+α + intake gate; **blocked** on customer corpus |
| Provenance + severity triage + HITL | **Partial:** findings provenance, priority, divergences; CoVe not shipped |

**Invariant unchanged:** determinism ≻ LLM for sign-off (Mirhosseini et al. BRI 2026; Claims Lock).

## Theme map

### 1. VLM / multimodal drawings

| Source (verified*) | Recommendation | AeroBIM today | Next slice (no GO) |
|--------------------|----------------|---------------|--------------------|
| Blueprint [arXiv:2602.13345]* | YOLO regions → region-restricted VLM OCR | OCR-only multimodal; regions plumbed I7 | **I8a:** detector adapter behind `MultimodalDrawingPipeline`; honesty stays MISSING until corpus F1 |
| MechVQA [arXiv:2605.30794]† | Symbol VQA + drafting standards in prompts | Heuristic OCR annotations | Optional MechVQA-style eval harness (fixture only) |
| AEI bridge digitization 2026† | VLM for 2D engineering sheets | Same | Bundle with I8a |

\*Externally spot-checked 2026-07-17. †From operator synthesis — re-verify before public cite.

### 2. Automated code/rule compliance (ACC)

| Source | Recommendation | AeroBIM today | Next slice |
|--------|----------------|---------------|------------|
| AiC / AEI LLM ACC 2025–26† | LLM → IDS; hybrid RASE | Deterministic IDS compile + stub LLM assist | **I8b:** RASE fields on norm pack / issue provenance (`norm_clause` already partial) |
| LLM regulatory NL 2026† | Ambiguity → LLM; numbers → engine | DeterminismGate | Keep; add CoVe optional advisory loop |

### 3. IFC + LLM agents / GraphRAG

| Source | Recommendation | AeroBIM today | Next slice |
|--------|----------------|---------------|------------|
| IfcLLM [arXiv:2605.13236]* | Relational + graph backends; LLM routes queries | Direct IfcOpenShell | **I9:** `IfcKnowledgeGraphPort` + advisory query tool (allowlisted); never sign-off |
| ASK-BIM / BIMConverse / IFC Whisperer† | GraphRAG over IFC | — | Same I9; cite after verify |

### 4. Cross-document consistency

| Source | Recommendation | AeroBIM today | Next slice |
|--------|----------------|---------------|------------|
| Context-aware 2D↔3D VLM [arXiv:2602.18296]† | Escalate unmatched zones to HITL | SectionDiff + load/qty | **I8c:** escalate unmatched `DrawingRegionRef` → review events |
| Spec ↔ IFC attribute alignment† | Compare marks/quantities not raw geom | Quantity/Load ports | Extend claims; keep сверка ≠ correctness |

### 5. Evaluation / gold corpora

| Source | Recommendation | AeroBIM today | Next slice |
|--------|----------------|---------------|------------|
| Blueprint benchmark graded relevance* | nDCG for ranked findings | Priority score; no nDCG | Optional ranking eval (fixture) |
| Cohen κ in engineering tasks† | Dual annotate; κ threshold | κ≥0.60 + α≥0.67 gates | **Literature stretch:** report κ≥0.80 as *aspirational* customer SOP; do not silently raise publish gate without pilot agreement |
| Inter-annotator ≠ ceiling† | Low κ → rewrite rule | Intake runbook | Document in intake SOP |

### 6. Production AI / HITL

| Source | Recommendation | AeroBIM today | Next slice |
|--------|----------------|---------------|------------|
| Hallucination mitigations 2026† | Severity + CoVe + provenance | Severity + DeterminismGate + evidence_refs | CoVe as advisory tool; deep-link sheet/clause |
| buildingSMART HITL 2026† | Expert confirm | ReviewEventStore + HITL packs | Promote IDS draft HITL (partial I4/I7) |

## Honest gaps (do not overclaim)

1. **No product VLM** — Blueprint-class pipeline not shipped; OCR degrade ≠ human CV.  
2. **No GraphRAG IFC** — IfcLLM is target pattern, not runtime.  
3. **No RASE compiler** — norm packs carry clause metadata; not full RASE extraction.  
4. **κ≥0.8** is literature preference; AeroBIM publish gate remains κ≥0.60 / α≥0.67 until customer protocol amends Claims Lock.  
5. **Checkpoint NO_GO** until RT-001/002/003 regardless of research alignment.

## Proposed roadmap waves (post-I7)

| Wave | Priority | Deliverable | Literature driver | Blocks GO? |
|------|----------|-------------|-------------------|------------|
| **I8a** | P1 | Region detector + region-OCR/VLM degrade path; keep `cv_human_level=MISSING` | Blueprint | No |
| **I8b** | P1 | RASE-ish provenance on advisory findings (R/A/S/E tags) | Hybrid ACC | No |
| **I8c** | P2 | HITL escalate unmatched drawing regions | Cross-doc VLM | No |
| **I9** | P2 | `IfcKnowledgeGraphPort` + agent query tool (advisory) | IfcLLM | No |
| **I6′** | P0 | Customer corpus + κ/α publish path (existing I6) | Evaluation chapter | **Yes — RT-001** |

## Suggested reading order for implementers

1. Blueprint (2602.13345) — region pipeline  
2. IfcLLM (2605.13236) — IFC query backends  
3. Mirhosseini et al. BRI 2026 — already in TARGET (ACC interpretation review)  
4. AeroBIM Claims Lock + Red Team PASS3 — honesty bar  

## Non-goals

- Raising public accuracy claims from literature F1/MechVQA numbers  
- Treating GraphRAG demos as MEP clash delivery  
- Skipping DeterminismGate for “SOTA agent” demos  
