# Quality journal — Class A honesty fixes (2026-08-09)

| Time | Action |
| --- | --- |
| 2026-08-09 | Removed co-author trailer stripping from `.githooks/commit-msg` and related scripts/docs (N-34). Provenance metadata must remain honest. |
| 2026-08-09 | Static API bearer denied for expert HITL events in all profiles (N-32). Claim boundary updated: bearer = pilot transport/read, not expert verdict. |
| 2026-08-09 | Concurrent review-event append regression test added; filesystem lock path proven (N-33 SELF_REFUTED as product break). |
| 2026-08-09 | Browser hardening headers + public error sanitization for path jail / BCF export (B-3/B-10). |
| 2026-08-09 | Accepted-risks registry published (aggregated Class B deferrals). SSRF translation prefixes blocked. |
| 2026-08-09 | N-46: operator `.local` moved to sibling `../AeroBIM-private/`; pre-commit blocks recheck/internal markers. |
| 2026-08-09 | A-2: reclaim review-event locks older than 60s; stale-lock test. |
| 2026-08-09 | A-3: AI-assistance honesty in SECURITY.md; strip filter renamed to passthrough tombstone. |
| 2026-08-09 | A-4/N-45: signing ratchet date today + target 0.03; `enforce_ci` stays false until G-status + pubkey. |
