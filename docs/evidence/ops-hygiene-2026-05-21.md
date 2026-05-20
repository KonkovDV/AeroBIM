---
title: "Ops Hygiene Notes 2026-05-21"
status: active
---

# Ops Hygiene (2026-05-21)

## Dependabot

Triage open PRs at https://github.com/KonkovDV/AeroBIM/pulls — prefer security patches and patch/minor dev-deps during pilot; defer major bumps until post-pilot unless CVE critical.

Record merges in weekly log when applied.

## GitHub About / Topics

Apply manually when `gh` is available:

```bash
gh repo edit KonkovDV/AeroBIM --description "Deterministic cross-modal BIM validation (IFC, IDS, BCF)" --add-topic bim --add-topic ifc --add-topic openbim
```

Canonical text: [`.github/repository-metadata.md`](../../.github/repository-metadata.md).

## Optional adapters

Pilot default: `pip install -e ".[dev,vision]"` only. Document `.[clash]` / `.[docling]` smoke outcomes in [`pilot-weekly-log-2026.md`](../pilot-weekly-log-2026.md) per [`optional-adapters-smoke-2026.md`](../optional-adapters-smoke-2026.md).
