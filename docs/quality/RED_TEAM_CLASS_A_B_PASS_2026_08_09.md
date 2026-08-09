# Red Team pass — Class A closure + B window (2026-08-09)

**Tree:** `11dc84c` + follow-up commits on this pass.  
**Mode:** claim-breaking first; no public exploit catalogue (N-40).

## Ground truth

| Check | Result |
| --- | --- |
| Remote heads | `main` only |
| Class A on main | N-32/34/35 closed; N-33 self-refuted with regression |
| CI (prior Class A) | success on `11dc84c` |

## Self-attacks (this pass)

| # | Attack | Verdict | Evidence |
| --- | --- | --- | --- |
| A21 | Shared bearer accepts HITL when role gate off | **KILLED** | `HitlRbacTests.test_static_bearer_blocked_even_when_role_gate_disabled` |
| A22 | Parallel accept same `previous_state` | **KILLED** | `ConcurrentReviewEventAppendTests` — exactly one wins |
| A23 | Commit-msg strips Co-authored-by | **KILLED** | `CommitMsgHookHonestyTests` |
| A24 | `enforce_ci=true` with min ratio 0 | **KILLED** | `CommitSigningPolicyHonestyTests` |
| A25 | Health without HSTS / Permissions-Policy | **KILLED** | `SecurityHeadersTests` (extended) |
| A26 | 6to4 / NAT64 literal as outbound IP | **KILLED** | `OutboundTranslationPrefixTests` |
| A27 | PathJailError path echoed to client | **KILLED** | public storage-boundary detail helpers |

**KILLED this pass:** 7 · **SURVIVED:** 0 · **Δ TZ #7:** 0%

## Customer-safe line

Independent audit closed claim-breaking findings in-window with failing-before-fix tests; remaining residuals are in the accepted-risks registry with deferral justification.
