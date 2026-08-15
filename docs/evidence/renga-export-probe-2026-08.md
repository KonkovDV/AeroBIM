<!-- claims-lint: allow-file reason="Renga publisher IFC probe; not Samolet; NO_GO" -->
---
title: "Renga IFC export probe"
date: 2026-08-15
claim_level: renga_export_probe
claim_boundary: >-
  Header-level probe of one IFC: FILE_SCHEMA, FILE_NAME originating_system, and official MOEXP ifcVersion=IFC4 fail-closed. Publisher PNST 909 sample is not a Samolet export, not product accuracy, not Exp A 18/22 rerun. Vertical-slice demo IFC stays IfcOpenShell. This Renga 8.7 pack sample is FILE_SCHEMA IFC4 (not IFC4X3). IFC4X3 fail-closed remains on the IfcOpenShell fixture. Checkpoint NO_GO.
---

# Renga IFC export probe

Vertical-slice demo IFC is **not** replaced. Publisher PNST 909 sample is **not** a Samolet export. Checkpoint **NO_GO**.

- status: **MEASURED**
- ifc: `.local/renga-pnst909/pack/IFC/pnst909-c14-mf-renga-87.ifc` (103112 bytes)
- ifc_sha256: `c55b39a52cf64950b2d05b0b688a711d98c48d6d7cb56cc4f67fd524e9b90030`
- originating_system: `Renga Professional 8.7.20879.0`
- preprocessor_version: `IfcPlusPlus`
- view_definition: `Renga View`
- originating_family: **renga**
- is_renga_export: **True**
- publisher_pnst909_sample: **True**
- samolet_export: **False**
- FILE_SCHEMA: `IFC4`
- MOEXP IDS: `samples/ids/moexp/pack/oks/IDS_v1.0_Требования_МОГЭ_к_ЦИМ_АР_v3.2.ids`
- schema_mismatch_count: **0** / 20 specs
- schema_fail_closed: **False** (`None`)
- elapsed_ms: 2.506
- content_sha256: `f24eee483f518e9ac0eb7f80a27ff6deecbb8ca944e84ab00be7c008ebc50223`

## Pack header sample (this machine)

- members_sampled: 18 (15 smallest + 3 files ~5MB)
- FILE_SCHEMA counts: `{'IFC4': 18}`
- originating_system: `Renga Professional 8.7.20879.0`

Not a 198-file census. Not proof that Renga never emits IFC4X3.

Not product accuracy. Not Exp A 18/22. Not customer precision.

```bash
cd backend
python -m aerobim.tools.run_renga_export_probe --write-evidence
```
