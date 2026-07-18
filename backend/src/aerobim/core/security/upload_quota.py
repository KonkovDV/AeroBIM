"""Per-tenant upload quota accounting (filesystem counter)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


class UploadQuotaExceeded(ValueError):
    """Raised when a tenant exceeds configured upload quotas."""


@dataclass(frozen=True)
class QuotaSnapshot:
    tenant_id: str
    day: str
    upload_count: int
    bytes_used: int
    max_uploads: int | None
    max_bytes: int | None


class FilesystemUploadQuotaStore:
    """Day-bucketed counters under ``storage_dir/quotas/<tenant>/<YYYY-MM-DD>.json``."""

    def __init__(
        self,
        storage_dir: Path,
        *,
        max_uploads_per_day: int | None = None,
        max_bytes_per_day: int | None = None,
    ) -> None:
        self._root = storage_dir / "quotas"
        self._root.mkdir(parents=True, exist_ok=True)
        self._max_uploads = (
            max_uploads_per_day if max_uploads_per_day and max_uploads_per_day > 0 else None
        )
        self._max_bytes = max_bytes_per_day if max_bytes_per_day and max_bytes_per_day > 0 else None

    def _day(self) -> str:
        return datetime.now(tz=UTC).strftime("%Y-%m-%d")

    def _path(self, tenant_id: str, day: str) -> Path:
        safe = (tenant_id or "anonymous").strip().replace("/", "_").replace(
            "\\", "_"
        ) or "anonymous"
        folder = self._root / safe
        folder.mkdir(parents=True, exist_ok=True)
        return folder / f"{day}.json"

    def _load(self, path: Path) -> dict[str, int]:
        if not path.exists():
            return {"upload_count": 0, "bytes_used": 0}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"upload_count": 0, "bytes_used": 0}
        return {
            "upload_count": int(data.get("upload_count") or 0),
            "bytes_used": int(data.get("bytes_used") or 0),
        }

    def snapshot(self, tenant_id: str) -> QuotaSnapshot:
        day = self._day()
        data = self._load(self._path(tenant_id, day))
        return QuotaSnapshot(
            tenant_id=tenant_id or "anonymous",
            day=day,
            upload_count=data["upload_count"],
            bytes_used=data["bytes_used"],
            max_uploads=self._max_uploads,
            max_bytes=self._max_bytes,
        )

    def assert_can_accept(self, tenant_id: str, *, size_bytes: int) -> None:
        snap = self.snapshot(tenant_id)
        if self._max_uploads is not None and snap.upload_count + 1 > self._max_uploads:
            raise UploadQuotaExceeded(
                "Tenant upload count quota exceeded "
                f"({snap.upload_count + 1} > {self._max_uploads}/day)"
            )
        if self._max_bytes is not None and snap.bytes_used + size_bytes > self._max_bytes:
            raise UploadQuotaExceeded(
                f"Tenant upload bytes quota exceeded "
                f"({snap.bytes_used + size_bytes} > {self._max_bytes}/day)"
            )

    def record(self, tenant_id: str, *, size_bytes: int) -> QuotaSnapshot:
        day = self._day()
        path = self._path(tenant_id, day)
        data = self._load(path)
        data["upload_count"] = int(data["upload_count"]) + 1
        data["bytes_used"] = int(data["bytes_used"]) + max(0, int(size_bytes))
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return self.snapshot(tenant_id)


__all__ = [
    "FilesystemUploadQuotaStore",
    "QuotaSnapshot",
    "UploadQuotaExceeded",
]
