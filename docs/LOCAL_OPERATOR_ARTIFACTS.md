---
title: "Local Operator Artifacts (not in git)"
status: active
version: "1.2.0"
last_updated: "2026-07-19"
tags: [aerobim, operator, NDA, hygiene]
---

# Local operator artifacts

Files that **must not** appear on public GitHub. Create on your machine only.

## Recommended layout

```text
AeroBIM/
├── .local/
│   ├── prompts/                      # AI session prompts
│   └── engineering-docs/
│       └── audit-reports/            # RED_TEAM_*, RT_HYPERDEEP_*, PHASE0_*, …
├── docs/prompts/                     # gitignored alternate for session prompts
├── docs/evidence/internal/           # NDA customer SLA, CDE screenshots
├── samples/customer/                 # customer packs (README only in git)
└── backend/var/                      # runtime reports
```

## Public equivalents (safe to cite)

| Need | Public path |
|------|-------------|
| Docs map / Tier-0 | `docs/README.md` · `docs/TIER0_INDEX.md` |
| Jury memo (RU) | `docs/docs.md` |
| Samolet strategy | `docs/samolet.md` |
| TZ Task 07 | `docs/tz/` |
| Claims / blockers | `audit/reports/` (see `audit/reports/README.md`) |
| Claim boundary | `docs/pilot-claim-boundary-2026.md` |
| Architecture SSOT | `docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md` |
| Fixture SLA | `docs/evidence/samolet-sla-pilot-moscow-2026-05-21.json` |
| Reproducibility | `docs/REPRODUCIBILITY-2026.md` |

See [`REPOSITORY-HYGIENE-2026.md`](REPOSITORY-HYGIENE-2026.md).
