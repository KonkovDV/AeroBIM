"""Multipart document upload route (storage jail + quarantine + quotas)."""

import hashlib
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from aerobim.core.security.path_jail import (
    PathJailError,
    reject_symlinks,
    sanitize_upload_filename,
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
from aerobim.presentation.http.errors import (
    public_upload_content_rejected_detail,
    public_upload_object_store_failed_detail,
    public_upload_promote_failed_detail,
    public_upload_quota_exceeded_detail,
    public_upload_too_large_detail,
    public_upload_write_failed_detail,
    public_upload_zip_rejected_detail,
)


def build_uploads_router(ctx: ApiContext) -> APIRouter:
    router = APIRouter()
    settings = ctx.settings
    logger = ctx.logger

    @router.post("/v1/uploads")
    async def upload_document(
        request: Request,
        file: Annotated[UploadFile, File(...)],
        principal: Annotated[AuthPrincipal, Depends(ctx.require_bearer_auth)],
    ) -> dict[str, object]:
        """Multipart document ingest into the storage jail (TZ P0).

        Returns a storage-relative ``path`` suitable for ``ifc_path`` / drawing paths
        on subsequent analyze calls. Validates extension + magic bytes and enforces
        per-type ingest caps (office vs model) under the ``max_upload_bytes`` envelope.
        Content is quarantined until checks pass, then promoted under
        ``tenants/{tenant}/uploads/``.
        """
        tenant_key = (
            principal.tenant_id or principal.subject or "anonymous"
        ).strip() or "anonymous"
        try:
            tenant_prefix = tenant_storage_prefix(tenant_key)
            tenant_seg = tenant_prefix.rstrip("/").rsplit("/", 1)[-1]
        except PathJailError as exc:
            raise HTTPException(status_code=400, detail="Invalid tenant identity") from exc

        try:
            safe_name = sanitize_upload_filename(file.filename or "upload.bin")
        except PathJailError as exc:
            raise HTTPException(status_code=400, detail="Invalid upload filename") from exc

        max_bytes = settings.upload_limit_for_filename(safe_name)
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                declared = int(content_length)
            except ValueError:
                declared = -1
            if declared > max_bytes:
                raise HTTPException(
                    status_code=413,
                    detail=public_upload_too_large_detail(),
                )

        upload_id = uuid4().hex
        try:
            ctx.upload_quota_store.reconcile_stale_holds()
            ctx.upload_quota_store.reserve(tenant_key, size_bytes=max_bytes, hold_id=upload_id)
        except UploadQuotaExceeded as exc:
            logger.warning(
                "upload quota reserve-ahead failed", tenant_id=tenant_key, detail=str(exc)
            )
            raise HTTPException(
                status_code=429,
                detail=public_upload_quota_exceeded_detail(),
            ) from exc
        held_bytes = max_bytes

        def _drop_quota() -> None:
            nonlocal held_bytes
            if held_bytes <= 0:
                ctx.upload_quota_store.clear_hold(tenant_key, upload_id)
                return
            try:
                ctx.upload_quota_store.release(tenant_key, size_bytes=held_bytes)
            except Exception:  # noqa: BLE001 — best-effort compensate
                logger.warning(
                    "upload quota release failed",
                    tenant_id=tenant_key,
                    size_bytes=held_bytes,
                )
            held_bytes = 0
            ctx.upload_quota_store.clear_hold(tenant_key, upload_id)

        relative_path = f"{tenant_prefix}uploads/{upload_id}/{safe_name}"
        base = settings.storage_dir.resolve()
        quarantine = (
            settings.storage_dir / "quarantine" / tenant_seg / upload_id / safe_name
        ).resolve()
        try:
            from aerobim.core.security.path_jail import resolve_storage_path

            target = resolve_storage_path(relative_path, base=settings.storage_dir)
        except PathJailError as exc:
            _drop_quota()
            raise HTTPException(status_code=400, detail="Invalid upload path") from exc
        quarantine.parent.mkdir(parents=True, exist_ok=True)
        try:
            reject_symlinks(quarantine.parent, base=base)
            if not quarantine.resolve().is_relative_to(base):
                raise PathJailError("Quarantine path escapes storage boundary")
        except PathJailError as exc:
            _drop_quota()
            raise HTTPException(status_code=409, detail="Upload path rejected") from exc

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
                            detail=public_upload_too_large_detail(),
                        )
                    digest.update(chunk)
                    if len(sniff_buf) < UPLOAD_SNIFF_BYTES:
                        need = UPLOAD_SNIFF_BYTES - len(sniff_buf)
                        sniff_buf.extend(chunk[:need])
                    handle.write(chunk)
        except HTTPException:
            quarantine.unlink(missing_ok=True)
            _drop_quota()
            raise
        except OSError as exc:
            quarantine.unlink(missing_ok=True)
            _drop_quota()
            logger.error("upload write failed", detail=str(exc))
            raise HTTPException(
                status_code=500,
                detail=public_upload_write_failed_detail(),
            ) from exc

        if total == 0:
            quarantine.unlink(missing_ok=True)
            _drop_quota()
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
            _drop_quota()
            logger.warning("upload content rejected", detail=str(exc))
            raise HTTPException(
                status_code=415,
                detail=public_upload_content_rejected_detail(),
            ) from exc
        except ZipBombError as exc:
            quarantine.unlink(missing_ok=True)
            _drop_quota()
            logger.warning("upload zip rejected", detail=str(exc))
            raise HTTPException(
                status_code=422,
                detail=public_upload_zip_rejected_detail(),
            ) from exc

        if total < held_bytes:
            try:
                ctx.upload_quota_store.release(tenant_key, size_bytes=held_bytes - total, count=0)
            except Exception:  # noqa: BLE001 — keep held_bytes; promote path still compensates
                logger.warning(
                    "upload quota shrink failed",
                    tenant_id=tenant_key,
                    size_bytes=held_bytes - total,
                )
            else:
                held_bytes = total

        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            reject_symlinks(target.parent, base=base)
            quarantine.replace(target)
        except (OSError, PathJailError) as exc:
            quarantine.unlink(missing_ok=True)
            _drop_quota()
            logger.error("upload promote failed", detail=str(exc))
            raise HTTPException(
                status_code=500,
                detail=public_upload_promote_failed_detail(),
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
                _drop_quota()
                logger.error("object store put failed", detail=str(exc))
                raise HTTPException(
                    status_code=500,
                    detail=public_upload_object_store_failed_detail(),
                ) from exc

        ctx.upload_quota_store.clear_hold(tenant_key, upload_id)
        quota = ctx.upload_quota_store.snapshot(tenant_key)
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
