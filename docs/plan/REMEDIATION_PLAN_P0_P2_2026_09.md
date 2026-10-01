---
title: "Remediation plan P0-P2 — evidence before features"
status: active
version: "1.1.1"
last_updated: "2026-09-10"
claim_boundary: >
  Planning document only. Nothing here is customer acceptance, product
  accuracy, SLA evidence, CDE import, or a contractual commitment.
---

# Remediation plan P0-P2

This plan orders the work after the September audit. The ordering rule is
simple: an artifact one customer expert can read and decide on outranks any
new engine capability.

Current honest status stays unchanged until matching evidence exists:
`checkpoint=GO`, `go_kind=regulatory_measurement_mvp`, `customer_go=false`,
`market_go=false`.

## Calendar this plan is measured against

| Date | Commitment | Artifact that proves it |
| --- | --- | --- |
| 14.09 | working stand, 10-25 findings, two-page summary | review pack delivered with a receipt |
| 18.09 | feature freeze | only fixes, docs and evidence land after this point |
| 19.09 | rehearsal run | recorded run log, no live improvisation |
| 19-21.09 | versioned delivery set | offline bundle, checksums, SBOM, format matrix, recovery scenario |
| 22.09 | demonstration day | deck that repeats the current checkpoint wording |

The review window is a review milestone, not completion of the full
specification. That has to be said in writing before the date, not after it.

## P0 — make one delivery reviewable

| Step | Acceptance criterion | State |
| --- | --- | --- |
| Compact review pack generator | Deterministic top-K shortlist, redacted paths, SHA-256 manifest, unit tests, runbook | done in this branch |
| Known-findings comparison | Identity match by `finding_id` or `rule_id` + target, never labelled a new defect | done in this branch |
| Triage funnel and data-gap split | Funnel counts in every pack; findings with no statement or locator routed to the model authors, not the reviewer | done in this branch |
| Expert decision form | One semicolon-separated CSV per delivery, four allowed decisions, one expert in 60-90 minutes | done in this branch |
| Manual baseline refresh workflow | Dispatch-only job that re-runs ruff, mypy, pytest, vitest and build fatally before minting the pin | done in this branch |
| Defect-injection rerun on current HEAD | Recall run recorded with input digests and `source_content_hashed=true` | open |
| Intake and export blockers | Live artifacts from a clean-storage rehearsal, not code reading | open |
| Delivery with a receipt | Named recipient, timestamp and channel stored next to the pack digest | open |
| One expert decision round | 10-25 findings delivered, decisions returned per finding | open |
| Public wording alignment | Repository description and deck repeat the checkpoint wording used here | open |

P0 exit condition: one customer expert has returned decisions for a delivered
shortlist, and those decisions are stored with the source report digest.

## Facts to quote correctly

Misquoting our own evidence is the fastest way to lose a technical reviewer.

- the runtime baseline pin is minted only in CI; quote `commit_sha`,
  `tests_collected`, `tests_passed`, and `tests_skipped` from
  `docs/evidence/runtime-baseline-latest.json` and never a local run or a
  copied integer from this plan;
- the defect-injection experiment covered part of the planned mutation classes
  and produced a recall point estimate of 0.0 with a Wilson upper bound near
  0.39; it is an unfinished experiment, not a measured recall;
- MEP system clash stays `NOT_VERIFIED`: the counts are axis-aligned bounding
  box overlaps, the ring is bounded and off by default, and geometric
  intersection is not claimed;
- heavy jobs still run as in-process background tasks, so a crash loses
  in-flight work; that is an open P1 gap, not a solved problem.

## P1 — make the delivery defensible

1. **Atomic export bundle.** One captured snapshot produces JSON, HTML, PDF and
   BCF from the same report and review events, with a manifest and a SHA-256
   per artifact. Acceptance: a single request returns a bundle whose files
   agree on report id, revision and review history; PDF verification asserts
   extracted text, not raw bytes.
2. **Durable worker and queue.** Replace background tasks as the only hard
   profile executor. Acceptance: request payload is reconstructable after a
   crash, leases and heartbeats are explicit, retries and a dead letter exist,
   stage progress and mid-stage cancellation are observable.
3. **Zero-egress on-prem package.** Acceptance: a rehearsal on a clean host
   with no outbound network produces a full run and an export bundle, with the
   network denial recorded.
4. **Exchange contract.** Acceptance: a documented, versioned schema for
   findings, decisions and evidence references, with a contract test that fails
   on breaking change.
5. **Signed acceptance profile.** Acceptance: thresholds, scope and sampling
   agreed in writing before the measurement run, not after.
6. **Current demonstration set.** Acceptance: the deck and demo match the
   current checkpoint wording and carry no unverified capability claims.

## P2 — pilot measurement over 30-60 days

Measure and publish per scenario: precision and recall against expert
decisions, share of findings with complete provenance, wall-clock time at
customer scale, operator effort per package, and the number of findings
rejected as false positives. Only a completed protocol may change
`accuracy_claim` or `sla_claim` from `NOT_ESTABLISHED`.

## Rules that do not bend

- Test counts, fixture scores and passing gates are code health, never customer
  accuracy.
- A BCF archive is not a CDE import; a queue in memory is not durable
  execution; raw overlap counts are not verified clashes.
- Baseline overlap is not recall, and a shortlist is not an acceptance act.
- A pack that was generated but not delivered counts as not delivered.
- `summary.passed` is a machine outcome and never customer acceptance.
- No blocker closes on inspection alone; each needs an artifact produced by a
  run that a reviewer can repeat.
