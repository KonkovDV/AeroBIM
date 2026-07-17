---
title: "Audit — post-I8c + TZ v2.0 + research re-verify"
status: active
generated_at: "2026-07-17"
author_relationship: self
claim_boundary: "Self-audit. Checkpoint remains NO_GO (RT-001/002/003)."
---

# Hostile audit of recent changes (Track E → I8c + TZ v2.0)

## Scope

| Wave | SHA / artifact | Claim under audit |
|------|----------------|-------------------|
| Track E | `903a2ad` | Residual honesty CLOSED |
| I8a | `6d0bf05` | Region detector without CV OK |
| I8b | `48fd926` | RASE advisory only |
| TZ v2.0 | `b3de023` | TBD filled; Claims Lock intact |
| I8c + research deepen | this wave | HITL escalate; external re-verify |

## External evidence (re-fetched 2026-07-17)

| Source | Finding used in product/TZ | Misuse risk |
|--------|----------------------------|-------------|
| Blueprint arXiv:2602.13345 | Region detect → crop → VLM OCR; nDCG@3 graded | Claiming YOLO shipped — **we only ship heuristic priors** |
| IfcLLM arXiv:2605.13236 | Relational+graph backends; 93–100% on **30 scenarios / 3 models** | Quoting as product IFC-LLM accuracy — **forbidden**; I9 not shipped |
| AECV-Bench arXiv:2601.04819 | OCR strong; symbol counting weak | Marketing “AI reads drawings like engineer” — **forbidden** |
| IEEE ACCESS HITL RASE | Expert-in-loop RASE tagging | Claiming full RASE compiler — **we only coarse infer R/A/S** |
| Cohen κ practice | Substantial ≈0.60–0.80 | Silently raising publish gate to 0.80 — **tooling stays 0.60** |

## Findings

| ID | Sev | Status | Detail |
|----|-----|--------|--------|
| AUD-I8A-001 | MED | **HOLD** | Heuristic regions ≠ Blueprint YOLO — docs/TZ must say “priors / future YOLO” |
| AUD-I8B-001 | LOW | **HOLD** | `E` (Exception) never auto-inferred — documented deferred |
| AUD-I8C-001 | MED | **MITIGATED** | HITL INFO issues do not block pass — correct; events only if store wired (DI now wires store) |
| AUD-TZ-001 | HIGH | **HOLD** | TZ still lists aspirational κ>0.80 — correctly labeled SOP stretch vs tooling 0.60 |
| AUD-TZ-002 | HIGH | **PASS** | No unconditional «точность >90%»; RT-001 path explicit |
| AUD-TZ-003 | MED | **PASS** | DWG / MEP / calc correctness / CDE-ready forbidden wording present |
| AUD-CLAIMS-001 | CRITICAL | **PASS** | Checkpoint NO_GO unchanged; intake gates not flipped |
| AUD-TEST-001 | — | **PASS** | `test_drawing_region_hitl` + prior I8 suites green this session |

## Residual risks (do not close as GO)

1. RT-001/002/003 customer evidence still open.  
2. FE does not yet filter `hitl_required` in UI (types only).  
3. I9 GraphRAG port absent — do not demo IfcLLM numbers as AeroBIM.  
4. Untracked `docs/samolet-techlab-scorecard-2026.zip` must not be committed.

## Verdict

**Engineering honesty improved; product checkpoint `NO_GO`.**  
TZ v2.0 is usable for contest documentation if Claims Lock slide rules are followed.  
Next safe engineering slice: **I9 advisory port** or **FE HITL region filter** — neither unlocks GO.
