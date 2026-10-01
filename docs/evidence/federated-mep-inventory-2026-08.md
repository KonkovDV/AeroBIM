<!-- claims-lint: allow-file reason="Federated MEP inventory; clash NOT_VERIFIED" -->
---
title: "Federated MEP inventory"
date: 2026-08-13
claim_level: federated_mep_inventory
claim_boundary: >-
  Public federated / MEP IFC on disk. Entity counts plus AABB broadphase on the in-repo HVAC fixture (existing graph + AABB filter) and duplex architecture-vs-MEP product AABBs. AABB overlap is not geometric clash. mep_system_clash remains NOT_VERIFIED. Not RT-003 delivered. Not customer MEP. GPLv3 IFC-Bench models are not opened.
---

# Federated MEP inventory

- present/run: **17**
- mep_system_clash: **NOT_VERIFIED**
- closes_rt003: **False**
- content_sha256: `d875af14f1f177ac27d64fd12ac9d700b635190ca9b2c80e8971ab017ec54c0b`
- HVAC graph+AABB: `{"status": "RUN", "geometry_verified": false, "nodes": 2, "edges": 1, "synthetic": true, "aabb_status": "unavailable", "aabb_reason": "no element AABBs built (missing geometry / create_shape failed) — falling back to co_presence/connects edges", "aabb_boxes_built": 0, "aabb_pairs_before": 1, "aabb_pairs_after": 0, "elapsed_ms": 3.593}`
- duplex AABB: `{"status": "RUN", "geometry_verified": false, "arc_boxes": 116, "mep_boxes": 548, "aabb_overlap_pairs": 654, "arc_types": ["IfcWall", "IfcSlab", "IfcDoor", "IfcWindow"], "mep_types": ["IfcFlowTerminal", "IfcEnergyConversionDevice", "IfcFlowSegment"], "elapsed_ms": 11351.468}`

| label | status | schema | IfcFlowTerminal | IfcSystem | products | ms |
| --- | --- | --- | --- | --- | --- | --- |
| eng_fixture | RUN | IFC4 | 0 | 2 | 2 | 261.562 |
| ifc_bench_duplex_mep | RUN | IFC2X3 | 105 | 0 | 973 | 915.271 |
| ifc_bench_duplex_arc | RUN | IFC2X3 | 0 | 0 | 295 | 80.567 |
| ifc_bench_dental_mep | RUN | IFC2X3 | 3053 | 0 | 16542 | 22103.782 |
| ifc_bench_dental_str | RUN | IFC2X3 | 0 | 0 | 1100 | 996.869 |
| ifc_bench_digital_hub | RUN | IFC4 | 0 | 0 | 1026 | 381.864 |
| ifc_bench_digital_hub_heating | RUN | IFC4 | 63 | 42 | 5560 | 1028.541 |
| ifc_bench_digital_hub_plumbing | RUN | IFC4 | 74 | 19 | 3120 | 1159.238 |
| ifc_bench_digital_hub_ventilation | RUN | IFC4 | 148 | 4 | 3971 | 701.715 |
| ifc_bench_wbdg_office_mep | RUN | IFC2X3 | 1456 | 0 | 5900 | 3203.217 |
| ifc_bench_west_riverside_arc_ifc4 | RUN | IFC4 | 0 | 0 | 15316 | 4120.189 |
| ifc_bench_west_riverside_mech_ifc4 | RUN | IFC4 | 0 | 466 | 59215 | 4053.138 |
| ifc_bench_west_riverside_plumb_ifc4 | RUN | IFC4 | 0 | 65 | 26942 | 1196.303 |
| ifc_bench_west_riverside_elec_ifc4 | RUN | IFC4 | 1410 | 221 | 6305 | 236.523 |
| ifc_bench_west_riverside_fire_ifc4 | RUN | IFC4 | 0 | 21 | 874 | 42.244 |
| ifc_bench_west_riverside_sprinkle_ifc4 | RUN | IFC4 | 1354 | 17 | 38255 | 2017.311 |
| ifc_bench_west_riverside_str_ifc4 | RUN | IFC4 | 0 | 0 | 2915 | 334.814 |

Public models measured here are **not** MEP delivered and **not** a 0.5 s teaching-pack claim.

```bash
cd backend
python -m aerobim.tools.run_federated_mep_inventory
```
