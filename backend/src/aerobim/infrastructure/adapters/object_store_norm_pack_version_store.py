"""ObjectStore-backed immutable norm-pack version history (P0.3)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from aerobim.domain.models import NormPackVersionInfo
from aerobim.domain.ports import ObjectStore


class ObjectStoreNormRulePackVersionStore:
    def __init__(self, object_store: ObjectStore, *, index_dir: Path) -> None:
        self._store = object_store
        self._index_dir = index_dir / "norm-pack-versions"
        self._index_dir.mkdir(parents=True, exist_ok=True)

    def _index_path(self, pack_id: str) -> Path:
        safe = "".join(ch if ch.isalnum() or ch in "._:-" else "_" for ch in pack_id)
        return self._index_dir / f"{safe}.json"

    def _object_key(self, pack_id: str, version: str) -> str:
        safe_pack = "".join(ch if ch.isalnum() or ch in "._:-" else "_" for ch in pack_id)
        safe_version = "".join(ch if ch.isalnum() or ch in "._:+-" else "_" for ch in version)
        return f"norm-packs/{safe_pack}/{safe_version}.json"

    def save_version(
        self,
        *,
        pack_id: str,
        version: str,
        payload: bytes,
        created_by: str | None,
        parent_version: str | None,
        approval_status: str | None,
        approval_ref: str | None,
    ) -> NormPackVersionInfo:
        existing = {item.version for item in self.list_versions(pack_id)}
        if version in existing:
            raise ValueError(f"Norm pack version already exists: {pack_id}@{version}")
        status = (approval_status or "").strip().lower()
        if status in {"customer_approved", "approved"} and not (approval_ref or "").strip():
            raise ValueError(
                "customer_approved/approved norm pack versions require non-empty approval_ref"
            )
        key = self._object_key(pack_id, version)
        # Immutable: refuse overwrite if object already present.
        if self._store.get_bytes(key) is not None:
            raise ValueError(f"ObjectStore key already exists (immutable history): {key}")
        self._store.put_bytes(key, payload, content_type="application/json")
        record = NormPackVersionInfo(
            pack_id=pack_id,
            version=version,
            object_key=key,
            created_at=datetime.now(tz=UTC).isoformat(),
            created_by=created_by,
            parent_version=parent_version,
            approval_status=approval_status,  # type: ignore[arg-type]
            approval_ref=approval_ref,
        )
        entries = [item.__dict__ for item in self.list_versions(pack_id)]
        entries.append(
            {
                "pack_id": record.pack_id,
                "version": record.version,
                "object_key": record.object_key,
                "created_at": record.created_at,
                "created_by": record.created_by,
                "parent_version": record.parent_version,
                "approval_status": record.approval_status,
                "approval_ref": record.approval_ref,
            }
        )
        self._index_path(pack_id).write_text(
            json.dumps(entries, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return record

    def list_versions(self, pack_id: str) -> list[NormPackVersionInfo]:
        path = self._index_path(pack_id)
        if not path.exists():
            return []
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        if not isinstance(raw, list):
            return []
        out: list[NormPackVersionInfo] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            out.append(
                NormPackVersionInfo(
                    pack_id=str(item["pack_id"]),
                    version=str(item["version"]),
                    object_key=str(item["object_key"]),
                    created_at=str(item["created_at"]),
                    created_by=item.get("created_by"),
                    parent_version=item.get("parent_version"),
                    approval_status=item.get("approval_status"),
                    approval_ref=item.get("approval_ref"),
                )
            )
        return out

    def get_version_bytes(self, pack_id: str, version: str) -> bytes | None:
        for item in self.list_versions(pack_id):
            if item.version == version:
                return self._store.get_bytes(item.object_key)
        return None
