---
title: "Customer review pack — compact delivery runbook"
status: active
version: "1.1.0"
last_updated: "2026-09-10"
claim_boundary: >
  Operator runbook only. A generated shortlist is not customer acceptance,
  product accuracy, SLA evidence, CDE import, or contractual fitness.
---

# Customer review pack

This runbook turns the public server report JSON into a compact, whitelisted
shortlist for one customer expert. It does not re-run analysis and does not
change `summary.passed`.

## Inputs

- report JSON from `GET /v1/reports/{report_id}/export/json`;
- optionally, a known-findings JSON with either `findings[]` or
  `cases[].findings[]` containing stable `finding_id` or `rule_id` +
  `target_ref`/`element_guid` identity.

Do not put customer files or generated customer packs in the public repository.
Run in the approved local/on-prem storage boundary.

## Command

```bash
cd backend
python -m aerobim.tools.build_customer_review_pack \
  --report-json ../.local/customer/report.json \
  --known-findings-json ../.local/customer/known-findings.json \
  --top-k 20 \
  --output-dir ../.local/customer/review-pack
```

If no baseline is available, omit `--known-findings-json`.

Optional flags:

- `--strict-evidence` — keep only findings that carry both an observed and an
  expected value; use it for a first delivery to a sceptical reviewer;
- `--keep-duplicates` — disable family collapsing when the reviewer wants to
  see repetition volume;
- `--include-needs-data` — mix findings without a statement or a locator back
  into the shortlist; off by default on purpose.

## Outputs

- `customer-review.md` — decision-first one-pager: scope, machine verdict,
  triage funnel, what was not checked, findings table;
- `customer-review.json` — whitelisted machine-readable cards;
- `customer-review-form.csv` — one decision row per finding, semicolon
  separated and UTF-8 with BOM so it opens directly in Excel; the reviewer
  fills `decision`, `comment`, `reviewer`, `decided_at`;
- `manifest.json` — source-report digest and output SHA-256 values.

The generator excludes terminal `rejected`, `waived`, and `superseded`
findings from the active candidates. It ranks accepted findings first, then
`deterministic` before `advisory`, then severity, evidence completeness,
priority and stable identity. Raw confidence is extraction confidence, never
probability of a true defect.

## Triage funnel

Both the JSON and the one-pager carry the funnel, so the customer can see how
a large machine run became a short list:

| Stage | Meaning |
| --- | --- |
| `machine_findings` | findings as reported by the run |
| `terminal_excluded` | already rejected, waived or superseded in review |
| `needs_data_deferred` | no statement or no locator, moved to the data-gap list |
| `incomplete_evidence_excluded` | dropped by `--strict-evidence` |
| `duplicates_collapsed` | same rule, category, severity and element type |
| `shortlisted` | what the expert is actually asked to decide |

Evidence completeness per finding is `full`, `partial`, `statement_only` or
`insufficient`. Only `full` carries both an observed and an expected value, so
only `full` findings are safe to argue against a normative clause.

## Data gaps are not defects

`needs_data` collects findings with no statement or no locator. Typical causes
are export defects rather than design errors: empty `NetFloorArea`, a missing
`IfcGrid`, or a translator that drops property sets. Send that list to the
model authors. Never show it to a reviewer as a confirmed defect.

## Known-findings coverage

`known_baseline.coverage_ratio` is the share of supplied baseline findings that
match an active candidate by deterministic identity key, measured over all
active candidates and not only the shortlist. It is not recall, not precision
and not accuracy: identity keys differ between authoring tools, and a remark
book written by a human rarely carries machine identity at all. Present it as
"overlap with the remarks you already know" and keep
`accuracy_claim=NOT_ESTABLISHED`.

## Expert decisions

Use only `confirmed`, `false_positive`, `needs_context`, or `already_known`.
`candidate_not_in_baseline` means only that no deterministic identity key
matched. It must never be described as a new defect until an expert confirms it.

Use one expert for all top-K findings now, in a single 60-90 minute pass. Use a
second reviewer or adjudicator for a random/disputed subset in the 30-60 day
pilot; inter-rater agreement belongs to the pilot protocol, not to this pack.

## Delivery

- generate inside the approved on-prem/offline boundary, with no outbound model
  calls, and keep every output out of the repository;
- deliver over a channel that returns a receipt, and record who received the
  pack and when: a pack that was produced but not delivered counts as not
  delivered;
- state explicitly what was not run, including packages skipped for size or
  format and any drawing that timed out;
- keep the two windows separate. The shortlist and a two-page summary go out in
  the review window; the versioned delivery set (offline bundle, checksums,
  SBOM, format matrix, run log, recovery scenario) follows in the delivery
  window.

## Required delivery note

Every delivery must retain:

- `customer_acceptance=NOT_EVALUATED` until explicit customer acceptance;
- `accuracy_claim=NOT_ESTABLISHED` until a labelled protocol is complete;
- `sla_claim=NOT_ESTABLISHED` until an agreed customer-scale run is measured.

## What the pack answers for the evaluation criteria

| Criterion | What this pack supplies |
| --- | --- |
| Technical result | shortlist with observed and expected values, locator, norm clause |
| Reproducibility | source-report digest, per-file SHA-256, fixed CLI flags |
| Honesty of scope | funnel, `not_evaluated_or_unverified`, separate data-gap list |
| Customer usefulness | one decision form, four decisions, no report wall |
| Readiness | what is delivered now versus what stays not established |

## Repository gate output for this tool

On branch commit `2c5a2911eaf79fa7e1e99b400db4aed94759770d` the repository
toolchain, installed from the pinned development lock file, reported:

- `python -m ruff format --check src tests` — exit 0, 822 files already
  formatted;
- `python -m ruff check src tests` — exit 0, all checks passed;
- `python -m mypy src/aerobim --strict --ignore-missing-imports` — exit 0,
  443 source files;
- `python -m pytest tests/test_build_customer_review_pack.py -q` — exit 0,
  2 passed.

The `1.1.0` triage extension was developed against an isolated Python harness
where only the unit tests could be executed (3 passed). `ruff`, `mypy` and the
full suite run in pull-request CI for this branch; read the results there
before quoting any of them.

These are code-health gates for the generator itself. They do not establish
product accuracy, customer acceptance, SLA at customer scale, or CDE import,
and they do not change any open blocker.
