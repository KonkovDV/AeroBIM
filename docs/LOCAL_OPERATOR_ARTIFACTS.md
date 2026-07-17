---
title: "Local Operator Artifacts (not in git)"
status: active
version: "1.1.0"
last_updated: "2026-07-17"
tags: [aerobim, operator, NDA, hygiene]
---

# Local operator artifacts

Files that **must not** appear on public GitHub. Create on your machine only.

## Recommended layout

```text
AeroBIM/
├── .local/
│   ├── prompts/                 # AI session prompts
│   └── engineering-docs/        # Red Team deltas, EXECUTION_PLAN waves, deep audits
├── docs/evidence/internal/      # NDA customer SLA, CDE screenshots
├── samples/customer/            # customer packs (README only in git)
└── backend/var/                 # runtime reports
```

## Public equivalents (safe to cite)

| Need | Public path |
|------|-------------|
| TZ Task 07 | `docs/tz/` |
| Claims / blockers | `audit/reports/CLAIMS_LOCK_*.md`, `CRITICAL_BLOCKERS.md` |
| Claim boundary | `docs/pilot-claim-boundary-2026.md` |
| Architecture SSOT | `docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md` |
| Fixture SLA | `docs/evidence/samolet-sla-pilot-moscow-2026-05-21.json` |
| Reproducibility | `docs/REPRODUCIBILITY-2026.md` |

See [`REPOSITORY-HYGIENE-2026.md`](REPOSITORY-HYGIENE-2026.md).
