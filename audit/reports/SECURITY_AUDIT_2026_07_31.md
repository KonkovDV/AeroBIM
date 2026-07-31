# Security audit — re-run 2026-07-31 (evening)

**Evidence class:** `REPRODUCED` for listed pytest suites on local workspace.  
**HEAD (git):** `64c69b4f9cdd99779e9aac91ec87078367190339`  
**Tree:** `c8b51c78cac3a68af0ccc1308b78c6f8b3326ef6`  
**Machine artifact:** `docs/evidence/security-rerun-2026-07-31.json`  
**Raw log:** `artifacts/security-rerun-2026-07-31/pytest-security.out.txt` (gitignored under `artifacts/*`)

## Command (REPRODUCED)

```bash
cd backend
pytest \
  tests/test_api_security.py \
  tests/test_api_object_acl.py \
  tests/test_security_bomb_guards.py \
  tests/test_security_hardening_2026_07_27.py \
  tests/test_rt_phase4_security.py \
  tests/test_outbound_guard_invariant.py \
  tests/test_mutation_kills_path_jail.py \
  tests/test_mutation_kills_object_acl.py \
  tests/test_upload_content_security.py \
  tests/test_advisory_cache_tenant_isolation.py \
  tests/test_rt_phase8_tenancy.py \
  tests/test_rt_norm_pack_tenancy.py \
  tests/test_hybrid_privacy_guard.py \
  tests/test_llm_prompt_injection.py \
  tests/test_llm_advisory_invariance.py \
  tests/test_llm_evidence_bounded.py \
  tests/test_p0_remediation_fail_closed.py \
  tests/test_rt_remediation_post.py \
  -q --tb=line
```

**Result:** `190 passed, 1 skipped, 0 failed` in ~6.0s (exit 0).

## Control matrix (this re-run)

| Control | Severity if broken | This re-run | Evidence suite |
|---|---|---|---|
| Path traversal / storage jail | critical | **REPRODUCED** | `test_mutation_kills_path_jail`, API security |
| Cross-tenant report/job/export ACL | critical | **REPRODUCED** | `test_api_object_acl`, phase8 tenancy, mutation ACL |
| SSRF outbound guard | high | **REPRODUCED** | `test_outbound_guard_invariant` |
| Unauthenticated fail-closed | high | **REPRODUCED** | `test_api_security` |
| ZIP bomb / member `..` / ratio caps | high | **REPRODUCED** | `test_security_bomb_guards`, upload content |
| XXE / billion laughs / XML caps | high | **REPRODUCED** | `test_security_bomb_guards` |
| Upload sniff + size limits | high | **REPRODUCED** | `test_upload_content_security` |
| Prompt injection → verdict | high | **REPRODUCED** | LLM advisory + invariance tests |
| Hybrid privacy / masking | medium | **REPRODUCED** | `test_hybrid_privacy_guard` |
| Fail-closed sign-off / soft flags | high | **REPRODUCED** | P0 + RT remediation post |
| PyMuPDF process isolation / sandbox | medium | **NOT_IN_SCOPE** | residual in SECURITY.md — no subprocess sandbox suite here |

## What this does **not** prove

- External penetration test or red-team live assault on a deployed host  
- Production multi-tenant certification  
- Customer data residency / DPA compliance  
- That uncommitted local changes are identical to a clean tagged release  
- Residual host risk of in-process PyMuPDF on untrusted PDF (accepted / documented)

## Forbidden claim

«Security audit passed for production multi-tenant» — **still forbidden**.  
Allowed: «Security regression battery 190 passed / 1 skipped on stated suites and commit/workspace (engineering)».

## Next

1. ~~CI job `security-regression`~~ — added in `.github/workflows/ci.yml` (engineering only)
2. PyMuPDF subprocess isolation remains MEDIUM residual (LIC-001 adjacent)
3. Customer sign-off still **NO_GO** (RT-001/002/003)
