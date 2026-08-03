---
title: "LLM→IDS research baselines (RT-023)"
status: active
version: "1.0.0"
last_updated: "2026-08-03"
claim_boundary: "Literature map only. Not AeroBIM product accuracy. Checkpoint NO_GO."
---

# LLM→IDS research baselines (RT-023)

## Why this note exists

Remote Red Team (Task 07) flagged that «LLM→IDS compiler» in TZ v2.0 is indefensible without the 2025–2026 published baseline layer. AeroBIM `RequirementToIdsCompiler` remains **planned / advisory+HITL**.

## Anchors

| ID | Citation | Takeaway for Claims Lock |
|---|---|---|
| ITMO-ICDM-2025 | Perov et al., ICDM Workshops 2025, DOI 10.1109/icdmw69685.2025.00203 | Санкт-Петербург peer pipeline: regulation→IDS with repair-loop ablation |
| Ishigaki-IDS | arXiv:2606.08545 | Verifier-aware open weights; practitioner HITL, not unsupervised product |
| Ishigaki-IDS-Bench | arXiv:2605.22079 | Expert bench; content-audit pass rates remain hard for general LLMs |
| P4IR | arXiv:2606.22402 | RL against rule hallucination in ACC |
| Zentgraf AEI | AEI 104735 | Smart Standards → SHACL path (adjacent, not IDS) |

## AeroBIM posture

1. Norm pack v2 + `expert_confirmation_journal` already fail-closed without customer approval (RT-002 still OPEN).  
2. Any LLM draft IDS/norm text is **advisory**; never sets `summary.passed`.  
3. TZ language: «advisory компилятор с HITL; метрики сопоставляем с опубликованными» — allowed.  
4. «SOTA compiler / beats Solibri IDS authoring» — **forbidden** without measured compare.

## Errata pointer

ASK-BIM venue + НРС: [`CITATION_ERRATA_2026_08_03.md`](CITATION_ERRATA_2026_08_03.md).
