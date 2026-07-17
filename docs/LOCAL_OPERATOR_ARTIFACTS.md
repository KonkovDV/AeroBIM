# Local operator artifacts (not published)

These paths are **gitignored**. Do not commit them to GitHub.

| Path | Purpose |
|------|---------|
| `.local/prompts/` | AI assistant session prompts for operators (e.g. next-work after Red Team) |
| `docs/prompts/` | Legacy location — also ignored; prefer `.local/prompts/` |
| `docs/evidence/internal/` | NDA / customer-only evidence |
| `docs/samolet-techlab-scorecard-2026.zip` | Local scorecard archive |
| `samples/customer/**` | Customer packs (except `README.md`) |
| `backend/var/`, `artifacts/` | Runtime / CI dumps |

## Public SSOT instead of prompts

Operators and jurors should use published surfaces only:

- `docs/TIER0_INDEX.md`
- `docs/pilot-claim-boundary-2026.md`
- `audit/reports/CLAIMS_LOCK_2026_07_17.md`
- `audit/reports/CRITICAL_BLOCKERS.md`
- Dated `audit/reports/AUDIT_*.md` (evidence of remediations, not chat prompts)

Policy: [`REPOSITORY-HYGIENE-2026.md`](REPOSITORY-HYGIENE-2026.md).
