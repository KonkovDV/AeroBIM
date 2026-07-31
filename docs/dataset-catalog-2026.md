# Dataset catalog (2026)

**Not** a customer production corpus. Classes: FIXTURE / SYNTHETIC / PUBLIC_REAL / EDUCATIONAL / CUSTOMER_CONFIDENTIAL.

| Dataset | Type | Ground truth | License | Public benchmark | Risk |
|---|---|---|---|---|---|
| `samples/ifc/*`, `samples/ids/*` | FIXTURE | partial | LicenseRef-AeroBIM-Fixture | yes | low |
| Sprint 2.1 pack | FIXTURE+SYNTHETIC | mutation SSOT | fixture | yes | low |
| Level B injected defects | SYNTHETIC | yes | fixture | yes | honesty anchors |
| buildingSMART Sample-Test-Files | PUBLIC_REAL | official cases | UNKNOWN until cleared | INTERNAL_ONLY_LICENSE_REVIEW | license |
| Schependomlaan / Duplex / Clinic | PUBLIC_REAL | limited | UNKNOWN | INTERNAL_ONLY_LICENSE_REVIEW | license |
| CubiCasa5K / FloorPlanCAD / DrawingVQA | PUBLIC / research | varies | UNKNOWN | INTERNAL_ONLY_LICENSE_REVIEW | license+PII |
| Customer packs | CUSTOMER_CONFIDENTIAL | expert | NDA | never public | RT-001 |

SSOT manifests: `samples/DATASET_MANIFEST.json`, `samples/benchmarks/sprint-2-1/manifest.json`, `audit/dataset_license_manifest.json`.

Do not call open educational IFC «production corpus».
