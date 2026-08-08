---
title: "BSI IDS TestCases — known IfcTester upstream edges (batch)"
date: 2026-08-08
claim_level: fixture_only
claim_boundary: >-
  Registry for IfcTester 0.8.x vs BSI pass-* filename disagreements.
  Adjusted BSI regression excludes these by label — NOT product accuracy.
---

# BSI IDS — upstream IfcTester edges (beyond case 0017)

Machine registry: `samples/ids/buildingsmart-testcases/KNOWN_UPSTREAM_EDGES.json` (22 edges as of 2026-08-08).

## Classes

| Class | Count | AeroBIM action |
|---|---:|---|
| `upstream_ids_ifctester_edge` (optional null / empty) | 2 | Document; no force-pass |
| `upstream_ifctester_float_tolerance` | 16 | Document; awaits IfcTester tolerance |
| `upstream_ifctester_or_regex` | 2 | Document; awaits IfcTester OR-pattern fix |
| Adapter mapping gaps (prohibited / zero-applicability) | 2 | **Fixed** in `IfcTesterIdsValidator` 2026-08-08 |

## Adjusted BSI regression (n=290)

- Raw IfcTester agreement: **270/290** (93.1%)
- Known upstream mismatches: **22** (labeled in registry)
- Unexplained mismatches after adapter fix: **0** → `regression_pass=true`

## Reproduce

```bash
cd backend
python -m aerobim.tools.run_open_corpora_profiles --mode full --include-bsi
python -m aerobim.tools.run_sprint3_open_corpus_battery
```

Evidence JSON: `audit/evidence/sprint3-open-corpus-battery-2026-08.json`.
