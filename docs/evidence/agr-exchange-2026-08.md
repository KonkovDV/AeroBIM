<!-- claims-lint: allow-file reason="AGR exchange fixture; not moscow_agr profile" -->
---
title: "AGR exchange-shape fixture (class 1)"
date: 2026-08-13
claim_level: agr_exchange_fixture
claim_boundary: >-
  AGR exchange-shape checks on a fixture (class 1). Not moscow_agr profile. Not УКЭП. Not CRS. Not MSSK. Not customer CIM acceptance.
---

# AGR exchange-shape fixture

IFC4 + ReferenceView + no `IfcBuildingElementProxy` + five-field filename + 
500 MB cap. **Not** the frozen `moscow_agr` profile (no УКЭП, CRS, MSSK).

- cases: **5**
- matching expect: **5**
- content_sha256: `346b9b73f65c0464ed9936689c0e3b83ac1fc00bd5e1ed5b388fc82b6dc37293`

| id | expect | observed | match |
| --- | --- | --- | --- |
| `pass-ifc4-referenceview` | `[]` | `[]` | True |
| `fail-design-transfer-view` | `['AEROBIM-AGR-REFERENCE-VIEW']` | `['AEROBIM-AGR-REFERENCE-VIEW']` | True |
| `fail-ifc4x3-schema` | `['AEROBIM-AGR-IFC-SCHEMA']` | `['AEROBIM-AGR-IFC-SCHEMA']` | True |
| `fail-building-element-proxy` | `['AEROBIM-AGR-PROXY-BANNED']` | `['AEROBIM-AGR-PROXY-BANNED']` | True |
| `fail-filename-shape` | `['AEROBIM-AGR-FILENAME']` | `['AEROBIM-AGR-FILENAME']` | True |

```bash
cd backend
python -m aerobim.tools.run_agr_exchange_fixture
```
