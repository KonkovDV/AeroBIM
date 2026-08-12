<!-- claims-lint: allow-file reason="N43 rehearsal checklist; governance only" -->
---
title: "N43 baseline lag=1 — rehearsal checklist (activate 17.08.2026)"
date: "2026-08-12"
claim_boundary: "Do not flip N43 before 2026-08-17. Preparation only."
---

# N43 rehearsal checklist

**Do not run activation before 2026-08-17** (`governance/deferred_controls_registry.json`).

## On 17.08

1. Clean tree (or only allowed lag paths).  
2. Export runtime baseline on tip; update `docs/evidence/runtime-baseline-latest.json`.  
3. Set policy `max_commits_behind=1` and registry waiver `N43-baseline-one-commit-lag` → `state=active`.  
4. Run:

```powershell
python backend/scripts/verify_deferred_controls.py --registry governance/deferred_controls_registry.json
python scripts/lint_claims.py --matrix-guard
```

5. Signed commit + push.  
6. Confirm CI baseline-integrity job green.

## Until 17.08

Keep `state=deferred` and `max_commits_behind=50`. Prep only.
