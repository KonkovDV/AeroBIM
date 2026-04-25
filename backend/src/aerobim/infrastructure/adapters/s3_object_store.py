from __future__ import annotations


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
    ) -> None:
        self._bucket = bucket
        self._region = region
        self._endpoint_url = endpoint_url
        self._access_key_id = access_key_id
        self._secret_access_key = secret_access_key
        self._prefix = prefix.strip("/")

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
        return response["Body"].read()

    def delete(self, key: str) -> None:
        client = self._build_client()
        client.delete_object(Bucket=self._bucket, Key=self._qualify_key(key))

    def presign_get(self, key: str, *, expires_in_seconds: int = 3600) -> str | None:
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
        return f"{self._prefix}/{normalised}"