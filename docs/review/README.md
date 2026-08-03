# Review pack

For reviewers who cannot rely on GitHub web cache.

| File | What it is |
|------|------------|
| [`aerobim-kt2-text.stat.txt`](aerobim-kt2-text.stat.txt) | Historical `--stat` snapshot (may lag HEAD) |
| [`CHECKLIST_SELF_AUDIT.md`](CHECKLIST_SELF_AUDIT.md) | Self-run of Red Team checklist |

**Removed (RT-W-05, 2026-08-04):** `aerobim-kt2-text.patch` — stale second source of truth that drifted from README. Use `git log` / `git diff` on `main` instead.

## Reproduce locally

```bash
git fetch origin
git checkout main
git log -5 --oneline
git status
```

## Honesty

- Prefer live `main` over any checked-in patch.
- Binary IDS fixtures under `samples/ids/buildingsmart-testcases/` are CC BY-ND — see `LICENSE_CC_BY_ND_4.0.txt` / `NOTICE` there.
- Vendored BCF/IDS XSD: CC BY-ND 4.0 (RT-W-01 closed) under `samples/bcf-xsd/` and `samples/ids-xsd/`.
