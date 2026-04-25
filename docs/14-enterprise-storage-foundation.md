---
title: "Enterprise Storage Foundation"
status: active
version: "0.1.0"
last_updated: "2026-04-25"
tags: [aerobim, storage, postgres, s3, minio, ttl]
---

# Enterprise Storage Foundation

## Purpose

This document records the **shipped foundation** for Iteration B.1.

It is not the final `Postgres + MinIO in CI` state promised by the academic plan.
It defines what is already live in the codebase today, what remains intentionally deferred, and how to enable the new storage seams without breaking the current runtime.

## Shipped In This Pass

1. `ObjectStore` domain port with `put/get/delete/presign` semantics.
2. `LocalObjectStore` adapter for the current local/runtime path.
3. `S3ObjectStore` adapter with lazy `boto3` import for S3/MinIO-compatible buckets.
4. `FilesystemAuditStore` refactored to persist IFC source binaries and drawing previews behind `ObjectStore` instead of hard-wiring file reads at the HTTP layer.
5. `AEROBIM_REPORT_TTL_DAYS` retention policy for persisted report payloads.
6. `PostgresAuditStore` foundation adapter that indexes report summaries in Postgres while full report payload round-tripping remains on the JSON/object path.
7. DI wiring in `bootstrap.py` for local-vs-S3 object storage and optional Postgres summary indexing.

## Current Runtime Contract

- If no enterprise variables are set, AeroBIM continues to use local storage under `AEROBIM_STORAGE_DIR`.
- If `AEROBIM_S3_BUCKET` is set and enterprise extras are installed, artifact writes go through `S3ObjectStore`.
- If `AEROBIM_DB_URL` is set and enterprise extras are installed, report summaries are indexed into Postgres.
- If enterprise extras are not installed, bootstrap falls back to local storage behaviour rather than breaking the runtime.
- Public HTTP paths stay unchanged:
  - `GET /v1/reports/{id}/source/ifc`
  - `GET /v1/reports/{id}/drawing-assets/{asset_id}/preview`
  - `GET /v1/reports/{id}/export/bcf`

## Environment Variables

| Variable | Default | Meaning |
|---|---|---|
| `AEROBIM_DB_URL` | unset | Postgres URL for report-summary indexing |
| `AEROBIM_REPORT_TTL_DAYS` | unset | TTL for persisted reports; unset means unlimited retention |
| `AEROBIM_S3_BUCKET` | unset | Target S3/MinIO bucket |
| `AEROBIM_S3_ENDPOINT_URL` | unset | MinIO/custom endpoint |
| `AEROBIM_S3_REGION` | `us-east-1` | Signing region |
| `AEROBIM_S3_ACCESS_KEY_ID` | unset | Access key |
| `AEROBIM_S3_SECRET_ACCESS_KEY` | unset | Secret key |
| `AEROBIM_S3_PREFIX` | `aerobim` | Key prefix within bucket |

## Validation Evidence

Targeted storage/API validation after the refactor:

- `tests/test_enterprise_storage_foundation.py`
- `tests/test_filesystem_audit_store.py`
- `tests/test_filesystem_audit_store_drawing_assets.py`
- `tests/test_api_security.py`

Focused result for this slice: `61 passed`.

## Still Pending For Full B.1 Exit

1. Full Postgres-first payload hydration instead of summary-only indexing.
2. Alembic migration rail and checked-in migration history.
3. MinIO-backed CI job with real object-store verification.
4. End-to-end evidence that backend suite passes with both Postgres and MinIO enabled.

## Dependency Profile

Use the new enterprise extra when enabling B.1 infrastructure:

```bash
pip install -e ".[enterprise]"
```

This extra is intended to carry the optional storage dependencies without making the default local developer install heavier than necessary.