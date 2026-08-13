<!-- claims-lint: allow-file reason="MOEXP IDS on GNI student sample; not CIM compliance" -->
---
title: "MOEXP IDS on a GNI student IFC"
date: 2026-08-13
claim_level: gni_student_vs_official_ids
claim_boundary: >-
  Official MOEXP IDS executed on one GNI student IFC. Not CIM compliance, not Samolet acceptance, not product accuracy. Does not overwrite the fixture MOEXP coverage snapshot.
---

# MOEXP IDS on a GNI student IFC

- sample: `.local/gni-bim/2025_BIMfundamentals/2025_BIMfundamentals/model_190.ifc`
- executable: **389** pass **0** fail **389**
- this is a student model, **not** CIM compliance, **not** Samolet
- content_sha256: `3cbd61098a2c956475a9a60e579701403ff5801411cd119c9592a1d2e954588e`

Does not overwrite [`norm-pack-moexp-coverage-2026-08.md`](norm-pack-moexp-coverage-2026-08.md).

```bash
cd backend
python -m aerobim.tools.run_moexp_on_gni_sample
```
