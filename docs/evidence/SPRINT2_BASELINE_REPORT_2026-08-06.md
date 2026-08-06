# Sprint 2 baseline report

> # SYNTHETIC/FIXTURE ONLY
> # CUSTOMER ACCURACY NOT ESTABLISHED

**Banner (mandatory):** `SYNTHETIC/FIXTURE ONLY` · `CUSTOMER ACCURACY NOT ESTABLISHED`

- generated_at: `2026-08-06T20:07:18.313444+00:00`
- commit_sha: `d96a59ac6704357336ae46f7d61f6435be4c6a2c`
- claim_level: `synthetic_only`
- customer_precision_claim_publishable: `False`
- precision_claim_publishable: `False`
- customer_accuracy_not_established: `True`
- closes_rt001: `False`
- checkpoint: `NO_GO`
- reproducibility_hash: `74e0eb2727d53cdce0d59cc32973eb425ee59cdf3cfc2f8cafcec1475eb80b86`

## 1. Goal

Synthetic detection baseline on planted fixtures. Checkpoint **NO_GO**. Does not publish product accuracy.

## 2. Commit SHA

`d96a59ac6704357336ae46f7d61f6435be4c6a2c`

## 3. Dataset

- ground_truth: `samples/benchmarks/sprint2-synthetic-ground-truth.json`
- dataset_manifest: `samples/benchmarks/sprint2-dataset/MANIFEST.json`
- dataset_meta: `{"reproducibility_hash": "59f903a936a66625b50ea914241a808f63ea8a4243d20272926fbbe3cd56310f", "case_count": 15, "mode_b_classes": ["cross_document_calc", "drawing_pdf_ocr_degraded", "ifc_ids_property"], "claim_level": "synthetic_only"}`

## 4. License / provenance

Repo MIT fixtures + synthetic planted defects. No customer packs. Mode A open sources referenced inventory-only (not vendored here).

## 5. Ground-truth method

See `docs/pilot/SPRINT2_DETECTION_METRICS_METHOD_2026_08.md`. Match keys from planted_detectable.

## 6. Environment

```json
{
  "python": "3.13.7",
  "platform": "Windows-11-10.0.26200-SP0",
  "implementation": "CPython"
}
```

## 7. Reproduction commands

```
cd backend
.venv\Scripts\python.exe -m aerobim.tools.export_sprint2_dataset_manifest
.venv\Scripts\python.exe -m aerobim.tools.run_sprint2_synthetic_baseline --iterations 1 --dataset-manifest ../samples/benchmarks/sprint2-dataset/MANIFEST.json
```

## 8. Speed table

| metric | value |
|---|---|
| time_per_case_mean_s | 0.457916 |
| time_per_case_p95_s | 2.705935 |

## 9. Quality table

| metric | value |
|---|---|
| TP / FP / FN | 6 / 2 / 0 |
| precision | 0.75 |
| recall | 1.0 |
| Wilson prec lower | 0.409275 |
| Wilson rec lower | 0.609666 |

## 10. Remarks

remarks_count = **6** (deterministic engine findings).

## 11. Clashes

clashes_count = **0**. clashes_count is 0: geometric_clash_between_systems is not_planted_runnable in sprint2-synthetic-ground-truth; do not interpret as product clash quality

## 12. Severity distribution

```json
{
  "error": 4,
  "warning": 3
}
```

## 13. Confusion / detection counts

TP=6 FP=2 FN=0 on planted detectable set (n=6).

## 14. Agreement / nDCG

- agreement: {'status': 'N/A', 'reason': 'No dual-human adjudicator CSV in this synthetic baseline; measure_adjudicator_agreement requires customer/expert labels (RT-001)'}
- ndcg: {'status': 'N/A', 'reason': 'No ranking relevance labels supplied to this runner'}

## 15. Reproducibility hash

`74e0eb2727d53cdce0d59cc32973eb425ee59cdf3cfc2f8cafcec1475eb80b86`

## 16. Capabilities snapshot

```json
{
  "clash": {
    "status": "PARTIAL",
    "note": "fixture path exists; MEP system clash NOT_VERIFIED"
  },
  "ids": {
    "status": "VERIFIED_FIXTURE_ONLY"
  },
  "ifc_validation": {
    "status": "VERIFIED_FIXTURE_ONLY"
  },
  "llm_advisory": {
    "status": "ADVISORY_ONLY",
    "affects_summary_passed": false
  },
  "mep_system_clash": {
    "status": "NOT_VERIFIED"
  },
  "native_dwg": {
    "status": "MISSING"
  },
  "bcf_cde": {
    "status": "PARTIAL",
    "note": "structural export only; not CDE-ready claim"
  },
  "customer_sla": {
    "status": "BLOCKED_BY_CUSTOMER_DATA"
  }
}
```

## 17. Claims boundary

- claim_level=`synthetic_only`
- customer_precision_claim_publishable=`false`
- precision_claim_publishable=`false`
- customer_accuracy_not_established=`true`
- Forbidden: product accuracy, >90%, production-ready, native DWG, delivered MEP clash, calc independence, CDE-ready BCF, customer SLA from fixtures

## 18. TZ map

```json
[
  {
    "tz_class": "geometric_clash_between_systems",
    "coverage": "not_planted_runnable",
    "reason": "hard_clash listed in mutation catalog; no deterministic planted IFC pair in this sprint. RT-003 OPEN for verified MEP clash.",
    "defect_ids": []
  },
  {
    "tz_class": "drawing_model_dimension_mismatch",
    "coverage": "not_planted_runnable",
    "reason": "drawing_annotation_mismatch in catalog; no runnable 2D↔IFC planted pair yet.",
    "defect_ids": []
  },
  {
    "tz_class": "incorrect_space_area",
    "coverage": "partial",
    "defect_ids": [
      "LB-001-load-value-mismatch"
    ],
    "note": "Canonical LOAD row mismatch is measured. Free-text area (LB-004) is known_undetected honesty boundary — not counted as FN for recall of planted detectable errors."
  },
  {
    "tz_class": "missing_element_in_section",
    "coverage": "partial",
    "defect_ids": [
      "LB-007-compensating-entity-presence"
    ],
    "note": "IDS-only class-swap is vacuous pass (honesty). Compensating entity-presence requirement is the planted detectable case."
  },
  {
    "tz_class": "tz_requirement_mismatch",
    "coverage": "measured",
    "defect_ids": [
      "LB-005-ifc-missing-property-relation",
      "LB-006-ifc-wrong-property-value"
    ]
  },
  {
    "tz_class": "specification_model_contradiction",
    "coverage": "measured",
    "defect_ids": [
      "LB-006-ifc-wrong-property-value"
    ],
    "note": "Wrong FireRating vs IDS requirement stands in for spec↔model contradiction on fixture."
  }
]
```

## 19. Limits / next steps

- Synthetic planted defects only; unplanted TZ classes unmeasured
- Ground truth complete by construction for planted detectable set
- No real customer packages
- TZ 90% threshold NOT confirmed
- Does not close RT-001
- Geometric clashes_count=0 by honesty (no planted clash IFC pair)
- Agreement kappa/alpha and nDCG: N/A (no dual-human / ranking labels in this run)

- Next: customer dual adjudication (RT-001), planted clash IFC pair, licensed Mode A corpus under review.

JSON twin: `C:/plans/AeroBIM/docs/evidence/sprint2-baseline-report.json`
