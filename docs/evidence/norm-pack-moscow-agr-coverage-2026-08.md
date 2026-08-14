<!-- claims-lint: allow-file reason="Official Moscow AGR IDS engine coverage; not Samolet profile" -->
# Official Moscow AGR IDS (ДГП / СтроимПросто)

**claim_level:** `official_ids_engine_coverage`
**customer_accuracy_not_established:** `True`
**closes_rt002_customer_profile:** `False`

Official Moscow AGR IDS zip from stroimprosto.mos.ru (АР / БиО / ПС / МССК). IfcTester engine coverage on a wall fixture is not CIM AGR acceptance, not УКЭП, and not a Samolet-signed pack. RT-002 stays OPEN.

Source: https://stroimprosto.mos.ru/knowledge/article/cim-agr/

## Engine coverage (headline)

| Metric | Count |
| --- | ---: |
| IDS files | 4 |
| Specifications | 102 |
| Executable (IfcTester ran) | 102 |
| Unsupported facets | 0 |
| Load errors | 0 |

## Fixture probe (not CIM compliance)

Open fixture `samples/ifc/wall-pset-qto-pass.ifc`. Fail here means the spec ran.

| Metric | Count |
| --- | ---: |
| Pass on fixture | 99 |
| Fail on fixture | 3 |

Generated at: `2026-08-14T17:07:47.373106+00:00`
content_sha256: `6c3cc896aa896a49b65472e9906256f51024f630b436e7a0ba0a00347cf1828a`
