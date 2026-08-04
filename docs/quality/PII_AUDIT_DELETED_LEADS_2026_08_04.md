# PII audit — deleted `docs/customer-discovery` history (2026-08-04)

**Scope:** blobs that ever lived on public `main` under `docs/customer-discovery/` and were removed in `774c18b`.  
**Question:** нужна ли перепись истории (`git-filter-repo` + force-push) по 152-ФЗ?

## Verdict

| Path (ever on GH) | Content class | Personal data? | Action |
|---|---|---|---|
| `sprint-2-1-leads.csv` | 5 synthetic / placeholder rows (`example.invalid`, `SYNTHETIC_LEAD_PLACEHOLDER`) | **No** | History rewrite **not required** |
| `sprint-2-1-leads.md` | Funnel zeros + policy | **No** | — |
| `sprint-2-1-customer-outreach-report.md` | contacted=0 template | **No** | — |
| `sprint2-outreach-tracking.md` | Empty event table | **No** | — |
| `sprint2-leads-30plus.csv` | — | Never tracked on GH | — |
| `commercial-pipeline.csv` / letters / verification / call-list | Live funnel | **Never committed** (local `.local/commercial-ops/` only) | Keep gitignored |

## Evidence

- Delete commit: `774c18b`  
- Introduced: `2c52f75`  
- Sample row marker: `SYNTHETIC_LEAD_PLACEHOLDER — replace with verified public orgs before outreach`  
- Explicit note in CSV: `Do not invent personal emails`

## Residual

Local SSOT under `.local/commercial-ops/` contains org names, INN, corporate emails, and some LPR names / phones in notes — **operator-only**. Do not `git add -f`. No force-push warranted for the deleted public files.
