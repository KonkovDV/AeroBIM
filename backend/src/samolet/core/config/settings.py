from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


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

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            application_name=os.getenv("SAMOLET_APP_NAME", "samolet-backend"),
            environment=os.getenv("SAMOLET_ENV", "development"),
            host=os.getenv("SAMOLET_HOST", "127.0.0.1"),
            port=_read_int("SAMOLET_PORT", 8080),
            storage_dir=Path(os.getenv("SAMOLET_STORAGE_DIR", "var/reports")),
            debug=_read_bool("SAMOLET_DEBUG", True),
        )
