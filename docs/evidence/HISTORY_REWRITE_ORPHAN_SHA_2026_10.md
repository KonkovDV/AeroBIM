<!-- claims-lint: allow-file reason="Evidence note: orphan SHA after main rewrite; Checkpoint GO; customer_go false" -->
---
title: "History rewrite — orphan evidence SHA"
status: active
version: "1.0.0"
last_updated: "2026-10-15"
---

# History rewrite (2026-10-01) — orphan evidence SHA

On 2026-10-01 `main` was rewritten to a short signed history. Git objects such as
`313e050505c6…` (runtime baseline pin generated 2026-09-23) **are not** ancestors
of current `main`. Evidence JSON/MD files that cite those SHAs remain in the tree
as historical pins; they must not be quoted as «на HEAD».

**Citeable HEAD pin:** [`runtime-baseline-latest.json`](runtime-baseline-latest.json)
must have `attestation.attested_by=ci`, `publishable=true`, and a `commit_sha`
that exists in the current `main` graph (`git merge-base --is-ancestor <sha> origin/main`).
Numbers (tests_passed / frontend) come only from that file — never from memory
or from a pre-rewrite deck slide.

Checkpoint `GO` (`regulatory_measurement_mvp`); `customer_go` false.
