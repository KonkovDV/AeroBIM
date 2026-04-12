# AeroBIM Storage And Retention

## Persistence Boundary

The canonical persisted artifact is the JSON validation report written by `FilesystemAuditStore`.

Path layout:

```text
${AEROBIM_STORAGE_DIR}/reports/<report_id>.json
${AEROBIM_STORAGE_DIR}/drawing-assets/<report_id>/<asset_id>.png
```

## What Is Persisted

- report metadata (`report_id`, `request_id`, `created_at`)
- normalized requirements
- materialized issues and remarks
- drawing annotations
- persisted drawing preview assets for PDF/image-backed evidence
- clash results

## What Is Not Persisted

- HTML export files
- BCF zip files
- frontend state

HTML and BCF exports are derived on demand from the stored JSON report.
Drawing previews are derived at report-save time from PDF/image-backed drawing sources and stored as report-scoped assets.

## Retention Guidance

### Local development

- retain reports only as long as the audit cycle is active;
- delete stale `reports/*.json` files when fixture noise obscures current validation work.

### Shared demo or review environment

- retain the last review cycle or sprint batch only;
- archive externally if reports must be attached to delivery evidence.

### Container runtime

- bind-mount or named-volume the storage directory;
- treat the volume as the source of truth for report continuity.

## Cleanup Guidance

- remove only the report JSON files you no longer need;
- remove the paired `drawing-assets/<report_id>/` directory together with a report when cleaning old evidence;
- preserve the storage directory itself so the backend can keep writing atomically;
- treat container volume deletion as a full persistence reset, not a routine maintenance action.