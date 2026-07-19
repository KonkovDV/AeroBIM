# RED TEAM REMEDIATION — 2026-07-19

**Branch:** `redteam/remediation-2026-07-19`  
**Baseline SHA:** `34debbfcb99fecf34361dda2449850bef4863fcf`  
**Checkpoint:** **`NO_GO`** — RT-001 / RT-002 / RT-003 remain OPEN.

---

## Threat model (condensed)

| Asset | Trust boundary | Top abuse |
|---|---|---|
| Multipart uploads / ZIP / IFC / IDS / PDF | Untrusted client → storage jail | Zip bombs, MIME spoof, traversal, quota DoS |
| Reports / jobs / previews / BCF | AuthN → tenant ACL → blob | Cross-tenant IDOR, 403≠404 enumeration |
| OIDC + static bearer | IdP / config → API | Claim spoof, JWKS SSRF, alg confusion |
| bSI / OpenCDE / S3 endpoints | Config → egress | SSRF to metadata / RFC1918 via redirect |
| Sign-off capabilities | Deterministic core vs advisory | Soft `development` under `AEROBIM_ENV=production` |
| CI / Docker / deps | Supply chain | Floating Action tags, no lockfile |

STRIDE covered in findings below. Full actor list: anonymous client, malicious tenant, compromised JWT, malicious config operator, CI attacker.

---

## Findings

| ID | Sev | CWE | Symbol | Remediation | Regression |
|---|---|---|---|---|---|
| **RT-POST-01** | P0 | CWE-1188 | `settings.from_env`, Dockerfile, compose | Non-dev defaults `signoff_profile=production`; bake profile into image/compose; remove soft clash override | `Post01ProductionSignoffDefaultTests` |
| **RT-POST-02** | P1 | CWE-203 | `_assert_*_access` | Cross-tenant ACL denial → **404** (same as missing) | ACL tests updated to 404 |
| **RT-POST-03** | P1 | CWE-918 | `outbound_url.py` + bSI/BCF/OIDC | SSRF host/literal IP guard; reject redirects/userinfo | `Post03SsrfGuardTests` |
| **RT-POST-04** | P1 | CWE-863 | OIDC tenant binding | Only `AEROBIM_OIDC_TENANT_CLAIM` (default `tenant_id`) | Code + settings field |
| **RT-POST-05** | P1 | CWE-522 | `VITE_*` bearer | Documented residual: demo-only; do not ship bearer in Vite for prod (**NOT fully eliminated** — needs BFF) | Compose warning retained |
| **RT-POST-06** | P1 | CWE-754 | `unit_scale` default | Default `NOT_VERIFIED`; pilot requires OK | `Post06*` |
| **RT-POST-07** | P1 | CWE-754 | pilot SKIPPED calc/qty | Pilot/production treat SKIPPED as blocking | `Post06*` |
| **RT-POST-08** | P1 | CWE-200 | upload response | Omit `object_key` | `Post08*` |
| **RT-POST-09** | P1 | CWE-829 | CI workflows | Pin Actions to full SHAs; **lockfile still NOT_VERIFIED** | Workflows pinned |
| **RT-POST-10** | P2 | CWE-79 | `_esc` | `html.escape(..., quote=True)` | `Post10*` |
| **RT-POST-11** | P2 | CWE-22 | `zip_limits` | Reject `..` / absolute ZIP members | `Post11*` |

### Residual / NOT_VERIFIED this session

| Item | Status |
|---|---|
| `pip-audit` / bandit / Semgrep / CodeQL / gitleaks | **NOT_VERIFIED** (not executed) |
| `npm audit` / frontend full suite | **NOT_VERIFIED** / pending |
| CycloneDX SBOM / Trivy / license scan | **NOT_VERIFIED** |
| Backend reproducible lockfile (`uv.lock`) | **NOT_VERIFIED** — residual of RT-POST-09 |
| BFF / HttpOnly cookie auth | **NOT_IMPLEMENTED** (RT-POST-05 residual) |
| DNS rebinding after allow | Mitigated at resolve-time; residual race **NOT_VERIFIED** fully closed |
| RT-001 / RT-002 / RT-003 | **OPEN** (external) |

---

## Gates (this branch)

| Gate | Result |
|---|---|
| `pytest tests -q` | **650 passed**, 4 skipped |
| `ruff check` | pass (after format) |
| `mypy` (baseline) | Success 149 files |
| Security scanners | **NOT_VERIFIED** |

---

## Verdict

**NO_GO** — code-fixable P0 (sign-off soft-prod) and listed P1s remediated with tests; external blockers and several supply-chain/scanner gates remain open or NOT_VERIFIED.
