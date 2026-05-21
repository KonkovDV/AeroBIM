---
title: "Git Hygiene — Single Author Commits"
status: active
version: "1.2.0"
last_updated: "2026-05-21"
---

# Git hygiene (2026)

Russian version: [`contributor-git-ru.md`](contributor-git-ru.md).

## Problem

Some commit tools append `Co-authored-by:` trailers. GitHub then shows a second author in history and Contributors.

## Recommended workflow

Commit from your shell or the VS Code task **AeroBIM: commit (single author)** — not through automated commit attribution that adds co-author trailers.

```powershell
cd AeroBIM
powershell -ExecutionPolicy Bypass -File scripts/git_commit.ps1 -Message "docs: your message"
```

The script:

- sets author `KonkovDV`;
- rejects messages containing `Co-authored-by:` before commit;
- verifies the recorded commit body after write.

## History check

```powershell
git log -20 --format="%B---" | Select-String "Co-authored-by"
```

Empty output means no co-author trailers in the last 20 commits.

## Cleaning polluted history

If older commits already contain `Co-authored-by:`:

```powershell
$env:FILTER_BRANCH_SQUELCH_WARNING = "1"
git filter-branch -f --msg-filter "python scripts/strip_coauthor_msgfilter.py" -- main
git push --force-with-lease origin main
```

Coordinate force-push with the branch owner first.

### Legacy author `KonkovaElena` / `test@example.com`

On `main` (2026-05-20) early commits were rewritten to `KonkovDV <KonkovDV@users.noreply.github.com>`.

```bash
bash scripts/rewrite-author-konkovdv.sh
git update-ref -d refs/original/refs/heads/main
git push --force-with-lease origin main
```

## CI and publication

**Tasks: AeroBIM: quality gate** → commit via `scripts/git_commit.ps1` → `git push`.
