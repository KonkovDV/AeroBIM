<!-- claims-lint: allow-file reason="AGR exchange fixture; not moscow_agr profile" -->
---
title: "AGR exchange-shape fixture (class 1)"
date: 2026-08-14
claim_level: agr_exchange_fixture
claim_boundary: >-
  AGR exchange-shape checks on a fixture (class 1). Not moscow_agr profile. Not УКЭП. Not CRS. Not MSSK. Not official TEP XML schema. Not customer CIM acceptance.
---

# AGR exchange-shape fixture

IFC4 + ReferenceView + no `IfcBuildingElementProxy` + five-field filename + 
500 MB cap + optional TEP XML sidecar presence. **Not** the frozen 
`moscow_agr` profile (no УКЭП, CRS, MSSK, official TEP schema).

- cases: **7**
- matching expect: **7**
- content_sha256: `68c1fbbc14b4bcd44f73cbf3fae36ed2583a512006f8be98976f3727dcbb9e42`

| id | expect | observed | match |
| --- | --- | --- | --- |
| `pass-ifc4-referenceview` | `[]` | `[]` | True |
| `fail-design-transfer-view` | `['AEROBIM-AGR-REFERENCE-VIEW']` | `['AEROBIM-AGR-REFERENCE-VIEW']` | True |
| `fail-ifc4x3-schema` | `['AEROBIM-AGR-IFC-SCHEMA']` | `['AEROBIM-AGR-IFC-SCHEMA']` | True |
| `fail-building-element-proxy` | `['AEROBIM-AGR-PROXY-BANNED']` | `['AEROBIM-AGR-PROXY-BANNED']` | True |
| `fail-filename-shape` | `['AEROBIM-AGR-FILENAME']` | `['AEROBIM-AGR-FILENAME']` | True |
| `fail-tep-xml-missing` | `['AEROBIM-AGR-TEP-XML']` | `['AEROBIM-AGR-TEP-XML']` | True |
| `pass-tep-xml-sidecar` | `[]` | `[]` | True |

```bash
cd backend
python -m aerobim.tools.run_agr_exchange_fixture
```
