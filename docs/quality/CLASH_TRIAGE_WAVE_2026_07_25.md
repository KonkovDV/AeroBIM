---
title: "Clash relevance triage wave (deterministic, advisory)"
status: done
version: "1.0.0"
last_updated: "2026-07-25"
claim_boundary: "Presentation/ordering metadata only. No ML relevance model claimed (RT-001). Never writes summary.passed. Checkpoint stays NO_GO."
---

# Wave B — Clash relevance triage (2026-07-25)

## External anchors (Jul 2026)

| Domain | Anchor |
|---|---|
| Clash relevance filtering | Ailem et al. 2026, *Automation in Construction* (S0926580525006843) — filter/prioritise clashes before review, ISO-aligned |
| Coordination frameworks | Koo et al. 2026, *ASCE JCEM* (JCEMD4.COENG-17676) — staged clash analysis + resolution |
| Atomic verifiable claims | TACO, EACL 2026 (2026.eacl-long.252); Chain-of-Verification — every advisory claim carries verifiable inputs |
| BCF 3.0 consumer | BIMcollab release notes 2026-02-20 — BCF 3.0 **import** now accepted (T2 evidence path for RT-008 stays customer-gated) |

## Delivered (code + test)

- `domain/clash_triage.py` — deterministic triage: symmetric-pair dedup (worst
  instance kept), penetration-depth / clearance-gap bands
  (critical ≥50 mm, major ≥10 mm, minor ≥1 mm hard; gap ≤2 mm major clearance),
  input-order-independent ranking, atomic rationale per item with the exact
  thresholds that justify the band.
- `application/services/spatial_predicates.py` — issues now emit in triage
  order with merged duplicates and provenance (`finding_id`, `source_id`,
  `evidence_refs` incl. `triage:band=…`, `origin=deterministic`). Severity
  policy unchanged (WARNING; ERROR only under `clash_affects_pass`).
- `domain/review_priority.py` — SPATIAL category score + band boost
  (critical 12 / major 6 / minor 2 / negligible 0); reorders review only.
- `tests/test_clash_triage.py` — 13 tests: band thresholds, shuffle-determinism,
  dedup-keeps-worst, no-clash-dropped, severity-policy invariance, priority
  boost, claim-boundary source assertion (module never touches
  `ValidationSummary` / `PackageOutcome`).

## Explicitly NOT claimed

- ML clash-relevance classification (needs customer-labeled corpus — RT-001).
- MEP system-aware clash delivery (RT-003 unchanged, `NOT_VERIFIED`).
- Any change to Shared-gate semantics: triage cannot flip `summary.passed`,
  cannot suppress findings, and negligible items remain visible in the tail.

## Gate evidence (2026-07-25 local)

`ruff format --check` 316 files PASS · `ruff check` PASS · `mypy src` 192 files
PASS · `pytest tests -q` **934 passed, 7 skipped**. Also fixed stale asserts
drifted by the prior uncommitted wave (capabilities `schema_version` 1.3.0,
`NATIVE_DWG_MISSING_REASON` SSOT) and added `defusedxml` mypy override.
