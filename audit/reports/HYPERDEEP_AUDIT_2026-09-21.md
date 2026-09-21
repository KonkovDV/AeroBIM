# AeroBIM hyperdeep audit — 2026-09-21

## Executive result

The repository has a mature fail-closed engineering posture and an unusually explicit claim boundary, but it is **not production-ready as an unaudited multi-tenant service**. This audit therefore separates confirmed engineering findings from evidence gaps and customer blockers. It does not promote fixture evidence to customer accuracy, CDE interoperability, SSO, or MEP-delivery claims.

## Confirmed finding fixed in this PR

### SEC-OBJ-001 — divergent object-key validation (High, fixed)

**Evidence:** `LocalObjectStore` rejected some path escapes through the filesystem jail, while `S3ObjectStore._qualify_key()` only normalized slashes and prefixed the key. The S3 path therefore accepted traversal-like, absolute, Windows ADS, reserved-device, and ambiguous Unicode components that the local backend rejected. Although S3 does not interpret `..` as a filesystem traversal, the divergent contract creates a tenant-prefix and portability risk: the same logical request can address different objects depending on the configured store.

**Fix:** both adapters now use `normalize_object_key()`, a shared canonical boundary that rejects absolute/traversal/empty components, control characters, colons/ADS syntax, reserved Windows device names, trailing dot/space components, and overlong components. Prefixing remains idempotent.

**Regression coverage:** `backend/tests/test_object_store_key_boundaries.py`.

## Areas reviewed

- **Backend/API:** FastAPI route split, bearer/OIDC principal binding, object ACL checks, path jail, multipart streaming, content sniffing, ZIP/XML limits, SSRF gates, rate limiting, report/review contracts, BCF export, and error mapping.
- **Review/HITL:** server-side state projection, optimistic version checks, idempotency keys, exclusive sequence slots, hash-chain evidence, actor/role gates, and the open PR #81 atomic final-remark change.
- **Frontend:** Vite/React review shell, `summary.passed` source guard, MIME allowlist, text rendering/XSS posture, Vitest/build gates, and the documented partial-scope boundary.
- **CI/supply chain:** SHA-pinned actions, hashed runtime/dev locks, lock-drift checks, CodeQL, pip-audit, SBOM/release attestation steps, coverage/JUnit artifacts, OpenAPI export, Docker/offline smoke, and Dependabot.
- **Documentation/governance:** README parity, claim-lock linting, ADR-001 verdict ownership, threat model, license inventory, pilot boundary, evidence freshness, and the blocker register.

## Residual risks and evidence gaps

1. **Production identity boundary:** the production OIDC BFF/SSO path remains documented as `NOT_IMPLEMENTED`; static bearer is a transport/service principal and must not sign HITL decisions. A reverse proxy must not be treated as an identity provider.
2. **Durable execution:** production submit uses Redis-backed state but the route still schedules `BackgroundTasks` in the API process. A process crash can strand queued work; a durable worker/lease consumer and recovery runbook are still required.
3. **Storage consistency:** local/S3 object storage, report metadata, quota counters, and review events do not form one transactional unit. Compensating cleanup is present, but crash injection and reconciliation should remain release gates.
4. **Runtime admission:** Docker pins the base image digest and drops capabilities, but image provenance/signature verification and a mandatory SBOM attestation policy are not equivalent to having SBOM generation code/tests. Treat release attestation as engineering evidence, not registry enforcement.
5. **CI bootstrap:** pip/uv bootstrap is version-pinned but the bootstrap wheels are not hash-verified. This is a documented residual in CI and should be removed with a trusted toolchain/bootstrap image or verified hashes.
6. **Interoperability:** BCF is structurally tested (T1); independent CDE import (T2) remains `NOT_VERIFIED`. Native RVT/NWD/DWG and system-aware MEP clash remain explicit gaps.
7. **Evaluation:** fixture/open-benchmark values, simulated raters, and mutation-kill tests do not establish customer precision/recall, false-pass rate, SLA, or `customer_go`.
8. **Concurrency:** PR #81 addresses atomic final-remark persistence, but its branch is still open and unverified in the current main line; merge ordering and CI results must be checked before treating that behavior as shipped.

## Recommended next gates

- Run the full CI matrix on this PR and on PR #81; do not merge either with a red/absent required check.
- Add crash-injection tests around object promotion, quota release, report persistence, and review-event append.
- Move production job execution to a durable worker with explicit lease recovery and idempotent side-effect boundaries.
- Replace static-bearer reverse-proxy deployment with a verified OIDC BFF/session contract before production customer data.
- Publish independent BCF consumer evidence and a signed customer acceptance profile before changing the claim boundary.
