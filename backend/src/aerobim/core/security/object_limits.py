"""Object-store get size caps — streaming OOM protection."""

from __future__ import annotations

DEFAULT_MAX_GET_BYTES = 256 * 1024 * 1024  # aligned with default max IFC
DEFAULT_GET_CHUNK_BYTES = 1 * 1024 * 1024  # 1 MiB


class ObjectTooLargeError(ValueError):
    """Raised when an object-store get exceeds the configured byte cap."""


def read_stream_capped(
    body: object,
    *,
    max_bytes: int,
    chunk_size: int = DEFAULT_GET_CHUNK_BYTES,
    content_length: int | None = None,
) -> bytes:
    """Read a StreamingBody-like object in chunks, aborting over ``max_bytes``."""

    if content_length is not None and content_length > max_bytes:
        raise ObjectTooLargeError(
            f"Object ContentLength too large ({content_length} > {max_bytes})"
        )
    read = getattr(body, "read", None)
    if not callable(read):
        raise TypeError("Object body does not support read()")
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = read(chunk_size)
        if not chunk:
            break
        if not isinstance(chunk, bytes | bytearray):
            chunk = bytes(chunk)
        total += len(chunk)
        if total > max_bytes:
            raise ObjectTooLargeError(f"Object payload too large (>{max_bytes} bytes)")
        chunks.append(bytes(chunk))
    return b"".join(chunks)


__all__ = [
    "DEFAULT_GET_CHUNK_BYTES",
    "DEFAULT_MAX_GET_BYTES",
    "ObjectTooLargeError",
    "read_stream_capped",
]
