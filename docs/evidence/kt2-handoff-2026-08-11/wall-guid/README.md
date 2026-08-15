# AeroBIM evidence bundle

Pack: `samples\benchmarks\project-package-wall-guid-demo.json`  
Report: `47848247aed244fa878acff822df86e9`  
`summary.passed` (Shared-gate): `False`  
Derived outcome (docs mapping): `BLOCKED`  
Code: `aerobim-backend@0.1.0+701a267`

## Artifacts

- `manifest.json` — pack identity, hashes, Shared-gate + derived outcome
- `package_source_hash_chain.json` — read-only SHA-256 chain of pack sources (RT-021; not УКЭП)
- `report.json` / `findings.json` / `capability_coverage.json`
- `report.html` — offline review surface
- `timings.json` / `logs_snippet.txt`
- `README.md` — this file

## Reproduce

```bash
cd backend
python -m aerobim.tools.export_evidence_bundle \
  --pack samples\benchmarks\project-package-wall-guid-demo.json \
  --output docs/evidence/kt2-handoff-2026-08-11/wall-guid
```

## Claim boundary

- Fixture / synthetic packs ≠ customer accuracy or Samolet SLA.
- BCF structural export is separate; CDE import is NOT_VERIFIED until Tier-2 evidence.
- Forbidden: customer accuracy >90%, customer SLA <=30 min, CDE BCF import proven, MEP system clash delivered, native DWG ready, independent calculation correctness.
