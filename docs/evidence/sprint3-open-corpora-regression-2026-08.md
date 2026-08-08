# Sprint 3 — open corpora regression re-run

Generated: `2026-08-08T14:41:38+00:00`

**claim_boundary:** fixture regression / timing only — not product accuracy.

## Regression profile (n=7)

| Metric | Value |
|---|---:|
| cases_run | 7 |
| cases_matched | 7 |
| binary_match_rate | **1.0** |

All pinned IDS↔IFC fixture pairs matched expected pass/fail.

## Artifacts (local, gitignored)

- `artifacts/open-corpora/open-corpora-full.json` — full profile run (regression + pilot-approx + load)
- `artifacts/open-corpora/open-corpora-smoke.json` — SHA pin smoke

## Reproduce

```bash
cd backend
python -m aerobim.tools.run_open_corpora_profiles --mode smoke
python -m aerobim.tools.run_open_corpora_profiles --mode full
```
