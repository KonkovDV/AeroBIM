# Dataset catalog (2026)

**Not** a customer production corpus. Classes: FIXTURE / SYNTHETIC / PUBLIC_REAL / EDUCATIONAL / CUSTOMER_CONFIDENTIAL.

| Dataset | Type | Ground truth | License | Public benchmark | Risk |
|---|---|---|---|---|---|
| `samples/ifc/*`, `samples/ids/*` (AeroBIM) | FIXTURE | partial | LicenseRef-AeroBIM-Fixture | yes | low |
| Sprint 2.1 pack + mutations / Sprint2 GT | FIXTURE+SYNTHETIC | mutation SSOT | fixture | yes | low |
| Level B injected defects | SYNTHETIC | yes | fixture | yes | honesty anchors |
| buildingSMART IDS TestCases | PUBLIC_REAL | official binary cases | **CC BY-ND 4.0** | regression only | low (pin+NOTICE) |
| buildingSMART BCF/IDS XSD | PUBLIC_REAL | schemas | **CC BY-ND 4.0** | schema validation | low (RT-W-01) |
| **IFC-Bench v2** (Hellin) | PUBLIC_REAL | 1027 QA | QA **CC BY 4.0**; models per-file | open_bench_only when scored | pin: `samples/benchmarks/ifc-bench-v2/`; exclude GPLv3 models from MIT tree |
| KAAN / OSArch / BatchPlan / ArchCAD / FloorPlanCAD / CODE-ACCORD | PUBLIC / research | varies | **PARTIAL — open primary license** | pin_or_link_only | license |
| Минстрой типовая ПД / реестр повторного применения | PUBLIC_META | none | N/A | **DEAD_CHANNEL** (no file download) | use Renga instead |
| Renga / ПНСТ 909 open sets | PUBLIC_REAL (link) | none in-repo | vendor ToS | **PRIORITY** → `.local/renga-pnst909/` | Exp A + 22 IDS scenarios |
| CubiCasa5K / CVC-FP | PUBLIC / research | via AECV only | UNKNOWN until cleared | **INTERNAL_ONLY_LICENSE_REVIEW** | license+PII |
| Customer packs | CUSTOMER_CONFIDENTIAL | expert | NDA | never public | RT-001 |

Inventory: [`docs/dataset/OPEN_SOURCE_CORPUS_INVENTORY_2026_08.md`](dataset/OPEN_SOURCE_CORPUS_INVENTORY_2026_08.md) · Search pass: [`docs/dataset/OPEN_SOURCE_SEARCH_RESULTS_2026_08_04.md`](dataset/OPEN_SOURCE_SEARCH_RESULTS_2026_08_04.md).

**Synthetic policy:** do not draw toy geometry from scratch — plant errors on real IFC (+ BatchPlan plans) when expanding the measurable corpus.

SSOT manifests: `samples/DATASET_MANIFEST.json`, `samples/benchmarks/sprint-2-1/manifest.json`, `samples/benchmarks/sprint-2-1/source-provenance.json`.

Do not call open educational IFC «production corpus».
