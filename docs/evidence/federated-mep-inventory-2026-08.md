<!-- claims-lint: allow-file reason="Federated MEP inventory; clash NOT_VERIFIED" -->
---
title: "Federated MEP inventory"
date: 2026-08-13
claim_level: federated_mep_inventory
claim_boundary: >-
  Inventory of public federated / MEP IFC on disk. Entity counts only. mep_system_clash remains NOT_VERIFIED. Not RT-003 delivered. Not customer MEP. GPLv3 IFC-Bench models are not opened.
---

# Federated MEP inventory

- present/run: **3**
- mep_system_clash: **NOT_VERIFIED**
- closes_rt003: **False**
- content_sha256: `8fd35e814cb0fd54ea60e80cecd5f8636c4c3a422d24dbe2fafb422866291aa5`

| label | status | schema | IfcFlowTerminal | IfcSystem | products | ms |
| --- | --- | --- | --- | --- | --- | --- |
| eng_fixture | RUN | IFC4 | 0 | 2 | 2 | 142.914 |
| ifc_bench_duplex_mep | RUN | IFC2X3 | 105 | 0 | 973 | 556.306 |
| ifc_bench_duplex_arc | RUN | IFC2X3 | 0 | 0 | 295 | 76.354 |
| ifc_bench_digital_hub | SKIPPED |  |  |  |  | 0.428 |
| ifc_bench_west_riverside | SKIPPED |  |  |  |  | 0.203 |

Public models measured here are **not** MEP delivered and **not** a 0.5 s teaching-pack claim.

```bash
cd backend
python -m aerobim.tools.run_federated_mep_inventory
```
