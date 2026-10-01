"""Object-store get size caps — streaming OOM protection."""

from __future__ import annotations

DEFAULT_MAX_GET_BYTES = 256 * 1024 * 1024  # aligned with default max IFC
DEFAULT_GET_CHUNK_BYTES = 1 * 1024 * 1024  # 1 MiB
DEFAULT_MAX_HTTP_RESPONSE_BYTES = 1 * 1024 * 1024  # aligned with OpenAI-compat LLM cap


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


def read_http_response_capped(
    response: object,
    *,
    max_bytes: int = DEFAULT_MAX_HTTP_RESPONSE_BYTES,
) -> bytes:
    """Read an HTTP response body with a hard byte cap (RT-EGRESS-001)."""

    read = getattr(response, "read", None)
    if not callable(read):
        raise TypeError("HTTP response does not support read()")
    raw = read(max_bytes + 1)
    if not isinstance(raw, bytes | bytearray):
        raw = bytes(raw)
    if len(raw) > max_bytes:
        raise ObjectTooLargeError(f"HTTP response payload too large (>{max_bytes} bytes)")
    return bytes(raw)


__all__ = [
    "DEFAULT_GET_CHUNK_BYTES",
    "DEFAULT_MAX_GET_BYTES",
    "DEFAULT_MAX_HTTP_RESPONSE_BYTES",
    "ObjectTooLargeError",
    "read_http_response_capped",
    "read_stream_capped",
]
