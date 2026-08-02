---
title: "Red Team rollup — P0 TechLab WP-01..08 (2026-08-02)"
status: active
version: "1.0.0"
last_updated: "2026-08-02"
claim_boundary: "Self red-team rollup. Checkpoint NO_GO. Not external audit / not Checkpoint GO."
---

# Red Team rollup — P0 WP-01..08 (2026-08-02)

**Author relationship:** self  
**Package:** TechLab Task 07 P0 eng work packages WP-01 → WP-08  
**Checkpoint:** **`NO_GO`**

## Per-WP evidence

| WP | Delivery | Detail RT |
|---|---|---|
| WP-01 | Runtime baseline schema 1.2.0 + CI `--check-complete` | [`RED_TEAM_WP01_03_2026_08_02.md`](RED_TEAM_WP01_03_2026_08_02.md) |
| WP-02 | `HybridRouteGate` mandatory advisory pre-gate | same |
| WP-03 | Detached signature envelope; trust_chain NOT_VERIFIED | same |
| WP-04 | Norm pack v2 RASE + eligibility + expert journal | [`RED_TEAM_WP04_05_2026_08_02.md`](RED_TEAM_WP04_05_2026_08_02.md) |
| WP-05 | Package completeness inventory (no native DWG claim) | same |
| WP-06 | Open-corpora profiles (honest n=7; CI smoke pins) | [`RED_TEAM_WP06_08_2026_08_02.md`](RED_TEAM_WP06_08_2026_08_02.md) |
| WP-07 | Quality protocol + Wilson planner (interim 0.60) | same |
| WP-08 | README EN/RU + baseline snippet + TZ matrix sync | same |

## Cross-cutting invariants (spot-check)

| Invariant | Status |
|---|---|
| `summary.passed` only deterministic / ADR-001 | Intact — advisory/hybrid/signature/quality tools do not flip pass |
| Advisory OFF==ON | Intact (WP-02 gate is verdict-neutral suppress path) |
| Fail-closed capabilities | Intact |
| No >90% accuracy claim | Intact — protocol interim 0.60 only |
| No MEP delivered / `mep_system_clash=OK` | Intact — RT-003 OPEN |
| No «УКЭП проверена» | Intact — WP-03 NOT_VERIFIED |
| No native DWG | Intact — WP-05 format honesty |
| Fixture ≠ customer | Intact — RT-001 OPEN |

## Highest residual risks

1. **RT-WP01-01** — baseline env fingerprint is generator host, not CI matrix attestation.  
2. **RT-WP07-03** — mitigated with `demonstrates_interim_target_publishable=false`; human Claims Lock still required for any publish.  
3. **RT-WP02-03** — MITIGATED on Analyze + kimi smoke (`vlm_smoke_gate`); any *new* PUBLIC egress path must still re-check gate.

## Verdict

P0 eng package WP-01..08 is **delivered under Claims Lock**.  
Customer Checkpoint remains **`NO_GO`** until RT-001 / RT-002 / RT-003 close with external evidence.
