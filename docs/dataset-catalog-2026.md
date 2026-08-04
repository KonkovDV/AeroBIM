# Dataset catalog (2026)

**Not** a customer production corpus. Classes: FIXTURE / SYNTHETIC / PUBLIC_REAL / EDUCATIONAL / CUSTOMER_CONFIDENTIAL.

| Dataset | Type | Ground truth | License | Public benchmark | Risk |
|---|---|---|---|---|---|
| `samples/ifc/*`, `samples/ids/*` (AeroBIM) | FIXTURE | partial | LicenseRef-AeroBIM-Fixture | yes | low |
| Sprint 2.1 pack + mutations | FIXTURE+SYNTHETIC | mutation SSOT | fixture | yes | low |
| Level B injected defects | SYNTHETIC | yes | fixture | yes | honesty anchors |
| buildingSMART IDS TestCases | PUBLIC_REAL | official binary cases | **CC BY-ND 4.0** | regression only | low (pin+NOTICE) |
| buildingSMART BCF/IDS XSD | PUBLIC_REAL | schemas | **CC BY-ND 4.0** | schema validation | low (RT-W-01) |
| Минстрой типовая ПД | PUBLIC_REAL (link) | none in-repo | portal ToS TBD | **pin_or_link_only** | license |
| Renga / ПНСТ 909 open sets | PUBLIC_REAL (link) | none in-repo | vendor TBD | **pin_or_link_only** | license |
| CubiCasa5K / CVC-FP / FloorPlanCAD | PUBLIC / research | via AECV only | UNKNOWN until cleared | **INTERNAL_ONLY_LICENSE_REVIEW** | license+PII |
| Customer packs | CUSTOMER_CONFIDENTIAL | expert | NDA | never public | RT-001 |

Inventory detail: [`docs/dataset/OPEN_SOURCE_CORPUS_INVENTORY_2026_08.md`](dataset/OPEN_SOURCE_CORPUS_INVENTORY_2026_08.md).

SSOT manifests: `samples/DATASET_MANIFEST.json`, `samples/benchmarks/sprint-2-1/manifest.json`, `samples/benchmarks/sprint-2-1/source-provenance.json`.

Do not call open educational IFC «production corpus».
