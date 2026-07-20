"""ObjectStore-backed immutable norm-pack version history (P0.3).

Phase 8 residual: versions are tenant-namespaced when ``tenant_id`` is set.
Changing one rule changes ``content_sha256``; mismatch blocks sign-off.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from aerobim.domain.models import NormPackVersionInfo
from aerobim.domain.ports import ObjectStore


def _safe_token(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._:-" else "_" for ch in value)


class ObjectStoreNormRulePackVersionStore:
    def __init__(self, object_store: ObjectStore, *, index_dir: Path) -> None:
        self._store = object_store
        self._index_dir = index_dir / "norm-pack-versions"
        self._index_dir.mkdir(parents=True, exist_ok=True)

    def _index_path(self, pack_id: str, *, tenant_id: str | None = None) -> Path:
        safe = _safe_token(pack_id)
        tenant = (tenant_id or "").strip()
        if tenant:
            tenant_dir = self._index_dir / _safe_token(tenant)
            tenant_dir.mkdir(parents=True, exist_ok=True)
            return tenant_dir / f"{safe}.json"
        return self._index_dir / f"{safe}.json"

    def _object_key(self, pack_id: str, version: str, *, tenant_id: str | None = None) -> str:
        safe_pack = _safe_token(pack_id)
        safe_version = "".join(ch if ch.isalnum() or ch in "._:+-" else "_" for ch in version)
        tenant = (tenant_id or "").strip()
        if tenant:
            return f"tenants/{_safe_token(tenant)}/norm-packs/{safe_pack}/{safe_version}.json"
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
        tenant_id: str | None = None,
    ) -> NormPackVersionInfo:
        existing = {item.version for item in self.list_versions(pack_id, tenant_id=tenant_id)}
        if version in existing:
            raise ValueError(f"Norm pack version already exists: {pack_id}@{version}")
        status = (approval_status or "").strip().lower()
        if status in {"customer_approved", "approved"} and not (approval_ref or "").strip():
            raise ValueError(
                "customer_approved/approved norm pack versions require non-empty approval_ref"
            )
        # Reject synthetic-labeled payloads claiming customer_approved.
        if status in {"customer_approved", "approved"}:
            self._assert_payload_not_synthetic_claim(payload)
        key = self._object_key(pack_id, version, tenant_id=tenant_id)
        # Immutable: refuse overwrite if object already present.
        if self._store.get_bytes(key) is not None:
            raise ValueError(f"ObjectStore key already exists (immutable history): {key}")
        content_sha256 = hashlib.sha256(payload).hexdigest()
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
            tenant_id=(tenant_id or "").strip() or None,
            content_sha256=content_sha256,
        )
        entries = [
            self._record_dict(item) for item in self.list_versions(pack_id, tenant_id=tenant_id)
        ]
        entries.append(self._record_dict(record))
        self._index_path(pack_id, tenant_id=tenant_id).write_text(
            json.dumps(entries, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return record

    def list_versions(
        self,
        pack_id: str,
        *,
        tenant_id: str | None = None,
    ) -> list[NormPackVersionInfo]:
        path = self._index_path(pack_id, tenant_id=tenant_id)
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
                    tenant_id=item.get("tenant_id"),
                    content_sha256=item.get("content_sha256"),
                )
            )
        return out

    def get_version_bytes(
        self,
        pack_id: str,
        version: str,
        *,
        tenant_id: str | None = None,
    ) -> bytes | None:
        for item in self.list_versions(pack_id, tenant_id=tenant_id):
            if item.version == version:
                return self._store.get_bytes(item.object_key)
        return None

    def verify_version_integrity(
        self,
        pack_id: str,
        version: str,
        *,
        tenant_id: str | None = None,
        expected_sha256: str | None = None,
    ) -> str:
        """Recompute payload hash; mismatch blocks sign-off.

        Returns the observed content SHA-256 when integrity holds.
        """

        record = next(
            (
                item
                for item in self.list_versions(pack_id, tenant_id=tenant_id)
                if item.version == version
            ),
            None,
        )
        if record is None:
            raise ValueError(f"Unknown norm pack version: {pack_id}@{version}")
        payload = self._store.get_bytes(record.object_key)
        if payload is None:
            raise ValueError(f"Missing immutable payload for {pack_id}@{version}")
        observed = hashlib.sha256(payload).hexdigest()
        if record.content_sha256 and record.content_sha256.lower() != observed.lower():
            raise ValueError(
                f"Norm pack content hash mismatch for {pack_id}@{version}: "
                f"index={record.content_sha256} observed={observed} — sign-off blocked"
            )
        if expected_sha256 and expected_sha256.lower() != observed.lower():
            raise ValueError(
                f"Norm pack expected hash mismatch for {pack_id}@{version}: "
                f"expected={expected_sha256} observed={observed} — sign-off blocked"
            )
        return observed

    @staticmethod
    def _record_dict(record: NormPackVersionInfo) -> dict[str, object]:
        return {
            "pack_id": record.pack_id,
            "version": record.version,
            "object_key": record.object_key,
            "created_at": record.created_at,
            "created_by": record.created_by,
            "parent_version": record.parent_version,
            "approval_status": record.approval_status,
            "approval_ref": record.approval_ref,
            "tenant_id": record.tenant_id,
            "content_sha256": record.content_sha256,
        }

    @staticmethod
    def _assert_payload_not_synthetic_claim(payload: bytes) -> None:
        try:
            data = json.loads(payload.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return
        if not isinstance(data, dict):
            return
        labels = data.get("claim_labels") or []
        if not isinstance(labels, list):
            return
        synthetic = {
            str(item).strip().lower() for item in labels if isinstance(item, str) and item.strip()
        }
        forbidden = {"synthetic", "fixture", "template", "not-customer-evidence"}
        if synthetic.intersection(forbidden):
            raise ValueError(
                "synthetic/fixture claim_labels cannot be stored as customer_approved (RT-002 open)"
            )
