from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_DEBUG_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
)


def _read_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    return int(raw)


def _read_optional_int(name: str) -> int | None:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return None
    return int(raw)


def _read_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    application_name: str
    environment: str
    host: str
    port: int
    storage_dir: Path
    debug: bool
    cors_origins: tuple[str, ...] = ()
    api_bearer_token: str | None = None
    cross_doc_contradiction_severity: str = "warning"
    db_url: str | None = None
    s3_endpoint_url: str | None = None
    s3_bucket: str | None = None
    s3_region: str = "us-east-1"
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_prefix: str = "aerobim"
    report_ttl_days: int | None = None
    """Severity emitted for cross-document contradictions.

    Set to ``"error"`` to make all cross-document contradictions block delivery
    (sets ``passed=False`` on the report).  Defaults to ``"warning"`` so that
    contradictions are surfaced but non-blocking.  Accepted values: ``"error"``,
    ``"warning"``, ``"info"``.
    """

    @classmethod
    def from_env(cls) -> Settings:
        debug = _read_bool("AEROBIM_DEBUG", True)
        raw_origins = os.getenv("AEROBIM_CORS_ORIGINS", "")
        if raw_origins:
            origins = tuple(o.strip() for o in raw_origins.split(",") if o.strip())
        elif debug:
            origins = _DEBUG_CORS_ORIGINS
        else:
            origins = ()
        raw_severity = (os.getenv("AEROBIM_CROSS_DOC_SEVERITY") or "warning").strip().lower()
        cross_doc_severity = (
            raw_severity if raw_severity in {"error", "warning", "info"} else "warning"
        )
        return cls(
            application_name=os.getenv("AEROBIM_APP_NAME", "aerobim-backend"),
            environment=os.getenv("AEROBIM_ENV", "development"),
            host=os.getenv("AEROBIM_HOST", "127.0.0.1"),
            port=_read_int("AEROBIM_PORT", 8080),
            storage_dir=Path(os.getenv("AEROBIM_STORAGE_DIR", "var/reports")),
            debug=debug,
            cors_origins=origins,
            api_bearer_token=(os.getenv("AEROBIM_API_BEARER_TOKEN") or "").strip() or None,
            cross_doc_contradiction_severity=cross_doc_severity,
            db_url=(os.getenv("AEROBIM_DB_URL") or "").strip() or None,
            s3_endpoint_url=(os.getenv("AEROBIM_S3_ENDPOINT_URL") or "").strip() or None,
            s3_bucket=(os.getenv("AEROBIM_S3_BUCKET") or "").strip() or None,
            s3_region=(os.getenv("AEROBIM_S3_REGION") or "us-east-1").strip() or "us-east-1",
            s3_access_key_id=(os.getenv("AEROBIM_S3_ACCESS_KEY_ID") or "").strip() or None,
            s3_secret_access_key=(os.getenv("AEROBIM_S3_SECRET_ACCESS_KEY") or "").strip()
            or None,
            s3_prefix=(os.getenv("AEROBIM_S3_PREFIX") or "aerobim").strip() or "aerobim",
            report_ttl_days=_read_optional_int("AEROBIM_REPORT_TTL_DAYS"),
        )
