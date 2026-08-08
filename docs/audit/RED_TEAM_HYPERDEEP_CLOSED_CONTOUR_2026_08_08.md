---
title: "Red Team Hyperdeep — Closed-Contour Docker (И1)"
date: 2026-08-08
status: remediated
i1_status: CLOSED_DOCKER_TRACK
---

# Red Team Hyperdeep Audit — Closed-Contour Docker (И1)

**Scope:** `offline_bundle`, install scripts, Dockerfile, CI `offline-bundle-smoke`, evidence artifacts.  
**Method:** code review + live Docker probes (Windows Docker Desktop 29.5.2).  
**Verdict:** **2 P1 findings remediated** in this pass; И1 Docker track **remains CLOSED** with stricter smoke.

---

## Finding registry

| ID | Sev | Status | Title |
|---|---|---|---|
| RT-CC-H01 | P1 | **REMEDIATED** | `install_offline.*` used `-p` + `--network none` → host port refused (Windows) |
| RT-CC-H02 | P1 | **REMEDIATED** | Install scripts defaulted weak `offline-bundle-token` without operator gate |
| RT-CC-H03 | P2 | **REMEDIATED** | Smoke lacked egress-block + unauthenticated 401 probes |
| RT-CC-H04 | P2 | **REMEDIATED** | `wheelhouse-OUT_OF_SCOPE.json` absent from build manifest |
| RT-CC-H05 | P2 | **REMEDIATED** | CI did not run `closed-contour --smoke` |
| RT-CC-H06 | — | **NOT_VULNERABLE** | Egress to `1.1.1.1` blocked under `--network none` |
| RT-CC-H07 | — | **NOT_VULNERABLE** | `/v1/system/capabilities` returns 401 without bearer |
| RT-CC-H08 | — | **NOT_VULNERABLE** | Manifest sha256 verify catches tamper (unit tests) |
| RT-CC-H09 | INFO | **ACCEPTED** | Host HTTP via `-p` unreliable with `--network none` — documented; use `docker exec` |
| RT-CC-H10 | P2 | **REMEDIATED** (R2) | Install scripts only health-checked; smoke ran full auth+egress probes |
| RT-CC-H11 | P2 | **REMEDIATED** (R2) | `verify` / `closed-contour` did not detect bundle/backend Dockerfile+lock drift |

---

## RT-CC-H01 — Install script host port mapping (P1, REMEDIATED)

**Probe:** `docker run --network none -p 18080:8080` → host `http://127.0.0.1:18080/health` → **Connection refused** (WinError 10061).

**Root cause:** Install scripts published host ports while runtime uses `--network none`. Smoke correctly used `docker exec` only; install path diverged.

**Fix:** Remove `-p` from `install_offline.sh` / `.ps1`; post-start health via `docker exec`; document operator pattern.

---

## RT-CC-H02 — Default demo token (P1, REMEDIATED)

**Issue:** Install scripts defaulted `AEROBIM_API_BEARER_TOKEN=offline-bundle-token`.

**Fix:** Require explicit token; refuse demo token unless `AEROBIM_OFFLINE_ALLOW_DEMO_TOKEN=1` (smoke/lab only).

---

## RT-CC-H03 — Smoke probe depth (P2, REMEDIATED)

**Fix:** `_container_probe_command()` adds unauthenticated 401 check + egress block probe (`1.1.1.1`). Token read from container env (shared with install scripts).

---

## RT-CC-H10 — Install script probe gap (P2, REMEDIATED, round 2)

**Issue:** `install_offline.sh` / `.ps1` only curled `/health`; smoke validated auth + egress — operator false confidence after install.

**Fix:** Install scripts invoke the same `_container_probe_command()` as `closed-contour --smoke`.

---

## RT-CC-H11 — Bundle/backend drift (P2, REMEDIATED, round 2)

**Issue:** `verify_manifest` checked tarball integrity only; stale Dockerfile or lockfile in bundle could pass verify after backend edits.

**Fix:** `verify_bundle_source_sync()` compares bundle `Dockerfile` + lockfiles to live `backend/` during `verify` and `closed-contour`.

---

## Verification (post-remediation)

```bash
cd backend
python -m pytest tests/test_offline_bundle_manifest.py -q
python -m aerobim.tools.offline_bundle build
python -m aerobim.tools.offline_bundle closed-contour --smoke
```

Expected: unit tests pass (13); smoke prints `offline bundle probes: health+auth+egress OK`; verify reports no bundle/backend drift.

---

## Residual / accepted

| Item | Notes |
|---|---|
| Host `-p` with `--network none` | Unreliable on some engines — operator uses `docker exec` |
| Bare-metal wheelhouse | OUT_OF_SCOPE |
| Full CycloneDX SBOM | SPDX-lite only |

**Checkpoint:** RT-001/002/003 unchanged OPEN. И1 eng track **CLOSED**.
