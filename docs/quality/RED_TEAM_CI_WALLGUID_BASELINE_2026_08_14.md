<!-- claims-lint: allow-file reason="Red Team of CI wall-guid/baseline pack; forbidden phrases as non-claims; NO_GO" -->
---
title: "Red Team — CI wall-guid CRLF + runtime baseline (2026-08-14)"
status: active
version: "1.0.0"
last_updated: "2026-08-14"
claim_boundary: >
  Internal Red Team of the CI-green continuation. Checkpoint remains NO_GO.
  Does not close RT-001/002/003. Not product accuracy. Not 10D/Tangl integration.
  Not N43 lag=1 activation.
---

# Red Team — CI wall-guid + baseline refresh

**Author relationship:** Internal self-assessment  
**Scope:** CI `main` on `88e726b` (jobs `test`, `lint`) + contour diagram vs Samolet vector  
**Checkpoint:** **`NO_GO`**

## Verdict

| Lane | Result |
|---|---|
| Application security (Critical/High) | **0** — no auth/ACL change |
| Integrity (Medium) | **0 open** — CRLF digest mismatch closed; env-doc hole closed |
| Claims Lock | **PASS intended** |
| Customer Checkpoint | Still **NO_GO** |
| N43 lag=1 | **Not activated** (still max_commits_behind=50) |

## Findings

| ID | Sev | Status | Finding | Mitigation |
|---|---|---|---|---|
| RT-CI-01 | HIGH | **FIXED** | `wall-guid` snapshot hashed with CRLF; Linux `eol=lf` checkout failed `verify_evidence_bundle` (`exit=1`) | LF-normalize snapshot + rehash; exporter writes `newline="\n"`; regression test |
| RT-CI-02 | MED | **FIXED** | `--check-readme`: undocumented `AEROBIM_VLM_ENABLED` / `AEROBIM_OIDC_BFF_*`; LOC drift vs `3489cad` | README table+marker; baseline metrics refreshed |
| RT-CI-03 | INFO | **CLOSED** | Python 3.12 was missing locally; hashes were 3.13.7 only | A6: CPython 3.12.10 venv; overlay/LIMITATIONS match 3.13 pin; repro hash differs via `code_version` |
| RT-CI-04 | INFO | **MITIGATED** | Contour diagram showed only 10D, hiding Tangl/Renga | Diagram 01 now Renga → IFC → Tangl + AeroBIM |

## Attack scripts that failed (good)

1. **«CI green = Checkpoint GO»** — NO_GO stays.  
2. **«Re-export wall-guid live HTML»** — snapshot bytes kept except EOL.  
3. **«Activate N43 lag=1»** — policy unchanged.  
4. **«auth_bff production-ready because env vars exist»** — README: lab-only, not implemented.

## Not claimed closed

RT-001, RT-002, RT-003, native DWG, Tangl/10D integration, Harbor 160, video, ЛК. Python 3.12 overlay pin measured (repro hash still binds git SHA).
