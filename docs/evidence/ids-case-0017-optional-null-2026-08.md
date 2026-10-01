---
title: "IDS case 0017 — optional attribute null (upstream edge)"
date: 2026-08-08
claim_level: fixture_only
claim_boundary: >-
  Documents IfcTester vs BSI TestCase filename disagreement. Not product accuracy.
  Do not claim AeroBIM IDS 100% by excluding this case silently.
---

# IDS case 0017 — optional attribute passes if null

## Case

| Field | Value |
|---|---|
| Path | `samples/ids/buildingsmart-testcases/cases/0017/` |
| IDS | optional attribute `Name` must be `Foobar` if present |
| IFC | single `IfcWall` with `Name=$` (null) |
| BSI filename expectation | **pass** |
| IfcTester / AeroBIM adapter | **fail** (issues emitted) |

## Reproduction (AeroBIM adapter = thin IfcTester wrap)

```text
python -c "from pathlib import Path; from aerobim.infrastructure.adapters.ifc_tester_ids_validator import IfcTesterIdsValidator; \
p=Path('samples/ids/buildingsmart-testcases/cases/0017'); \
issues=IfcTesterIdsValidator().validate(p/'pass-an_optional_attribute_passes_if_null.ids', p/'pass-an_optional_attribute_passes_if_null.ifc'); \
print(len(issues), issues[0].message if issues else 'PASS')"
```

Observed class of message: `The attribute value "None" is empty` on optional `Name` facet.

## Classification

**upstream IDS / IfcTester edge** — not an AeroBIM IFC parser crash and not expertise accuracy.

buildingSMART attribute-facet docs say optional+value means: *if the attribute exists, it must match*. TestCase scripts still name the null case `pass-…`. Related upstream discussion: optionality vs emptiness (e.g. IDS issues on optional facets / empty values).

## Policy

| Do | Don't |
|---|---|
| Keep 0017 in sample denominator (honest 23/24) | Patch adapter to force-pass for marketing 100% |
| Point to `KNOWN_UPSTREAM_EDGES.json` | Sell sample match-rate as customer precision |
| Track IfcOpenShell/ifctester upgrades | Claim RT-001 closed |

Registry: [`samples/ids/buildingsmart-testcases/KNOWN_UPSTREAM_EDGES.json`](../../samples/ids/buildingsmart-testcases/KNOWN_UPSTREAM_EDGES.json)
