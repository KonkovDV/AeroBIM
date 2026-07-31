# Sprint 2.1 research → code map

**Evidence class:** lecture/publication mapping is `PUBLIC_CLAIM` / `INFERRED` unless tied to a test.  
**Rule:** do not implement fashionable features without dataset + claim impact.

| Research finding | Code location | Proposed change | Priority | Test | Claim impact |
|---|---|---|---|---|---|
| openBIM / IFC as exchange SSOT | `infrastructure/adapters/ifc_*`, samples/ifc | Keep IFC4 fixtures in sprint pack; license-review before vendoring bSI samples | P0 | `test_sprint_2_1_dataset` | Allows fixture baseline only |
| IDS conformance | `ids` adapters + samples/ids | Mutation SSOT for missing/wrong property | P0 | mutation ground truth | Not customer IDS accuracy |
| BCF topic handoff | BCF export + T0–T5 ladder | Demo export OK; T2 stays not_verified | P1 | existing BCF tests | Forbid CDE_READY |
| CDE integration | docs + verify_bcf_t2 | No code claim without import-log evidence | P2 | T2 verifier | Customer-only |
| AEC compliance checking | deterministic analyze path | Baseline CLI inventory + future analyze hook | P0 | `test_sprint_2_1_baseline` | engineering_baseline_only |
| Drawing understanding | HybridDrawingAnalyzer / OCR | Advisory VLM separate; OCR primary | P1 | drawing advisory tests | No human-level CV |
| Document AI / RAG security | `domain/hybrid/*`, HybridRouteGate | Treat docs as data; default deny egress | P0 | prompt-injection tests | Masking ≠ anonymization |
| GraphRAG | I9 advisory scaffold | Do not expand to product GraphRAG | P3 | ifc-qa fixture | Forbid IfcLLM product claim |
| Prompt injection | `llm_advisory` mock + cases | Fixture cases 11–12 | P0 | `test_llm_prompt_injection` | Advisory only |
| HITL | coverage + review_required | Demo step 15 expert handoff | P1 | protocol doc | Expert decides |
| Calculation evidence | calculation_match vs correctness | Level B mutations; correctness not_implemented | P0 | Level B + sprint mutations | Forbid calc correctness |
| Revision comparison | revision diff domain | Pack group F empty until licensed revisions | P2 | existing revision tests | no_longer ≠ resolved |
| Quality metrics TP/FP/FN | detection-precision + sprint baseline | Lightweight CLI declares inventory; full TP needs mutation apply | P0 | baseline tests | Not product accuracy |
| LLM advisory hybrid | `domain/llm_advisory.py` | Provider Protocol + mock Kimi/Qwen/Gemma | P0 | invariance tests | Verdict invariance |

## Sources reviewed (non-exhaustive; not product proof)

- buildingSMART IFC/IDS/BCF public materials (`PUBLIC_CLAIM`)
- Existing AeroBIM Hybrid AI / Claims Lock / CRITICAL_BLOCKERS (`VERIFIED` in-repo)
- Industry lectures mapped only as candidates — never as RT-001 closure
