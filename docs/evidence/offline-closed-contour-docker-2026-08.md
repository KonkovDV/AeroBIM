# И1 closed-contour offline — Docker evidence (2026-08-08)

**Status:** **CLOSED** (Docker image-track, hyperdeep audited)  
**Hyperdeep report:** [`docs/audit/RED_TEAM_HYPERDEEP_CLOSED_CONTOUR_2026_08_08.md`](../audit/RED_TEAM_HYPERDEEP_CLOSED_CONTOUR_2026_08_08.md)  
**JSON:** [`offline-closed-contour-docker-2026-08.json`](../../audit/evidence/offline-closed-contour-docker-2026-08.json)  
**Runbook:** [`docs/offline-deployment-2026.md`](../../docs/offline-deployment-2026.md)

## Commands (local, 2026-08-08 hyperdeep pass)

```bash
cd backend
python -m pytest tests/test_offline_bundle_manifest.py -q   # 12 passed
python -m aerobim.tools.offline_bundle build                # PASS
python -m aerobim.tools.offline_bundle closed-contour --smoke  # PASS probes OK
```

Smoke probes: health 200, unauthenticated capabilities 401, bearer capabilities 200, egress to 1.1.1.1 blocked.

## Image

| Field | Value |
|---|---|
| tag | `aerobim-backend:offline-bundle` |
| id | `sha256:c8512d54c6d0…` |
| tar sha256 | `4c97430d1e8e70fa24f9d69374fed8e34848c7c19fb9073e7305d9bb63bdeaf7` |
| tar bytes | 864,927,744 |

## И1 scope

- **In scope:** Docker load from tar + `--network none` runtime on air-gap host with Docker.
- **Out of scope:** bare-metal pip wheelhouse (`wheelhouse` exit 2).
