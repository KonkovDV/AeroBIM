<!-- claims-lint: allow-file reason="Official SPb CGE IDS engine coverage; not Samolet profile" -->
# Official SPb GAU CGE IDS 1.0

**claim_level:** `official_ids_engine_coverage`
**customer_accuracy_not_established:** `True`
**closes_rt002_customer_profile:** `False`

Official SPb GAU CGE IDS 1.0 zips (ЦИМ ОКС 3.1.0 + ЦИМ РИИ 1.1.0). Second public GAU jurisdiction pack. Not MosoblGosExpertiza. Not a Samolet-signed acceptance profile. RT-002 stays OPEN.

Source: https://www.spbexp.ru/bim/docs/

## Engine coverage (headline)

| Metric | Count |
| --- | ---: |
| IDS files | 22 |
| Specifications | 356 |
| Executable (IfcTester ran) | 356 |
| Unsupported facets | 0 |
| Load errors | 0 |

## Fixture probe (not CIM compliance)

Open fixture `samples/ifc/wall-pset-qto-pass.ifc`. Fail here means the spec ran.

| Metric | Count |
| --- | ---: |
| Pass on fixture | 195 |
| Fail on fixture | 161 |

Generated at: `2026-08-14T17:07:48.321729+00:00`
content_sha256: `dde568f15d011ed18630918b284d1d5a58dabe30796ed1ece1816a05d1a33e8f`

## Two artifacts, two counters

This file is **specification** pass/fail on the wall fixture (195 / 161 of 356), dated 2026-08-14. `docs/evidence/spb-cge-profile-validation-2026-08.json` is the 2026-08-24 profile integrity run (1543 IfcTester issue rows × 2). One specification can emit many entity-level issues; do not equate 195+161 with 1543. Paths are repo-relative. Host OS fingerprint omitted. Counts were not re-run when paths were stripped.
