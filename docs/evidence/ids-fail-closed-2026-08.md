<!-- claims-lint: allow-file reason="IDS fail-closed evidence; BSI case names are measurements not product claims" -->
---
title: "IDS fail-closed gate (ifcVersion vs FILE_SCHEMA)"
date: 2026-08-13
claim_level: ids_fail_closed_gate
claim_boundary: >-
  AeroBIM fail-closes IDS ifcVersion vs IFC FILE_SCHEMA and IfcTester SKIPPED specs. buildingSMART case 0101 documents version-as-metadata; we disagree on purpose. Not product accuracy. Not CIM compliance. Not Samolet acceptance.
---

# IDS fail-closed — silent skip closed

IfcTester records `is_ifc_version` but still executes the spec
(`should_filter_version` defaults to false). buildingSMART case 0101
says version is metadata. AeroBIM emits `AEROBIM-IDS-IFC-VERSION`
and treats SKIPPED specs as FAILED under the IDS contour.

## Measured

- BSI pairs discovered: **290**
- Schema-mismatch pairs: **9**
- `pass-*` filename + schema mismatch: **6**
- Case 0101 `AEROBIM-IDS-IFC-VERSION`: **True**
- content_sha256: `94db20d230714159177828f7d4f8fd25b152c9577c9f1a5da40056e1043b3162`

## Canonical live case 0101

- issues: 1
- elapsed_ms: 561.109
- rule_ids: ['AEROBIM-IDS-IFC-VERSION']

## `pass-*` cases our gate fails (intentional)

| case_id | dir | FILE_SCHEMA |
| --- | --- | --- |
| `pass-a_specification_passes_only_if_all_requirements_pass_2_2` | 0096 | `IFC4` |
| `pass-optional_specifications_may_still_pass_if_nothing_is_applicable` | 0097 | `IFC4` |
| `pass-prohibited_specifications_passes_if_the_applicability_does_not_matches` | 0098 | `IFC4` |
| `pass-required_specifications_need_at_least_one_applicable_entity_1_2` | 0099 | `IFC4` |
| `pass-specification_optionality_and_facet_optionality_can_be_combined` | 0100 | `IFC4` |
| `pass-specification_version_is_purely_metadata_and_does_not_impact_pass_or_fail_result` | 0101 | `IFC4` |

Labeled in `samples/ids/buildingsmart-testcases/AEROBIM_FAIL_CLOSED_DIVERGENCES.json`.
Do not treat this list as product accuracy.

```bash
cd backend
python -m aerobim.tools.export_ids_fail_closed_gate
```
