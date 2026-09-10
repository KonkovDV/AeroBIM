---
title: "Customer review pack — compact delivery runbook"
status: active
version: "1.0.0"
last_updated: "2026-09-09"
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

## Outputs

- `customer-review.md` — concise human-review surface;
- `customer-review.json` — whitelisted machine-readable cards;
- `manifest.json` — source-report digest and output SHA-256 values.

The generator excludes terminal `rejected`, `waived`, and `superseded`
findings from the active top-K. It ranks accepted findings first, then
`deterministic` before `advisory`, then severity, priority and stable identity.
Raw confidence is extraction confidence, never probability of a true defect.

## Expert decisions

Use only `confirmed`, `false_positive`, `needs_context`, or `already_known`.
`candidate_not_in_baseline` means only that no deterministic identity key
matched. It must never be described as a new defect until an expert confirms it.

## Required delivery note

Every delivery must retain:

- `customer_acceptance=NOT_EVALUATED` until explicit customer acceptance;
- `accuracy_claim=NOT_ESTABLISHED` until a labelled protocol is complete;
- `sla_claim=NOT_ESTABLISHED` until an agreed customer-scale run is measured.

Use one expert for all top-K findings now. Use a second reviewer or adjudicator
for a random/disputed subset in the 30–60 day pilot.

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

These are code-health gates for the generator itself. They do not establish
product accuracy, customer acceptance, SLA at customer scale, or CDE import,
and they do not change any open blocker.
