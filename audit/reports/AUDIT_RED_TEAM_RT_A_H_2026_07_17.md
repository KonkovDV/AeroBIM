# Self-audit — Red Team remediations RT-A…H (2026-07-17)

**Checkpoint:** **NO_GO** (RT-001/002/003 **HOLD**)  
**Claims:** no flip of DWG/CV/MEP/accuracy OK states.

## Findings → remediations

| ID | Fix | Tests / docs |
|----|-----|--------------|
| **RT-A** | Contour orchestrators: `IngestionOrchestrator`, `DeterministicValidationOrchestrator`, `AdvisoryOrchestrator`, `EvidenceAssembler`; UC `execute()` coordinates only | `test_rt_a_*` |
| **RT-B** | `dataclasses.replace` for confidence/priority (no `__dict__`) | `test_rt_b_*`; mypy already in CI |
| **RT-C** | Infra `except` → ERROR + FAILED capability + traceback log (qty/load/mep); expected unconfigured → NOT_VERIFIED | `test_rt_c_*` |
| **RT-D** | Mixed DWG+DXF → `dwg_dxf=FAILED` if any DWG unparsed | `test_rt_d_*` |
| **RT-E** | Advisory ON/OFF: identical engine signature + `summary.passed` + hash | `test_rt_e_*` (real UC path) |
| **RT-F** | Non-dev `Settings.from_env()` without bearer/OIDC fail-closed | `test_rt_f_*` (+ existing wave0) |
| **RT-G1** | TZ path verified; CI `check_markdown_links` job | tool + workflow |
| **RT-G2** | `06-architecture-reference.md` → **SUPERSEDED**; SSOT = TARGET | header + Tier-0 |
| **RT-G3** | README top **NO_GO** banner + claim-boundary links | README |
| **RT-H** | `docs/TIER0_INDEX.md` live vs superseded; I0/I6/I7 → `docs/archive/execution/`; stubs kept; claim-boundary + Claims Lock aligned | Tier-0 + archive |

## HOLD (unchanged)

RT-001 / RT-002 / RT-003 — require customer evidence. No GO.
