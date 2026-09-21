"""Durable Redis queue for package-analysis requests.

The API is a producer only. A worker uses BRPOPLPUSH so a dequeued request
remains in the processing list until the job reaches a terminal state. Payloads
are JSON (never pickle) and retained across worker OOM/restart until ACK.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from enum import Enum
from pathlib import Path
from typing import Any

from aerobim.domain.models import (
    DrawingSource,
    RequirementSource,
    SourceKind,
    ValidationRequest,
)


class RedisAnalyzeJobQueue:
    def __init__(self, redis_url: str, *, prefix: str = "aerobim:analyze:") -> None:
        try:
            import redis
        except ModuleNotFoundError as exc:
            raise RuntimeError("analyze worker requires the redis package") from exc
        self._redis = redis.Redis.from_url(redis_url, decode_responses=True)
        self._ready = f"{prefix}ready"
        self._processing = f"{prefix}processing"
        self._payload_prefix = f"{prefix}payload:"

    @staticmethod
    def _default(value: object) -> object:
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, Enum):
            return value.value
        raise TypeError(f"Unsupported analyze request value: {type(value).__name__}")

    @classmethod
    def encode_request(cls, request: ValidationRequest) -> str:
        return json.dumps(
            asdict(request),
            default=cls._default,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    @staticmethod
    def _path(value: object) -> Path | None:
        return Path(str(value)) if value not in (None, "") else None

    @classmethod
    def decode_request(cls, raw: str) -> ValidationRequest:
        item: dict[str, Any] = json.loads(raw)
        requirement = dict(item.pop("requirement_source"))
        requirement["path"] = cls._path(requirement.get("path"))
        requirement["source_kind"] = SourceKind(
            requirement.get("source_kind", SourceKind.STRUCTURED_TEXT)
        )
        for name in ("technical_spec_source", "calculation_source"):
            source = item.get(name)
            if source is not None:
                source = dict(source)
                source["path"] = cls._path(source.get("path"))
                source["source_kind"] = SourceKind(
                    source.get("source_kind", SourceKind.STRUCTURED_TEXT)
                )
                item[name] = RequirementSource(**source)
        drawings = []
        for source in item.get("drawing_sources") or ():
            source = dict(source)
            source["path"] = cls._path(source.get("path"))
            drawings.append(DrawingSource(**source))
        item["drawing_sources"] = tuple(drawings)
        for name in (
            "ifc_path",
            "ids_path",
            "reinforcement_report_path",
            "pd_section_path",
            "rd_section_path",
            "signature_envelope_path",
            "package_inventory_path",
        ):
            item[name] = cls._path(item.get(name))
        item["norm_rule_pack_paths"] = tuple(
            Path(str(value)) for value in item.get("norm_rule_pack_paths") or ()
        )
        item["required_signer_roles"] = tuple(item.get("required_signer_roles") or ())
        item["requirement_source"] = RequirementSource(**requirement)
        return ValidationRequest(**item)

    def enqueue(self, job_id: str, request: ValidationRequest) -> bool:
        """Persist payload then publish exactly once; safe for idempotent HTTP replay."""
        key = f"{self._payload_prefix}{job_id}"
        payload = self.encode_request(request)
        script = """
        if redis.call('SET', KEYS[1], ARGV[2], 'NX') then
          redis.call('LPUSH', KEYS[2], ARGV[1])
          return 1
        end
        return 0
        """
        return bool(self._redis.eval(script, 2, key, self._ready, job_id, payload))

    def reserve(self, timeout_seconds: int = 5) -> tuple[str, ValidationRequest] | None:
        job_id = self._redis.brpoplpush(
            self._ready,
            self._processing,
            timeout=max(timeout_seconds, 1),
        )
        if job_id is None:
            return None
        raw = self._redis.get(f"{self._payload_prefix}{job_id}")
        if raw is None:
            self.ack(str(job_id))
            raise RuntimeError(f"queued analyze payload missing for {job_id}")
        return str(job_id), self.decode_request(str(raw))

    def ack(self, job_id: str) -> None:
        with self._redis.pipeline() as pipe:
            pipe.lrem(self._processing, 0, job_id)
            pipe.delete(f"{self._payload_prefix}{job_id}")
            pipe.execute()

    def retry(self, job_id: str) -> None:
        """Move an unacked reservation back to ready without duplicating it."""
        script = """
        if redis.call('LREM', KEYS[1], 1, ARGV[1]) > 0 then
          redis.call('LPUSH', KEYS[2], ARGV[1])
          return 1
        end
        return 0
        """
        self._redis.eval(script, 2, self._processing, self._ready, job_id)

    def recover_processing(self) -> list[str]:
        """Return processing ids; the worker decides using lease state when to retry."""
        return [str(value) for value in self._redis.lrange(self._processing, 0, -1)]
