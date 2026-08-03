# Review pack — 2026-08-03 (grant + checklist remediation)

For reviewers who cannot rely on GitHub web cache.

## Download these files from the repo

| File | What it is |
|------|------------|
| [`aerobim-kt2-text.patch`](aerobim-kt2-text.patch) | Unified diff: eng residuals + Qwen W1 + Yandex grant + checklist remediation (text only; no bSI IDS binaries) |
| [`aerobim-kt2-text.stat.txt`](aerobim-kt2-text.stat.txt) | `--stat` for the same range |
| [`CHECKLIST_SELF_AUDIT.md`](CHECKLIST_SELF_AUDIT.md) | Self-run of your Red Team checklist |

## Reproduce locally

```bash
git fetch origin
git checkout main
git log -5 --oneline
# expected tip includes: feat(grant-checklist): …  and earlier feat(grant)/feat(qwen-local)/feat(residuals)

git apply --check docs/review/aerobim-kt2-text.patch   # dry-run after reset to parent if needed
```

Base for the patch: parent of `feat(residuals): close eng residuals wave` (`e96866d^` / `b08b43d`).

## Honesty

- `e9c0afb3` is **not** in this clone’s object DB (likely a release tag/hash from another mirror). Use `git log -1 --format=%H` on `main` after fetch.
- Binary IDS fixtures under `samples/ids/buildingsmart-testcases/` are **omitted** from the text patch (too large); they landed in `e96866d` — inspect via `git show e96866d --stat`.
