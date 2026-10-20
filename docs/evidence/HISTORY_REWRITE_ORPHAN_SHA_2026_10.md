<!-- claims-lint: allow-file reason="Evidence note: orphan SHA after main rewrite; Checkpoint GO; customer_go false" -->
---
title: "History rewrite — orphan evidence SHA"
status: active
version: "1.1.0"
last_updated: "2026-10-20"
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


## Known orphan / pre-rewrite pins (do not cite as HEAD)

| SHA (short) | Former role | Status on current `main` |
|---|---|---|
| `313e050505c6` | runtime-baseline pin 2026-09-23 | orphan — replaced by CI pin on `d7a0290` (and successors) |
| `8f0a462d` | historical CI speech pin 15.09 | documentary on full deck; not HEAD |
| `4742d56d` | older CI pin cited in speech lock | documentary |
| `f2615e7` / `c0c4b2b` / `64c69b4` | freeze notes in audit reports | documentary after rewrite |
| `1a5c03e` (tag `pilot-2026-pre`) | frozen pre-pilot baseline | gone — neither the tag nor the commit is on the remote; cite the CI pin |

Evidence files that mention these SHAs stay in git; treat them as **historical**, not live attestation.
