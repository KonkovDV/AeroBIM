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
        return cls(
            application_name=os.getenv("AEROBIM_APP_NAME", "aerobim-backend"),
            environment=os.getenv("AEROBIM_ENV", "development"),
            host=os.getenv("AEROBIM_HOST", "127.0.0.1"),
            port=_read_int("AEROBIM_PORT", 8080),
            storage_dir=Path(os.getenv("AEROBIM_STORAGE_DIR", "var/reports")),
            debug=debug,
            cors_origins=origins,
            api_bearer_token=(os.getenv("AEROBIM_API_BEARER_TOKEN") or "").strip() or None,
        )
