<!-- claims-lint: allow-file reason="BCF T1 evidence boundary; CDE phrases as non-claims" -->
---
title: "BCF T1 structural handoff (KT#2 fixture)"
date: "2026-08-12"
claim_boundary: "Structural ZIP OK only. CDE import NOT_VERIFIED. Not production BCF handoff."
---

# BCF T1 under KT#2 handoff

- Artifact: `bcf-structural-handoff.json` from `aerobim.tools.verify_bcf_structural_handoff`
- `structural_ok=true` for BCF 2.1 + 3.0 XSD/structure + consumer agreement
- `cde_import.status=NOT_VERIFIED` — no Samolet CDE log/screenshot

Regenerate:

```powershell
cd backend
python -m aerobim.tools.verify_bcf_structural_handoff --output ../docs/evidence/kt2-handoff-2026-08-11/bcf-t1/bcf-structural-handoff.json
```
