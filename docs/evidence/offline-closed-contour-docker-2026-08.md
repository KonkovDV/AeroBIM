# И1 closed-contour offline — Docker evidence (2026-08-08)

**Status:** **CLOSED** (Docker image-track)  
**JSON:** [`offline-closed-contour-docker-2026-08.json`](../evidence/offline-closed-contour-docker-2026-08.json)  
**Runbook:** [`docs/ops/OFFLINE_CLOSED_CONTOUR_DOCKER_2026_08.md`](../../docs/ops/OFFLINE_CLOSED_CONTOUR_DOCKER_2026_08.md)

## Commands (local, 2026-08-08)

```bash
cd backend
python -m aerobim.tools.offline_bundle build      # PASS
python -m aerobim.tools.offline_bundle verify     # PASS
python -m aerobim.tools.offline_bundle smoke      # PASS
python -m aerobim.tools.offline_bundle closed-contour --smoke  # PASS
```

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
