<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
# Release Status — 2026-08-06

**commit_sha:** `d96a59ac6704357336ae46f7d61f6435be4c6a2c`  
**generated_at:** `2026-08-06T20:15:00+00:00`  
**checkpoint:** **NO_GO**  
**claim_level:** `synthetic_only`  
**verdict:** **ENGINEERING_READY_CUSTOMER_BLOCKED**

## Gates summary (recorded)

| Gate | Result |
|---|---|
| `ruff format --check src tests` | **PASS** |
| `ruff check src tests` | **PASS** |
| `mypy src/aerobim --ignore-missing-imports` | **PASS** |
| focused pytest (verify + sprint2 manifest + advisory OFF==ON) | **PASS** — 19 passed |
| full pytest | **PASS** — 1902 passed, 8 skipped, 159 subtests, ~26.7s |
| `verify_release_evidence` | **PASS** |
| runtime-baseline `quality_gates` | PASS (ruff/mypy/pytest/vitest/build) |

Honesty note: live full pytest counts (1902/8) differ from `runtime-baseline-latest.json` historical `tests_passed=2043` / `tests_collected=2052`. Do not conflate; both are engineering signals, neither is customer accuracy.

## Evidence paths

See [`RELEASE_EVIDENCE_INDEX_2026-08-06.md`](RELEASE_EVIDENCE_INDEX_2026-08-06.md) and [`docs/evidence/release-status-2026-08-06.json`](../evidence/release-status-2026-08-06.json).

## Customer intake gate

| Field | Value |
|---|---|
| status | `BLOCKED_NO_CUSTOMER_DATA` |
| claim_level | `not_ready` |
| precision_claim_publishable | `false` |
| path | `audit/evidence/customer-intake-gate.json` |

Outreach tracker has **one** TIM / «Фонд Транспортные инновации Москвы» row with `not_contacted` / `next_step=prepare outreach` — **not** a claim that contact occurred.

## SUPERSEDED note

`docs/evidence/sprint2-synthetic-baseline-2026-08-04.*` is **HISTORICAL/SUPERSEDED** by canonical 2026-08-06 brief filenames:

- `docs/evidence/SPRINT2_BASELINE_REPORT_2026-08-06.md`
- `docs/evidence/SPRINT2_BASELINE_REPORT_2026-08-06.pdf`
- `docs/evidence/sprint2-baseline-evidence.json`

## Claims lock (forbidden)

Do **not** claim: product accuracy, >90%, production-ready, native DWG, delivered MEP, calc independence, CDE-ready BCF, customer SLA. Synthetic/fixture only. `customer_precision_claim_publishable=false`.

## Remaining blockers (customer)

- Dual expert adjudication (RT-001)
- Licensed customer package + intake gates true
- Severity taxonomy customer approval
- Live model bake-off with keys (optional; not required for this verdict)
- Commit of uncommitted Sprint 2 packaging after human review
