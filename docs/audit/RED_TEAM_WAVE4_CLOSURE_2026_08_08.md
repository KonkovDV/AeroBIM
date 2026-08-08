---
title: "Red Team Wave 4 Closure"
date: 2026-08-08
status: remediated
---

# Red Team Wave 4 — Closure

| ID | Status | Fix |
|---|---|---|
| RT-DOS-002-R | **CLOSED** | Redis-backed shared rate limiter (`AEROBIM_REDIS_URL`) with in-process fallback |
| RT-RBAC-001 | **CLOSED** | OIDC `roles` / `realm_access.roles` claim → `AuthPrincipal.roles` |
| RT-RBAC-002 | **CLOSED** | Expert HITL requires `reviewer`/`admin` roles in pilot/prod |
| RT-RBAC-003 | **CLOSED** | Norm-pack mutations gated on editor/reviewer roles |
| RT-GOV-001 | **CLOSED** | `npm audit --audit-level=high` in CI frontend job |
| RT-GOV-002 | **CLOSED** | Mypy `--strict` on security/RBAC modules |
| RT-GOV-003 | **ADVISORY** | `scripts/verify_commit_signatures.py` in supply-chain CI |
| RT-GOV-004 | **DEFERRED** | Ruff S-band blocked by enum false positives; revisit with per-file noqa inventory |

Verification: `pytest tests/test_rt_wave4_remediation_2026_08.py -q`
