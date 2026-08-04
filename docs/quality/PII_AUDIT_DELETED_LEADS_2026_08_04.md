# PII audit — deleted `docs/customer-discovery` history (2026-08-04)

**Scope:** blobs that ever lived on public refs under `docs/customer-discovery/` or `.local/`.  
**Question:** нужна ли перепись истории (`git-filter-repo` + force-push) по 152-ФЗ?

## All-refs check (включая удалённые ветки)

Команда:

```bash
git log --all --diff-filter=A --name-only --pretty=format: -- \
  'docs/customer-discovery/*.csv' '.local/*'
```

**Результат на 2026-08-04 (`main` + `origin/main`; других локальных/удалённых веток нет):**

| Path ever added | On which refs |
|---|---|
| `docs/customer-discovery/sprint-2-1-leads.csv` | `main` (introduced `2c52f75`, deleted `774c18b`) |
| `.local/*` | **никогда** (нет add в истории) |
| `sprint2-leads-30plus.csv` / `commercial-pipeline.csv` | **никогда** на GH |

## Verdict

| Path (ever on GH) | Content class | Personal data? | Action |
|---|---|---|---|
| `sprint-2-1-leads.csv` | 5 synthetic / placeholder rows (`example.invalid`, `SYNTHETIC_LEAD_PLACEHOLDER`) | **No** | History rewrite **not required** |
| `sprint-2-1-leads.md` | Funnel zeros + policy | **No** | — |
| `sprint-2-1-customer-outreach-report.md` | contacted=0 template | **No** | Removed from HEAD in `774c18b`; live учёт только в `.local/commercial-ops/` |
| `sprint2-outreach-tracking.md` | Empty event table | **No** | Same |
| Live pipeline / letters / call-list | Org + corp email + some LPR | **Never committed** | Keep gitignored |

## Evidence

- Delete commit: `774c18b`  
- Introduced: `2c52f75`  
- Sample row marker: `SYNTHETIC_LEAD_PLACEHOLDER`  
- Branches scanned: `main`, `remotes/origin/main` only

## Residual

Local SSOT under `.local/commercial-ops/` — operator-only. Do not `git add -f`. Re-run the all-refs command after any fetch of unknown remotes.
