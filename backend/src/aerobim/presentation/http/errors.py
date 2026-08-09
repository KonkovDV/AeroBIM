"""Public HTTP error detail helpers (RT-ERR-001)."""

from __future__ import annotations

_PUBLIC_BAD_REQUEST = "Invalid request"
_PUBLIC_SERVICE_UNAVAILABLE = "Service unavailable"
_PUBLIC_UPLOAD_TOO_LARGE = "Upload exceeds size limit"
_PUBLIC_UPLOAD_WRITE_FAILED = "Upload write failed"
_PUBLIC_UPLOAD_CONTENT_REJECTED = "Upload content rejected"
_PUBLIC_UPLOAD_ZIP_REJECTED = "Upload archive rejected"
_PUBLIC_UPLOAD_QUOTA_EXCEEDED = "Upload quota exceeded"
_PUBLIC_UPLOAD_PROMOTE_FAILED = "Upload promote failed"
_PUBLIC_UPLOAD_OBJECT_STORE_FAILED = "Object store write failed"
_PUBLIC_HITL_FORBIDDEN = "Expert HITL events require OIDC reviewer identity"
_PUBLIC_SYNC_ANALYZE_DISABLED = "Synchronous analyze disabled; use async submit endpoint"
_PUBLIC_ANALYZE_CONCURRENCY_LIMIT = "Analyze concurrency limit exceeded"
_PUBLIC_HITL_STATE_CONFLICT = "HITL state conflict"
_PUBLIC_STORAGE_BOUNDARY = "Stored object escapes storage boundary"
_PUBLIC_NOT_FOUND = "Object not found"
_PUBLIC_EXPORT_UNAVAILABLE = "Export service unavailable"


def public_bad_request_detail() -> str:
    """Stable client-facing 400 detail — never echo internal ``ValueError`` text."""

    return _PUBLIC_BAD_REQUEST


def public_service_unavailable_detail() -> str:
    """Stable client-facing 503 detail."""

    return _PUBLIC_SERVICE_UNAVAILABLE


def public_upload_too_large_detail() -> str:
    return _PUBLIC_UPLOAD_TOO_LARGE


def public_upload_write_failed_detail() -> str:
    return _PUBLIC_UPLOAD_WRITE_FAILED


def public_upload_content_rejected_detail() -> str:
    return _PUBLIC_UPLOAD_CONTENT_REJECTED


def public_upload_zip_rejected_detail() -> str:
    return _PUBLIC_UPLOAD_ZIP_REJECTED


def public_upload_quota_exceeded_detail() -> str:
    return _PUBLIC_UPLOAD_QUOTA_EXCEEDED


def public_upload_promote_failed_detail() -> str:
    return _PUBLIC_UPLOAD_PROMOTE_FAILED


def public_upload_object_store_failed_detail() -> str:
    return _PUBLIC_UPLOAD_OBJECT_STORE_FAILED


def public_hitl_forbidden_detail() -> str:
    return _PUBLIC_HITL_FORBIDDEN


def public_sync_analyze_disabled_detail() -> str:
    return _PUBLIC_SYNC_ANALYZE_DISABLED


def public_analyze_concurrency_limit_detail() -> str:
    return _PUBLIC_ANALYZE_CONCURRENCY_LIMIT


def public_hitl_state_conflict_detail() -> str:
    return _PUBLIC_HITL_STATE_CONFLICT


def public_storage_boundary_detail() -> str:
    """Stable 409 detail — never echo PathJailError path text to clients."""

    return _PUBLIC_STORAGE_BOUNDARY


def public_not_found_detail() -> str:
    return _PUBLIC_NOT_FOUND


def public_export_unavailable_detail() -> str:
    return _PUBLIC_EXPORT_UNAVAILABLE


__all__ = [
    "public_analyze_concurrency_limit_detail",
    "public_bad_request_detail",
    "public_export_unavailable_detail",
    "public_hitl_forbidden_detail",
    "public_hitl_state_conflict_detail",
    "public_not_found_detail",
    "public_service_unavailable_detail",
    "public_storage_boundary_detail",
    "public_sync_analyze_disabled_detail",
    "public_upload_content_rejected_detail",
    "public_upload_object_store_failed_detail",
    "public_upload_promote_failed_detail",
    "public_upload_quota_exceeded_detail",
    "public_upload_too_large_detail",
    "public_upload_write_failed_detail",
    "public_upload_zip_rejected_detail",
]
