from __future__ import annotations

from aerobim.core.security.object_limits import (
    DEFAULT_MAX_GET_BYTES,
    ObjectTooLargeError,
    read_stream_capped,
)


class S3ObjectStore:
    def __init__(
        self,
        *,
        bucket: str,
        region: str,
        endpoint_url: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        prefix: str = "aerobim",
        allow_http_endpoint: bool = False,
        max_get_bytes: int = DEFAULT_MAX_GET_BYTES,
    ) -> None:
        if endpoint_url:
            from aerobim.core.security.outbound_url import assert_safe_outbound_url

            assert_safe_outbound_url(
                endpoint_url,
                allow_http=allow_http_endpoint,
                resolve_dns=True,
            )
        self._bucket = bucket
        self._region = region
        self._endpoint_url = endpoint_url
        self._access_key_id = access_key_id
        self._secret_access_key = secret_access_key
        self._prefix = prefix.strip("/")
        self._allow_http_endpoint = allow_http_endpoint
        self._max_get_bytes = max_get_bytes

    def put_bytes(
        self,
        key: str,
        payload: bytes,
        *,
        content_type: str | None = None,
    ) -> str:
        client = self._build_client()
        object_key = self._qualify_key(key)
        kwargs: dict[str, object] = {
            "Bucket": self._bucket,
            "Key": object_key,
            "Body": payload,
        }
        if content_type:
            kwargs["ContentType"] = content_type
        client.put_object(**kwargs)
        return object_key

    def get_bytes(self, key: str) -> bytes | None:
        client = self._build_client()
        object_key = self._qualify_key(key)
        try:
            response = client.get_object(Bucket=self._bucket, Key=object_key)
        except client.exceptions.NoSuchKey:
            return None
        content_length = response.get("ContentLength")
        length: int | None = None
        if content_length is not None:
            try:
                length = int(content_length)
            except (TypeError, ValueError):
                length = None
            if length is not None and length > self._max_get_bytes:
                raise ObjectTooLargeError(
                    f"Object ContentLength too large ({length} > {self._max_get_bytes})"
                )
        return read_stream_capped(
            response["Body"],
            max_bytes=self._max_get_bytes,
            content_length=length,
        )

    def delete(self, key: str) -> None:
        client = self._build_client()
        client.delete_object(Bucket=self._bucket, Key=self._qualify_key(key))

    def presign_get(self, key: str, *, expires_in_seconds: int = 3600) -> str | None:
        # Residual: presigned GET bypasses this store's max_get_bytes streaming cap;
        # callers that fetch via URL must enforce their own size limits.
        client = self._build_client()
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": self._qualify_key(key)},
            ExpiresIn=expires_in_seconds,
        )

    def _build_client(self):
        try:
            import boto3  # type: ignore[import-not-found]
            from botocore.config import Config  # type: ignore[import-not-found]
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "S3ObjectStore requires boto3/botocore. Install AeroBIM enterprise extras."
            ) from exc

        # Re-assert DNS pin at connect time so a stale boot-time check cannot
        # survive a rebind. Residual: boto3 still dials the hostname (Host/SNI);
        # full IP dial requires a custom endpoint resolver.
        if self._endpoint_url:
            from aerobim.core.security.outbound_url import assert_safe_outbound_url

            assert_safe_outbound_url(
                self._endpoint_url,
                allow_http=self._allow_http_endpoint,
                resolve_dns=True,
            )

        return boto3.client(
            "s3",
            region_name=self._region,
            endpoint_url=self._endpoint_url,
            aws_access_key_id=self._access_key_id,
            aws_secret_access_key=self._secret_access_key,
            config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
        )

    def _qualify_key(self, key: str) -> str:
        normalised = key.strip().replace("\\", "/").lstrip("/")
        if not self._prefix:
            return normalised
        if normalised == self._prefix or normalised.startswith(f"{self._prefix}/"):
            return normalised
        return f"{self._prefix}/{normalised}"


__all__ = ["ObjectTooLargeError", "S3ObjectStore"]
