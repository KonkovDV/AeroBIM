from pathlib import Path

import pytest

from aerobim.domain.models import (
    DrawingSource,
    RequirementSource,
    SourceKind,
    ValidationRequest,
)
from aerobim.infrastructure.adapters.redis_analyze_job_queue import (
    AnalyzeQueuePayloadError,
    RedisAnalyzeJobQueue,
)


class _FakeRedis:
    def __init__(self, reserved: str | None = None, payload: str | None = None) -> None:
        self.reserved = reserved
        self.payload = payload
        self.commands: list[tuple[object, ...]] = []
        self.eval_args: tuple[object, ...] | None = None

    def execute_command(self, *args: object) -> str | None:
        self.commands.append(args)
        return self.reserved

    def get(self, _key: str) -> str | None:
        return self.payload

    def eval(self, *args: object) -> int:
        self.eval_args = args
        return 2


def _queue(fake: _FakeRedis) -> RedisAnalyzeJobQueue:
    queue = object.__new__(RedisAnalyzeJobQueue)
    queue._redis = fake  # type: ignore[attr-defined]
    queue._ready = "aerobim:analyze:ready"  # type: ignore[attr-defined]
    queue._processing = "aerobim:analyze:processing"  # type: ignore[attr-defined]
    queue._payload_prefix = "aerobim:analyze:payload:"  # type: ignore[attr-defined]
    return queue


def test_request_json_round_trip_preserves_paths_enums_and_tuples() -> None:
    request = ValidationRequest(
        request_id="req-queue",
        ifc_path=Path("/data/samples/model.ifc"),
        requirement_source=RequirementSource(
            text="REQ-1|IFCWALL|Pset|Name|x",
            path=Path("/data/samples/requirements.txt"),
            source_kind=SourceKind.STRUCTURED_TEXT,
        ),
        drawing_sources=(
            DrawingSource(
                path=Path("/data/samples/A-101.pdf"),
                sheet_id="A-101",
            ),
        ),
        ids_path=Path("/data/samples/rules.ids"),
        norm_rule_pack_paths=(Path("/data/samples/rules.json"),),
        required_signer_roles=("author", "checker"),
        tenant_id="tenant-a",
    )

    restored = RedisAnalyzeJobQueue.decode_request(RedisAnalyzeJobQueue.encode_request(request))

    assert restored == request
    assert isinstance(restored.ifc_path, Path)
    assert restored.requirement_source.source_kind is SourceKind.STRUCTURED_TEXT


def test_payload_is_json_not_pickle() -> None:
    request = ValidationRequest(
        request_id="req-json",
        ifc_path=None,
        requirement_source=RequirementSource(text="REQ"),
    )
    encoded = RedisAnalyzeJobQueue.encode_request(request)
    assert encoded.startswith("{")
    assert "req-json" in encoded


def test_reserve_uses_blmove_and_attributes_poison_payload() -> None:
    fake = _FakeRedis(reserved="job-poison", payload=None)
    with pytest.raises(AnalyzeQueuePayloadError) as caught:
        _queue(fake).reserve(timeout_seconds=7)
    assert caught.value.job_id == "job-poison"
    assert fake.commands == [
        (
            "BLMOVE",
            "aerobim:analyze:ready",
            "aerobim:analyze:processing",
            "RIGHT",
            "LEFT",
            7,
        )
    ]


def test_enqueue_script_covers_ready_and_processing_for_orphan_repair() -> None:
    fake = _FakeRedis()
    request = ValidationRequest(
        request_id="req-repair",
        ifc_path=None,
        requirement_source=RequirementSource(text="REQ"),
    )
    assert _queue(fake).enqueue("job-repair", request) is True
    assert fake.eval_args is not None
    script, key_count, *_ = fake.eval_args
    assert key_count == 3
    assert "LPOS" in str(script)
    assert "analyze_payload_conflict" in str(script)


@pytest.mark.parametrize("payload", ["null", "[]", '"string"', '{"requirement_source": []}'])
def test_reserve_rejects_non_object_or_malformed_request(payload: str) -> None:
    fake = _FakeRedis(reserved="job-malformed", payload=payload)
    with pytest.raises(AnalyzeQueuePayloadError) as caught:
        _queue(fake).reserve()
    assert caught.value.job_id == "job-malformed"
