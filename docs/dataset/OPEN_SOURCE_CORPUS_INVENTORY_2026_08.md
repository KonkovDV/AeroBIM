# Open-source corpus inventory (Sprint 2)

**Date:** 2026-08-04  
**Commit base:** `77a59d7`+  
**claim_level:** inventory only — not product accuracy; Checkpoint **NO_GO**

Rule: same as BSI — verbatim NOTICE + pin, or link-only until license GO. No derivatives without explicit license.

| Source | In repo? | License | Storage | Status | Notes |
|---|---|---|---|---|---|
| buildingSMART IDS TestCases | Yes — `samples/ids/buildingsmart-testcases/` | CC BY-ND 4.0 | Vendored unmodified + NOTICE + IMPORT_PINS (`upstream_commit` `016bbad…`) | **READY** | 290 honest pass/fail pairs; regression only |
| buildingSMART BCF/IDS XSD | Yes — `samples/bcf-xsd/`, `samples/ids-xsd/` | CC BY-ND 4.0 | Vendored + NOTICE + LICENSE | **READY** | RT-W-01 closed; `review_pending=0` |
| AeroBIM fixtures (`samples/ifc`, `samples/ids`, Level-B) | Yes | LicenseRef-AeroBIM-Fixture / MIT repo | In-tree | **READY** | Synthetic / fixture; never customer evidence |
| Минстрой реестр типовой ПД | No | Unclear / government portal ToS | **pin_or_link_only** | **INVENTORY** | Cite letter `4420-КМ/14` in research; do **not** vendor without license GO |
| Renga open sets (ПНСТ 909) | No | Vendor/ToS TBD | **pin_or_link_only** | **INVENTORY** | Mentioned in feasibility docs; 0 samples |
| buildingSMART Sample-Test-Files (IFC) | Partial via IDS TestCases IFC | CC BY-ND 4.0 for TestCases tree | Pin / unmodified | **PARTIAL** | Prefer TestCases tree already pinned |
| CubiCasa5K | No (via AECV upstream only) | Research / check before direct use | **EXTERNAL_PIN** via AECV-Bench | **INTERNAL_ONLY_LICENSE_REVIEW** | Do not copy into `samples/` |
| CVC-FP | No (via AECV) | Research / check | **EXTERNAL_PIN** | **INTERNAL_ONLY_LICENSE_REVIEW** | Same |

## Decisions

1. **Do not vendor** Минстрой / Renga / CubiCasa / CVC-FP in this sprint.  
2. Synthetic Level-B + Sprint mutation SSOT remain the **measurable** GT for baseline PDF.  
3. Customer completed-project + examination conclusion remains the only path to close RT-001.

## Manifest sync

- Root [`samples/DATASET_MANIFEST.json`](../samples/DATASET_MANIFEST.json): `review_pending=0`, 15× `cc_by_nd_4.0`.  
- Sprint provenance [`samples/benchmarks/sprint-2-1/source-provenance.json`](../samples/benchmarks/sprint-2-1/source-provenance.json): aligned to CC BY-ND (was stale `review_pending`).
