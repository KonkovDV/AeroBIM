---
title: "Red Team Wave 4 Closure"
date: 2026-08-08
status: superseded
superseded_by: docs/audit/RED_TEAM_WAVE5_CLOSURE_2026_08_08.md
---

# Red Team Wave 4 — Closure

> **Superseded:** RT-GOV-003 and RT-GOV-004 were closed in Wave 5 (`RED_TEAM_WAVE5_CLOSURE_2026_08_08.md`).

| ID | Status | Fix |
|---|---|---|
| RT-DOS-002-R | **CLOSED** | Redis-backed shared rate limiter (`AEROBIM_REDIS_URL`) with in-process fallback |
| RT-RBAC-001 | **CLOSED** | OIDC `roles` / `realm_access.roles` claim → `AuthPrincipal.roles` |
| RT-RBAC-002 | **CLOSED** | Expert HITL requires `reviewer`/`admin` roles in pilot/prod |
| RT-RBAC-003 | **CLOSED** | Norm-pack mutations gated on editor/reviewer roles |
| RT-GOV-001 | **CLOSED** | `npm audit --audit-level=high` in CI frontend job |
| RT-GOV-002 | **CLOSED** | Mypy `--strict` on security/RBAC modules (extended to full `src/` in Wave 5) |
| RT-GOV-003 | **CLOSED** (Wave 5) | Enforced commit-signature policy in CI |
| RT-GOV-004 | **CLOSED** (Wave 5) | Ruff S-band with per-file inventory |

Verification: `pytest tests/test_rt_wave4_remediation_2026_08.py -q`
