<!-- claims-lint: allow-file reason="AGR exchange fixture; not moscow_agr profile" -->
---
title: "AGR exchange-shape fixture (class 1)"
date: 2026-08-14
claim_level: agr_exchange_fixture
claim_boundary: >-
  AGR exchange-shape checks on a fixture (class 1). Not moscow_agr profile. Not УКЭП. Not CRS. Not MSSK. Official ДГП TEP example + Vedomost XSD are public city files, not a Samolet-signed acceptance pack. Not customer CIM acceptance.
---

# AGR exchange-shape fixture

IFC4 + ReferenceView + no `IfcBuildingElementProxy` + five-field filename + 
500 MB cap + TEP XML sidecar + official ДГП Vedomost XSD. **Not** the frozen 
`moscow_agr` profile (no УКЭП, CRS, MSSK). Not a Samolet pack.

- cases: **11**
- matching expect: **11**
- content_sha256: `d24b8e7be463a50844f5bd4d2e5efc9c492b645857bfc7ba24bbc11654a207cf`

| id | expect | observed | match |
| --- | --- | --- | --- |
| `pass-ifc4-referenceview` | `[]` | `[]` | True |
| `fail-design-transfer-view` | `['AEROBIM-AGR-REFERENCE-VIEW']` | `['AEROBIM-AGR-REFERENCE-VIEW']` | True |
| `fail-ifc4x3-schema` | `['AEROBIM-AGR-IFC-SCHEMA']` | `['AEROBIM-AGR-IFC-SCHEMA']` | True |
| `fail-building-element-proxy` | `['AEROBIM-AGR-PROXY-BANNED']` | `['AEROBIM-AGR-PROXY-BANNED']` | True |
| `fail-filename-shape` | `['AEROBIM-AGR-FILENAME']` | `['AEROBIM-AGR-FILENAME']` | True |
| `fail-tep-xml-missing` | `['AEROBIM-AGR-TEP-XML']` | `['AEROBIM-AGR-TEP-XML']` | True |
| `pass-tep-xml-sidecar` | `[]` | `[]` | True |
| `pass-tep-official-root` | `[]` | `[]` | True |
| `fail-tep-wrong-root` | `['AEROBIM-AGR-TEP-ROOT']` | `['AEROBIM-AGR-TEP-ROOT']` | True |
| `pass-vedomost-xsd` | `[]` | `[]` | True |
| `fail-vedomost-xsd` | `['AEROBIM-AGR-VEDOMOST-XSD']` | `['AEROBIM-AGR-VEDOMOST-XSD']` | True |

```bash
cd backend
python -m aerobim.tools.run_agr_exchange_fixture
```
