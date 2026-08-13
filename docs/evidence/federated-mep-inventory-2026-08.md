<!-- claims-lint: allow-file reason="Federated MEP inventory; clash NOT_VERIFIED" -->
---
title: "Federated MEP inventory"
date: 2026-08-13
claim_level: federated_mep_inventory
claim_boundary: >-
  Public federated / MEP IFC on disk. Entity counts plus AABB broadphase on the in-repo HVAC fixture (existing graph + AABB filter) and duplex architecture-vs-MEP product AABBs. AABB overlap is not geometric clash. mep_system_clash remains NOT_VERIFIED. Not RT-003 delivered. Not customer MEP. GPLv3 IFC-Bench models are not opened.
---

# Federated MEP inventory

- present/run: **5**
- mep_system_clash: **NOT_VERIFIED**
- closes_rt003: **False**
- content_sha256: `3ece8ecd31497344bc302f5ddce93ee7b44c1ab01880d94a0d3498ad7049a8d5`
- HVAC graph+AABB: `{"status": "RUN", "geometry_verified": false, "nodes": 2, "edges": 1, "synthetic": true, "aabb_status": "unavailable", "aabb_reason": "no element AABBs built (missing geometry / create_shape failed) — falling back to co_presence/connects edges", "aabb_boxes_built": 0, "aabb_pairs_before": 1, "aabb_pairs_after": 0, "elapsed_ms": 24.45}`
- duplex AABB: `{"status": "RUN", "geometry_verified": false, "arc_boxes": 116, "mep_boxes": 548, "aabb_overlap_pairs": 654, "arc_types": ["IfcWall", "IfcSlab", "IfcDoor", "IfcWindow"], "mep_types": ["IfcFlowTerminal", "IfcEnergyConversionDevice", "IfcFlowSegment"], "elapsed_ms": 13354.01}`

| label | status | schema | IfcFlowTerminal | IfcSystem | products | ms |
| --- | --- | --- | --- | --- | --- | --- |
| eng_fixture | RUN | IFC4 | 0 | 2 | 2 | 187.288 |
| ifc_bench_duplex_mep | RUN | IFC2X3 | 105 | 0 | 973 | 549.58 |
| ifc_bench_duplex_arc | RUN | IFC2X3 | 0 | 0 | 295 | 79.367 |
| ifc_bench_dental_mep | RUN | IFC2X3 | 3053 | 0 | 16542 | 27174.247 |
| ifc_bench_dental_str | RUN | IFC2X3 | 0 | 0 | 1100 | 1342.738 |
| ifc_bench_digital_hub | SKIPPED |  |  |  |  | 0.759 |
| ifc_bench_west_riverside | SKIPPED |  |  |  |  | 1.09 |

Public models measured here are **not** MEP delivered and **not** a 0.5 s teaching-pack claim.

```bash
cd backend
python -m aerobim.tools.run_federated_mep_inventory
```
