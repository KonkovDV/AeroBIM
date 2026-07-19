# RED TEAM HYPERDEEP AUDIT + FIX — 2026-07-19

**Scope:** Adversarial re-audit of Phases 0–10 + residual slices after Master Prompt delivery.  
**Checkpoint:** **`NO_GO`** — external blockers **RT-001 / RT-002 / RT-003** remain OPEN.  
**Absolute:** PR #10/#11 untouched; no history rewrite; AI must not own `summary.passed`; no VLM/GraphRAG promotion.

---

## Remote hygiene note (for reviewers still on `9f05c44`)

`9f05c44` (2026-07-17) is **not** current `main`. GitHub `KonkovDV/AeroBIM` `main` already contained Red Team Phases 0–10 + residuals through `97e58bf` (2026-07-19T09:51:29Z).

If a local clone still shows July 17 HEAD:

```bash
git fetch origin
git log origin/main -5 --oneline
```

On `97e58bf` the following claimed July-17 defects were **already fixed**:

| Claimed defect (verbatim vs `9f05c44`) | Status on `97e58bf`+ |
|---|---|
| quantity exception → WARNING / not in blocking list | **Already FIXED**: ERROR + `quantity=FAILED`; `quantity` in `_PASS_BLOCKING_*` |
| MEP provider exception → soft `NOT_VERIFIED` | **Already FIXED**: infra exception → `FAILED` (unconfigured stays `NOT_VERIFIED`) |
| HITL events after `save(report)` | **Fixed in this commit**: append trail → then save; discard on save failure |

Hyperdeep ADV-01…05/09 fixes below were previously **local-only** (not committed) — that is why a fresh `main` pull before this push would not show them.

---

## Verdict

Code-level false-pass / tenancy / job-store races from hyperdeep re-audit are mitigated in this push.  
Ship decision remains **NO_GO**.

---

## Findings → Fixes (this push)

| ID | Sev | Finding | Fix |
|---|---|---|---|
| **RT-ADV-01** | CRITICAL | bSI submit ACK → `ifc_schema=OK` under require | ACK → `NOT_VERIFIED` |
| **RT-ADV-02** | CRITICAL | Flat uploads + storage-wide jail | `tenants/{tid}/uploads/…` + ACL prefix |
| **RT-ADV-03** | HIGH | Redis idempotency `SET nx` ignored | Honor nx / return winner / retry |
| **RT-ADV-04** | HIGH | Reclaim on every job GET | Reclaim on submit only |
| **RT-ADV-05** | HIGH | Pilot/prod weaken `REQUIRE_*` / local cert | Fail-closed + cert disabled |
| **RT-ADV-09** | MEDIUM | BCF `xsd_status=failed` without XSD run | Stay `not_run` |
| **RT-ADV-HITL-TX** | HIGH | HITL trail after report save | Trail first; `discard_report` on save fail |

### Still open

| ID | Note |
|---|---|
| RT-001 / RT-002 / RT-003 | External evidence only — **do not close with code** |

---

## Gates

| Gate | Result |
|---|---|
| `pytest` (backend) | **642 passed**, 4 skipped |
| Explicit non-claims | Not GO; not full EXPRESS/bSI; not federated MEP complete |
