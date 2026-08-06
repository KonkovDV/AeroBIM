"""Multipart document upload route (storage jail + quarantine + quotas)."""

import hashlib
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from aerobim.core.security.path_jail import (
    PathJailError,
    reject_symlinks,
    tenant_storage_prefix,
)
from aerobim.core.security.upload_content import UploadContentError, validate_upload_content
from aerobim.core.security.upload_quota import UploadQuotaExceeded
from aerobim.core.security.zip_limits import ZipBombError, inspect_zip_path
from aerobim.domain.object_acl import AuthPrincipal
from aerobim.presentation.http.context import (
    UPLOAD_HASH_CHUNK,
    UPLOAD_SNIFF_BYTES,
    ApiContext,
)


def build_uploads_router(ctx: ApiContext) -> APIRouter:
    router = APIRouter()
    settings = ctx.settings
    logger = ctx.logger

    @router.post("/v1/uploads")
    async def upload_document(
        file: Annotated[UploadFile, File(...)],
        principal: Annotated[AuthPrincipal, Depends(ctx.require_bearer_auth)],
    ) -> dict[str, object]:
        """Multipart document ingest into the storage jail (TZ P0).

        Returns a storage-relative ``path`` suitable for ``ifc_path`` / drawing paths
        on subsequent analyze calls. Validates extension + magic bytes and enforces
        ``max_upload_bytes`` for all document types. Content is quarantined until
        checks pass, then promoted under ``tenants/{tenant}/uploads/``.
        """
        tenant_key = (
            principal.tenant_id or principal.subject or "anonymous"
        ).strip() or "anonymous"
        try:
            # Encode once via tenant_storage_prefix — never pass a pre-encoded segment.
            tenant_prefix = tenant_storage_prefix(tenant_key)
            tenant_seg = tenant_prefix.rstrip("/").rsplit("/", 1)[-1]
        except PathJailError as exc:
            raise HTTPException(status_code=400, detail="Invalid tenant identity") from exc
        raw_name = (file.filename or "upload.bin").replace("\\", "/").split("/")[-1]
        for banned in ':*?"<>|\r\n':
            raw_name = raw_name.replace(banned, "")
        safe_name = (raw_name.strip() or "upload.bin")[:180]
        upload_id = uuid4().hex
        relative_path = f"{tenant_prefix}uploads/{upload_id}/{safe_name}"
        base = settings.storage_dir.resolve()
        quarantine = (
            settings.storage_dir / "quarantine" / tenant_seg / upload_id / safe_name
        ).resolve()
        try:
            # Resolve through the jail before any write so ``..`` tokens cannot escape.
            from aerobim.core.security.path_jail import resolve_storage_path

            target = resolve_storage_path(relative_path, base=settings.storage_dir)
        except PathJailError as exc:
            raise HTTPException(status_code=400, detail="Invalid upload path") from exc
        quarantine.parent.mkdir(parents=True, exist_ok=True)
        try:
            reject_symlinks(quarantine.parent, base=base)
            if not quarantine.resolve().is_relative_to(base):
                raise PathJailError("Quarantine path escapes storage boundary")
        except PathJailError as exc:
            raise HTTPException(status_code=409, detail="Upload path rejected") from exc

        max_bytes = settings.max_upload_bytes
        total = 0
        digest = hashlib.sha256()
        sniff_buf = bytearray()
        try:
            with quarantine.open("wb") as handle:
                while True:
                    chunk = await file.read(UPLOAD_HASH_CHUNK)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > max_bytes:
                        raise HTTPException(
                            status_code=413,
                            detail=(
                                f"Upload exceeds size limit ({total} bytes > {max_bytes} bytes)"
                            ),
                        )
                    digest.update(chunk)
                    if len(sniff_buf) < UPLOAD_SNIFF_BYTES:
                        need = UPLOAD_SNIFF_BYTES - len(sniff_buf)
                        sniff_buf.extend(chunk[:need])
                    handle.write(chunk)
        except HTTPException:
            quarantine.unlink(missing_ok=True)
            raise
        except OSError as exc:
            quarantine.unlink(missing_ok=True)
            raise HTTPException(status_code=500, detail=f"Upload write failed: {exc}") from exc

        if total == 0:
            quarantine.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail="Empty upload")

        try:
            sniffed = validate_upload_content(
                filename=safe_name,
                payload=bytes(sniff_buf)
                if sniff_buf
                else quarantine.read_bytes()[:UPLOAD_SNIFF_BYTES],
                declared_content_type=file.content_type,
            )
            if sniffed.kind == "zip" or safe_name.lower().endswith(
                (".zip", ".ifczip", ".docx", ".xlsx", ".pptx")
            ):
                inspect_zip_path(quarantine)
        except UploadContentError as exc:
            quarantine.unlink(missing_ok=True)
            raise HTTPException(status_code=415, detail=str(exc)) from exc
        except ZipBombError as exc:
            quarantine.unlink(missing_ok=True)
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        try:
            quota = ctx.upload_quota_store.reserve(tenant_key, size_bytes=total)
        except UploadQuotaExceeded as exc:
            quarantine.unlink(missing_ok=True)
            raise HTTPException(status_code=429, detail=str(exc)) from exc

        # Promote out of quarantine only after content + zip checks pass.
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            reject_symlinks(target.parent, base=base)
            quarantine.replace(target)
        except (OSError, PathJailError) as exc:
            quarantine.unlink(missing_ok=True)
            try:
                ctx.upload_quota_store.release(tenant_key, size_bytes=total)
            except Exception:  # noqa: BLE001 — best-effort compensate; surface promote error
                logger.warning(
                    "upload quota release failed after promote error",
                    tenant_id=tenant_key,
                    size_bytes=total,
                )
            raise HTTPException(
                status_code=500, detail=f"Quarantine promote failed: {exc}"
            ) from exc

        if ctx.object_store is not None:
            try:
                payload = target.read_bytes()
                ctx.object_store.put_bytes(
                    relative_path.replace("\\", "/"),
                    payload,
                    content_type=sniffed.mime or file.content_type,
                )
                del payload
            except Exception as exc:
                target.unlink(missing_ok=True)
                try:
                    ctx.upload_quota_store.release(tenant_key, size_bytes=total)
                except Exception:  # noqa: BLE001 — best-effort compensate
                    logger.warning(
                        "upload quota release failed after object-store error",
                        tenant_id=tenant_key,
                        size_bytes=total,
                    )
                raise HTTPException(
                    status_code=500, detail=f"Object store put failed: {exc}"
                ) from exc

        return {
            "upload_id": upload_id,
            "filename": safe_name,
            "path": relative_path.replace("\\", "/"),
            "size_bytes": total,
            "content_type": sniffed.mime or file.content_type,
            "sniffed_kind": sniffed.kind,
            "sha256": digest.hexdigest(),
            "tenant_id": tenant_key,
            "quota": {
                "day": quota.day,
                "upload_count": quota.upload_count,
                "bytes_used": quota.bytes_used,
                "max_uploads": quota.max_uploads,
                "max_bytes": quota.max_bytes,
            },
        }

    return router
