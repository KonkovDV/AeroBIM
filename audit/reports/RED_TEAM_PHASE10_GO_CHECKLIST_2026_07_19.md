# RED TEAM PHASE 10 — GO / NO_GO Checklist — 2026-07-19

**Phase:** 10 (decision surface only — no claim inflation)  
**Checkpoint verdict:** **`NO_GO`**  
**Reason:** External blockers RT-001 / RT-002 / RT-003 remain OPEN. Engineering hardening through Phases 0–9 does **not** authorize pilot GO.

---

## Absolute confirmations

| Constraint | Status |
|---|---|
| PR #10 untouched | Confirmed |
| PR #11 untouched | Confirmed |
| Git history untouched | Confirmed |
| No destructive Git | Confirmed |
| AI does not own `summary.passed` | Confirmed |
| No unsupported capability promoted to OK | Confirmed |

---

## Engineering readiness (code-only)

| Gate | Status |
|---|---|
| Sign-off honesty / capability policy (P1) | Mitigated locally |
| Provenance / finding_id (P2) | Mitigated |
| Persistence / commit / orphans (P3) | Mitigated |
| Upload / path jail / quotas (P4) | Mitigated |
| HITL state machine (P5) | Mitigated |
| Job lease / cancel / dead-letter (P6) | Mitigated |
| openBIM schema/IDS/GlobalId/BCF honesty (P7) | Mitigated |
| Tenancy job ACL / concurrency (P8) | Mitigated |
| Frontend build + Redis reclaim (P9) | Mitigated |
| Backend pytest | 622+ passed (Phase 8 gate); Phase 9 focused green |
| Frontend production build | **passed** (Phase 9) |

These rows prove **engineering false-pass / isolation work**, not customer accuracy or federated MEP.

---

## External blockers (cannot close with code)

| ID | Status | Required evidence |
|---|---|---|
| **RT-001** | **OPEN** | Customer corpus + accuracy protocol + ≥2 expert adjudicators; publishable >90% (or agreed threshold) |
| **RT-002** | **OPEN** | Customer-approved norm pack with `approval_ref` |
| **RT-003** | **OPEN** | Federated MEP scope memo + system-aware clash evidence |

---

## Claims vocabulary (locked)

| Claim class | Allowed status now |
|---|---|
| Fixture IFC/IDS / structural BCF | `VERIFIED_ON_FIXTURE` |
| Customer accuracy | `BLOCKED` |
| Customer norms | `BLOCKED` |
| Federated MEP OK | `BLOCKED` / `NOT_VERIFIED` |
| CDE BCF import | `NOT_VERIFIED` |
| Calculation correctness | `NOT_IMPLEMENTED` |
| LLM/VLM/GraphRAG on sign-off | Must remain **out** of deterministic path |

---

## GO criteria (all must be true)

1. RT-001 closed with reproducible customer evidence artifact  
2. RT-002 closed with approved pack + approval_ref wired into sign-off  
3. RT-003 closed with signed MEP scope memo + system-aware capability OK under pilot profile  
4. No open HIGH false-pass paths under `samolet_pilot`  
5. Claims Lock + README still honest (no marketing upgrade)  
6. CI green on `main` for lint/type/test/frontend build  

**Current:** criteria 1–3 **false** → verdict **`NO_GO`**.

---

## Explicit non-actions

- Do **not** start VLM/GraphRAG productization as a sign-off substitute.  
- Do **not** reword fixture SLA / F1 as customer metrics.  
- Do **not** mark MEP system clash OK without RT-003 evidence.

---

## Next operator actions

1. Commit + push Phases 8–10 local diffs when ready.  
2. Collect customer evidence for RT-001/002/003.  
3. Re-run Phase 10 checklist only after external artifacts land.
