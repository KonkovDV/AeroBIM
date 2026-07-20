# AeroBIM Pilot Phase-0 Status Matrix

**Freeze SHA:** `c366b08` (2026-07-21 eng F–L)  
**Checkpoint:** **NO_GO** (RT-001 / RT-002 / RT-003) — unchanged by engineering remediations  
**Principle:** do not invent customer evidence; do not flip checkpoint to GO

## Open blockers (customer)

| ID | Проблема | Текущий статус | Доказательство | Требуется изменение | Можно закрыть без заказчика |
|---|---|---|---|---|---|
| RT-001 | Нет размеченного клиентского корпуса точности | **OPEN** | `customer-intake-gate.json` all false; PrecisionClaim withhold | Customer corpus + ≥2 adjudicators + agreement + held-out + FN | **Нет** |
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
| F | Precision claim gates | **DONE** (eng) | publishable requires customer+≥2+κ/α+held-out+FN; per-class metrics | Customer corpus | Eng **да**; **RT-001 OPEN** |
| G | SLA ≤30 min evidence | **DONE** (eng gate) | measure_package_sla 1.3.0 refuses customer_measurable without evidence | Customer pack measurement | Eng **да**; customer SLA **OPEN** |
| H | BCF T0–T4 ladder | **DONE** (taxonomy) | Ladder doc + empty T2 template; STATUS NOT_VERIFIED | Real CDE import evidence | Taxonomy **да**; T2 **нет** |
| I | Revision compare findings | **DONE** (eng) | `compare_findings_across_revisions` + export helper | Customer revision packs (none invented) | Eng **да** |
| J | HITL review flow | **DONE** | Full state machine + SSOT previous_state + FE filters | — | **Да** |
| K | Security residuals | **DONE** (doc) | Pilot threat model + inventory tests; POST-05 residual | BFF implementation | Residual risk **да** |
| L | Open-core model | **DONE** (ADR) | ADR-002 proposed; LICENSE unchanged MIT | Future license ADR if needed | **Да** |

## Already closed (do not reopen)

RTATOM A1/A2.5/A3, RT-POST-01..11 (hashes residual on pip bootstrap), RT-004..015 engineering remediations — see `CRITICAL_BLOCKERS.md`.

## Allowed pre-customer verdict

```
Engineering readiness: improved
Fixture readiness: GO
Customer sign-off: NO_GO
Pilot start: CONDITIONAL_GO after intake
Checkpoint: NO_GO
```
