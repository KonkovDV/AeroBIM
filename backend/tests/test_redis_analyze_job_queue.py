from pathlib import Path

from aerobim.domain.models import (
    DrawingSource,
    RequirementSource,
    SourceKind,
    ValidationRequest,
)
from aerobim.infrastructure.adapters.redis_analyze_job_queue import (
    RedisAnalyzeJobQueue,
)


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

    restored = RedisAnalyzeJobQueue.decode_request(
        RedisAnalyzeJobQueue.encode_request(request)
    )

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
