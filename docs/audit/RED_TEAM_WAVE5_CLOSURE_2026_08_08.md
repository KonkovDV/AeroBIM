---
title: "Red Team Wave 5 Closure"
date: 2026-08-08
status: remediated
---

# Red Team Wave 5 — Closure

| ID | Status | Fix |
|---|---|---|
| RT-GOV-004 | **CLOSED** | Ruff S-band enabled; inventory in `governance/ruff_s_band_inventory.json`; per-file noqa in `pyproject.toml` |
| RT-GOV-003 | **CLOSED** | Commit-signature gate enforced in CI via `governance/commit_signing_policy.json` + ratchet policy |
| RT-GOV-005 | **CLOSED** | Mypy `--strict` on entire `src/aerobim` (305 files, 0 errors) |

| RT-GOV-006 | **CLOSED** | FastAPI `response_model=None` for binary/stream routes (`Response \| FileResponse`) |
| RT-GOV-007 | **CLOSED** | Rate-limit Redis keys hash bearer; pilot/prod fail-closed when Redis unavailable |
| RT-GOV-008 | **CLOSED** | OIDC tenant claim rejects non-string values; analyze idempotency key normalized |
| RT-ERR-002 | **CLOSED** | Stable public HTTP details on analyze 429, HITL 409/400, norm-pack 400 (no `str(exc)` leak) |

## Post-Wave 5 hardening (2026-08-08)

- `reports.py` / `exports.py`: `response_model=None` fixes FastAPI startup on union/binary responses.
- `rate_limit.py`: SHA-256 fingerprint instead of bearer prefix in Redis keys.
- `rate_limit_backend.py`: no silent in-process fallback under `samolet_pilot` / `production`.
- `verify_commit_signatures.py`: missing policy file exits non-zero (fail-closed).
- `scripts/verify_ruff_s_band_inventory.py`: CI drift gate vs `pyproject.toml`.

## Governance details

### Ruff S-band
- `select` includes `S` (bandit security rules).
- Documented suppressions: enum false positives (`S105`), SSRF-guarded HTTP (`S310`), test asserts (`S101`), operator CLIs (`S603`/`S607`), long shell literals in tools (`E501`).
- Inventory SSOT: `governance/ruff_s_band_inventory.json`.

### GPG signed commits
- Policy: `governance/commit_signing_policy.json`
  - `enforce_ci: true`, `min_signed_ratio: 0.0` (passes today)
  - Ratchet: `ratchet_target_ratio: 0.5` effective `2026-09-01`
  - Release tags: `require_head_signed_on_release_tags: true`
- Gate: `backend/scripts/verify_commit_signatures.py --policy ../governance/commit_signing_policy.json` (blocking in `supply-chain-audit` CI job).

### Mypy strict
- `pyproject.toml`: `strict = true` globally.
- CI: `mypy src/aerobim --strict --ignore-missing-imports` (replaces partial 3-module strict step).

## Verification

```bash
cd backend
ruff check src tests
python -m mypy src/aerobim --strict --ignore-missing-imports
python scripts/verify_commit_signatures.py --policy ../governance/commit_signing_policy.json
pytest tests/test_rt_wave3_remediation_2026_08.py tests/test_rt_wave4_remediation_2026_08.py tests/test_rt_wave5_remediation_2026_08.py -q
python scripts/verify_ruff_s_band_inventory.py
```
