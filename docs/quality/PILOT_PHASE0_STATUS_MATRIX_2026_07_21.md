# AeroBIM Pilot Phase-0 Status Matrix

**Freeze SHA:** `a77e54f` (2026-07-21)  
**Checkpoint:** **NO_GO** (RT-001 / RT-002 / RT-003) — unchanged by engineering remediations  
**Principle:** do not invent customer evidence; do not flip checkpoint to GO

## Open blockers (customer)

| ID | Проблема | Текущий статус | Доказательство | Требуется изменение | Можно закрыть без заказчика |
|---|---|---|---|---|---|
| RT-001 | Нет размеченного клиентского корпуса точности | **OPEN** | `customer-intake-gate.json` all false; PrecisionClaim withhold | Customer corpus + ≥2 adjudicators + agreement | **Нет** |
| RT-002 | Нет утверждённого norm pack | **OPEN** | Synthetic/draft packs only | Signed customer_approved pack | **Нет** |
| RT-003 | MEP system clash не verified на федеративной модели | **OPEN** | Unconfigured provider DI; MEP gap doc | Federated IFC + matrix + expert review | Тех. основу — **да**; закрыть RT-003 — **нет** |

## Engineering phases (A–L)

| ID | Проблема | Текущий статус | Доказательство | Требуется изменение | Можно закрыть без заказчика |
|---|---|---|---|---|---|
| A | Drift runtime metrics / README | **DONE** | schema 1.1.0 artifact + README/RU markers; CI `--check-readme` | SSOT JSON + CI drift gate | **Да** |
| B | Customer intake fail-closed | **DONE** | Gate tool + `CustomerIntakeGate` + `AEROBIM-CUSTOMER-INTAKE` on `samolet_pilot` | Enforce intake before samolet_pilot analyze → BLOCKED/passed=false | Eng **да** |
| C | Boolean `summary.passed` ambiguity | **DONE** | Domain `PackageOutcome` + `summary.outcome` + FE badge | Domain enum + API/FE | **Да** |
| D | Rule pack pilot contract | **DONE** (eng) | Schema + loader + immutable hash + negative tests | — | Eng **да**; **RT-002 OPEN** |
| E | MEP system-aware clash | **DONE** (eng foundation) | Domain entities + matrix eval + Unconfigured DI + synthetic stub tests | Federated IFC + signed matrix | Тех. основу **да**; **RT-003 OPEN** |
| F | Precision claim gates | **PARTIAL** | PrecisionClaim + agreement tool | Per-class metrics + publishable gates honesty | Eng **да** |
| G | SLA ≤30 min evidence | **PARTIAL** | measure_package_sla 1.2.0 fixture-only | Harden claim_level gates | Eng **да** |
| H | BCF T0–T4 ladder | **PARTIAL** | T1 structural done; T2 NOT_VERIFIED | Formal ladder + T2 evidence template | Taxonomy **да**; T2 **нет** |
| I | Revision compare findings | **PARTIAL** | Doc-identity / section diff | Cross-revision finding matcher | Scaffold **да** |
| J | HITL review flow | **DONE** | Full state machine + SSOT previous_state | Minor UX filters if gaps | Mostly **да** |
| K | Security residuals | **PARTIAL** | RTATOM A1–A3 CLOSED* | Threat model note; POST-05 residual | Residual risk **да** |
| L | Open-core model | **MISSING** | MIT only | ADR proposal (not license change) | **Да** |

## Already closed (do not reopen)

RTATOM A1/A2.5/A3, RT-POST-01..11 (hashes residual on pip bootstrap), RT-004..015 engineering remediations — see `CRITICAL_BLOCKERS.md`.

## Allowed pre-customer verdict

```
Engineering readiness: improved (target)
Fixture readiness: GO
Customer sign-off: NO_GO
Pilot start: CONDITIONAL_GO after intake
```
