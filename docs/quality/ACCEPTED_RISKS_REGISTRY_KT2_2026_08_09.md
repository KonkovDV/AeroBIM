# Accepted risks registry (pilot / KT#2 window)

**Purpose:** public maturity signal — deferred defects are named, justified, and scheduled.
**Rule (N-40):** no exploit recipes, no function-level attack maps. Detail stays in private team notes.

| ID | Theme | Class | Why deferred past 19.08 | Plan |
| --- | --- | --- | --- | --- |
| B-1 | Upload quota vs write order | Residual | Single-user closed pilot; disk watched | Reserve-before-write sprint after KT#2 |
| B-2 | Multipart temp spill | Residual | Same | Reverse-proxy body limits in deploy config |
| B-5 | Bidirectional override in names | Residual | Low pilot probability | Expand control-char strip |
| B-6 | Stale quota lock file | Residual | Availability, not integrity claim | Timestamp + reclaim |
| B-7 | Counter fsync before replace | Residual | Crash accounting loss | `fsync` before rename |
| B-8 | JWKS refresh / cache races | Residual | Appears on IdP key rotation | Post-KT#2 sprint |
| B-9 | Token type / azp / clock skew / revoke | Residual | RFC 9068 hygiene | Post-KT#2 sprint |
| B-11 | Archive bomb edge cases | Residual | Needs malicious uploader in contour | Streamed unpack limits |
| B-12 | XML element count after parse | Residual | 16 MiB cap already set | Incremental parse later |
| B-13 | PDF signature whitespace | Residual | Needs malicious uploader | Strict magic bytes |

## Closed in this window (not deferred)

| ID | Theme | Evidence |
| --- | --- | --- |
| N-32 / A-1 | Expert HITL vs shared bearer | `principal_may_append_hitl_event` + claim boundary |
| N-33 / A-2 | Review-event sequence race | Concurrent append test — property holds |
| N-34 / A-3 | Co-author metadata rewrite | Hook passthrough + honesty docs |
| N-35 / A-4 | Decorative commit-signing enforce | `enforce_ci: false` honesty fork |
| N-36 | Cyrillic attachment names | `attachment_content_disposition` + tests |
| N-37 / B-3 | Client-facing exception path text | Public error helpers on upload/export/path jail |
| B-10 | Browser hardening headers | HSTS / Permissions-Policy / COOP / CORP / no-store |

## Governance rule

Every control that claims to enforce something must have a test that fails when the control is disabled.
