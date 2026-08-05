# Red Team — Wave-2: Tracker К0 + commercial hygiene + coverage UI (2026-08-04)

**Author relationship:** self + [Security Review](220ba608-c549-4739-a0b5-cda1ce659326)  
**Scope:** uncommitted wave after `385c4b9` — К0 tracker pack, commercial templates, private-doc quarantine, coverage schema 1.1.0 / CoverageMapPanel, LLM advisory rename + pilot egress hard-disable  
**Checkpoint:** **`NO_GO`** (unchanged)  

## Verdict

| Lane | Result |
|---|---|
| Application security (Critical/High/Medium) | **0 validated** |
| Claims Lock (hard >90% / MEP delivered / CDE-ready / proven customer SLA) | **PASS** |
| Doc integrity / process | **HIGH/MED found → mitigated in this commit** |
| Customer Checkpoint | Still **NO_GO** (RT-001/002/003) |
| Friday commercial readiness | **OPEN** — live funnel counts только у владельца / `.local` (не дублировать в GH); tracker ask 30+ orgs |

## Findings

| ID | Sev | Status | Finding | Mitigation |
|---|---|---|---|---|
| RT-W2-01 | HIGH | **MITIGATED** | Org count contradicted (35 vs 39 vs SSOT) | Unified to SSOT = `.local/commercial-ops/commercial-pipeline.csv` (число — kitchen only); legacy sprint2 CSV marked superseded |
| RT-W2-02 | HIGH | **MITIGATED** | Root `AeroBIM/` private dump + live commercial CSV/outreach risked GH | Moved to `.local/internal-docs/team-private/` + `.local/commercial-ops/`; `.gitignore` `/AeroBIM/` + customer-discovery globs; sprint lead files removed from index |
| RT-W2-03 | MED | **MITIGATED** | Baseline PDF cited old public CSV path | Generator + PDF regenerated: SSOT org count только `.local/…; не в GH` |
| RT-W2-04 | MED | **MITIGATED** | Soft capability phrasing in outreach («бесплатно», модель+чертежи+ТЗ+расчёты без границ) | Softened; DWG/MEP/CDE not promised in long email / one-pager |
| RT-W2-05 | MED | **MITIGATED** | Unsourced peer «15 пилотов» in qa-defense | Softened to field-pilot reality without hard count / without peer names |
| RT-W2-06 | MED | **MITIGATED** | «Четыре состояния» vs 5 operator labels | Doc retitled; five labels explicit; mirrors updated |
| RT-W2-07 | MED | **OPEN** | Outreach counter still empty (owner kitchen); caller / ≥10 emails / phone | Cannot close in code — owner action before Fri 08:00 |
| RT-W2-08 | LOW | **OPEN** | ~11 ₽ cost line needs owner OK before chat paste | Opening omits ₽; PDF keeps ~111 ₽ evidence + forbid 11 ₽ |
| RT-W2-09 | LOW | **MITIGATED** | Demo artifact ambiguity (tech protocol vs draft demo-format) | Meeting pack row 4 clarifies |
| RT-W2-10 | LOW | **MITIGATED** | TIER0 `last_updated` stale | Bumped 4.4.0 / 2026-08-04 |
| RT-W2-11 | LOW | **MITIGATED** | Typo «сненулевой» | Fixed |
| RT-W2-SLA | LOW | **MITIGATED** | `measure_package_sla` ignored `AEROBIM_LLM_ADVISORY_ENABLED` | Reads ADVISORY then LOCAL alias |
| RT-SEC-01 | INFO | OPEN | Git history still has deleted synthetic lead placeholders | No rewrite; content was `example.invalid` only |
| RT-SEC-02 | INFO | OPEN | Live emails/INN remain only under `.local/commercial-ops/` | Keep out of commit; never `git add -f` |

## Security spot-check (code)

| Control | Status |
|---|---|
| `samolet_pilot` / `production` hard-disable advisory egress via `llm_local_ready()` | Intact + new test |
| Coverage API same ACL as report fetch | Intact |
| CoverageMapPanel React text-only (no XSS sink) | Intact |
| `operator_status=done` ≠ `summary.passed` (ADR-001) | Documented in API note |

## Claims Lock spot-check

| Invariant | Status |
|---|---|
| No product >90% | Intact (protocol / baseline / templates) |
| AECV 0.4325 ≠ product accuracy | Intact |
| Fixture SLA ≠ customer ≤30 мин | Intact |
| MEP / native DWG / CDE not delivered | Intact (gaps explicit) |
| Commercial PII not on public GH surface | Intact after quarantine |

## Residual risks (do not claim closed)

1. RT-001 / RT-002 / RT-003.  
2. Friday tracker ask «30+ orgs» — live SSOT count только в `.local`; do not invent orgs on GH.  
3. Contacted / replied / demo — заполняет только владелец; публичные TRACKER_* = placeholders.  
4. Owner: phone, who calls, tone OK, ADR-002, DWG option, Kortunov slot, builder-in-team.  
5. Model bake-off still NOT_RUN without API key.  
6. PDF binary must stay aligned with MD after any regen.

## Not claimed closed

Customer Checkpoint GO · publishable precision · customer SLA · MEP system-clash · signed LOI · Rospatent · Dom.RF figure verification.
