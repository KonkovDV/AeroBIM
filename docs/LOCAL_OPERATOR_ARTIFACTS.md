---
title: "Local Operator Artifacts (not in git)"
status: active
version: "1.0.0"
last_updated: "2026-05-21"
tags: [aerobim, operator, NDA]
---

# Local operator artifacts

Files that **must not** appear in the public repository. Create on your machine only.

## Recommended layout

```text
AeroBIM/
├── docs/evidence/internal/          # gitignored
│   ├── cde-import-proof/            # screenshots after BCF import
│   ├── samolet-sla-customer-*.json  # SLA on NDA package
│   └── traceability-audit.json
├── samples/benchmarks/
│   └── project-package-samolet-pilot-v1.json   # gitignored manifest
└── backend/var/                     # gitignored runtime reports
```

## Public equivalents (safe to cite)

| Need | Public path |
|------|-------------|
| Fixture SLA | `docs/evidence/samolet-sla-pilot-moscow-2026-05-21.json` |
| Mapping report | `docs/evidence/samolet-typical-errors-mapping.json` |
| Reproducibility | `docs/REPRODUCIBILITY-2026.md` |

See [`REPOSITORY-HYGIENE-2026.md`](REPOSITORY-HYGIENE-2026.md).
