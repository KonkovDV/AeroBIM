---
title: "Red Team — eng residuals wave (2026-08-03)"
status: active
version: "1.0.0"
last_updated: "2026-08-03"
claim_boundary: "Self red-team. Checkpoint NO_GO. Not external audit."
---

# Red Team — Eng residuals wave (2026-08-03)

**Author relationship:** Internal self-assessment  
**Scope:** VLM smoke gate · signature deepen · OIDC Phase 2 · BCF T2 checklist · DWG honesty · BSI IDS import · bare-metal DEFERRED  
**Checkpoint:** **NO_GO**

## Findings

| ID | Surface | Verdict |
|---|---|---|
| RT-RES-VLM-01 | kimi smoke bypassed HybridRouteGate | MITIGATED — `vlm_smoke_gate` before client; blocked → exit 3 / zero bytes |
| RT-RES-SIG-01 | Envelope ok sold as УКЭП | MITIGATED — alg/value presence-only + trust_chain not_verified; crypto missing |
| RT-RES-SIG-02 | Envelope `package_hashes` path traversal / out-of-jail read | MITIGATED — hashes jailed under content dir; abs/`..` ignored |
| RT-RES-OIDC-01 | Phase 2 stubs sold as SSO ready | MITIGATED — `auth_bff.status=NOT_IMPLEMENTED`; no session cookie |
| RT-RES-OIDC-02 | Public `/v1/auth/logout` wiped global CSRF store (DoS) | MITIGATED — logout honesty only; no `clear()` |
| RT-RES-BCF-01 | Checklist sold as T2 VERIFIED | MITIGATED — `--checklist` never sets claim_allowed; STATUS stays NOT_VERIFIED |
| RT-RES-DWG-01 | supported=True native DWG | MITIGATED — fail-closed even if stub returns supported |
| RT-RES-IDS-01 | n=290 sold as product accuracy / >90% | MITIGATED — CC BY-ND NOTICE + claim_boundary regression only |
| RT-RES-OFF-01 | wheelhouse sold as offline-ready | MITIGATED — exit 2 + DEFERRED artifact |

## Still open (external)

RT-001 / RT-002 / RT-003 · BCF T2 live CDE · OIDC Phase 3 IdP · УКЭП crypto · bare-metal owner reopen

## Verdict

Residuals eng-acceptable under Claims Lock. Checkpoint **NO_GO**.
