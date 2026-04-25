# AeroBIM Environment Matrix

## Backend Variables

| Variable | Default | Required | Notes |
|---|---|---:|---|
| `AEROBIM_APP_NAME` | `aerobim-backend` | no | Service label returned by `/health`. |
| `AEROBIM_ENV` | `development` | no | Drives runtime labelling only. |
| `AEROBIM_HOST` | `127.0.0.1` | no | Use `0.0.0.0` for Docker/container binding. |
| `AEROBIM_PORT` | `8080` | no | HTTP listen port. |
| `AEROBIM_STORAGE_DIR` | `var/reports` | no | Parent directory for persisted JSON reports. Runtime store writes to `reports/*.json` below this root. |
| `AEROBIM_DEBUG` | `true` | no | Enables debug defaults including permissive local frontend CORS fallback. |
| `AEROBIM_CORS_ORIGINS` | empty | no | Comma-separated explicit frontend origins. In debug mode, empty falls back to `http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173`. |
| `AEROBIM_DB_URL` | empty | no | Optional Postgres URL for report-summary indexing. |
| `AEROBIM_REPORT_TTL_DAYS` | empty | no | Optional TTL for persisted report payloads; empty means unlimited retention. |
| `AEROBIM_S3_BUCKET` | empty | no | Optional S3/MinIO bucket for binary artifacts. |
| `AEROBIM_S3_ENDPOINT_URL` | empty | no | Custom S3-compatible endpoint, e.g. MinIO. |
| `AEROBIM_S3_REGION` | `us-east-1` | no | Signing region for S3-compatible object storage. |
| `AEROBIM_S3_ACCESS_KEY_ID` | empty | no | Access key for S3-compatible storage. |
| `AEROBIM_S3_SECRET_ACCESS_KEY` | empty | no | Secret key for S3-compatible storage. |
| `AEROBIM_S3_PREFIX` | `aerobim` | no | Prefix prepended to object keys in S3-compatible storage. |

## Frontend Variable

| Variable | Default | Required | Notes |
|---|---|---:|---|
| `VITE_AEROBIM_API_BASE_URL` | `http://localhost:8080` | no | Compile-time API target for the review shell. |

## Dependency Profiles

| Install Profile | Command | Use Case |
|---|---|---|
| backend minimal runtime | `pip install -e .` | IFC/IDS/report APIs without raster OCR |
| backend with OCR baseline | `pip install -e ".[vision]"` | PDF + raster deterministic drawing extraction |
| backend with clash detection | `pip install -e ".[clash]"` | real IfcClash-backed geometry clash detection |
| backend with Docling extraction | `pip install -e ".[docling]"` | non-text requirement extraction from office/PDF packages |
| backend with enterprise storage | `pip install -e ".[enterprise]"` | optional S3/Postgres storage foundation |
| backend full dev | `pip install -e ".[dev,vision]"` | local development, typing, tests, OCR baseline |
| backend full capability bench | `pip install -e ".[dev,vision,clash,docling,enterprise]"` | full local capability set for integration and demo work |
| frontend dev/build | `npm install` | browser review shell |

Optional integration rail:

- `backend/tests/test_optional_adapter_integrations.py` auto-skips unless `ifcclash` and/or `docling` are installed in the active backend environment.
- first real runtime proof for both extras has been captured in the project backend venv with `.[clash,docling]` installed.

## Deployment Notes

- Docker backend image now installs `.[vision]`, so PDF and raster drawing analysis are available in the containerized runtime.
- Clash detection and Docling extraction remain explicit opt-in extras in the current phase.
- Frontend build output is static and can be hosted independently from the backend.
- There is no dedicated OCR cache environment variable in this tranche; RapidOCR uses its own runtime model management defaults.