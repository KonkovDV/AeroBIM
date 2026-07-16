# AeroBIM Environment Matrix

## Backend Variables

| Variable | Default | Required | Notes |
|---|---|---:|---|
| `AEROBIM_APP_NAME` | `aerobim-backend` | no | Service label returned by `/health`. |
| `AEROBIM_ENV` | `development` | no | Runtime label. Outside `development`/`dev`/`test`, `AEROBIM_API_BEARER_TOKEN` is mandatory (fail-closed). |
| `AEROBIM_HOST` | `127.0.0.1` | no | Use `0.0.0.0` for Docker/container binding. |
| `AEROBIM_PORT` | `8080` | no | HTTP listen port. |
| `AEROBIM_STORAGE_DIR` | `var/reports` | no | Parent directory for persisted JSON reports. Runtime store writes to `reports/*.json` below this root. Symlinks under this root are rejected. |
| `AEROBIM_DEBUG` | `true` | no | Enables debug defaults including permissive local frontend CORS fallback. |
| `AEROBIM_CORS_ORIGINS` | empty | no | Comma-separated explicit frontend origins. In debug mode, empty falls back to `http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173`. |
| `AEROBIM_API_BEARER_TOKEN` | empty | conditional | Required for all `/v1/*` when set; required at startup outside development/test. |
| `AEROBIM_CLASH_AFFECTS_PASS` | `false` | no | When `true`, hard clashes or failed clash capability set `summary.passed=false`. |
| `AEROBIM_MAX_IFC_BYTES` | `268435456` | no | Max IFC file size (256 MiB default). |
| `AEROBIM_BCF_API_BASE_URL` | empty | no | OpenCDE hub base URL for BCF API 3.0 topic push. |
| `AEROBIM_BCF_API_TOKEN` | empty | conditional | Bearer access token from Foundation OAuth2 / hub. |
| `AEROBIM_BCF_API_PROJECT_ID` | empty | no | Default BCF project id for push endpoint. |
| `AEROBIM_BCF_API_VERSION` | `3.0` | no | BCF API version path segment. |
| `AEROBIM_OIDC_ISSUER` | empty | conditional | OIDC issuer (`iss`) for JWT validation. |
| `AEROBIM_OIDC_AUDIENCE` | empty | conditional | Expected JWT `aud`. |
| `AEROBIM_OIDC_JWKS_URL` | empty | conditional | JWKS URL; requires enterprise `PyJWT`. |
| `AEROBIM_REDIS_URL` | empty | no | When set, analyze jobs use Redis store (enterprise `redis`). |
| `AEROBIM_BSI_VALIDATION_URL` | empty | no | buildingSMART Validation Service base URL (e.g. `https://dev.validate.buildingsmart.org`). |
| `AEROBIM_BSI_API_TOKEN` | empty | conditional | Token auth for bSI Validation Service when URL is set. |
| `AEROBIM_BSI_LOCAL_CERT` | `false` | no | When `true` and remote URL unset, emit a local schema-pack certificate id on reports. |
| `AEROBIM_REMARK_LOCALE` | `ru` | no | Remark template language: `ru` or `en`. |
| `AEROBIM_DB_URL` | empty | no | Optional Postgres URL for report-summary indexing (supports filtered `list_reports`). |
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
| `VITE_AEROBIM_API_BEARER_TOKEN` | empty | conditional | Must match backend `AEROBIM_API_BEARER_TOKEN` when the API is secured. |

## Dependency Profiles

| Install Profile | Command | Use Case |
|---|---|---|
| backend minimal runtime | `pip install -e .` | IFC/IDS/report APIs without raster OCR |
| backend with OCR baseline | `pip install -e ".[raster]"` | PDF + raster deterministic drawing extraction |
| backend with clash detection | `pip install -e ".[clash]"` | real IfcClash-backed geometry clash detection |
| backend with Docling extraction | `pip install -e ".[docling]"` | non-text requirement extraction from office/PDF packages |
| backend with enterprise storage | `pip install -e ".[enterprise]"` | optional S3/Postgres storage foundation |
| backend full dev | `pip install -e ".[dev,raster]"` | local development, typing, tests, OCR baseline |
| backend full capability bench | `pip install -e ".[dev,raster,clash,docling,enterprise]"` | full local capability set for integration and demo work |
| frontend dev/build | `npm install` | browser review shell |

Optional integration rail:

- `backend/tests/test_optional_adapter_integrations.py` auto-skips unless `ifcclash` and/or `docling` are installed in the active backend environment.
- first real runtime proof for both extras has been captured in the project backend venv with `.[clash,docling]` installed.

## Deployment Notes

- Docker backend image now installs `.[raster]`, so PDF and raster drawing analysis are available in the containerized runtime.
- Clash detection and Docling extraction remain explicit opt-in extras in the current phase.
- Frontend build output is static and can be hosted independently from the backend.
- There is no dedicated OCR cache environment variable in this tranche; RapidOCR uses its own runtime model management defaults.