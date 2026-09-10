"""Run passport: submitted sources, format rows, stage timings. Not an SLA."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Final, Literal

from aerobim.domain.checkpoint import CHECKPOINT, CUSTOMER_GO

CLAIM_BOUNDARY: Final = (
    "Timing and format rows for this run on this machine. "
    "Not a customer SLA. Not TZ ≤30 min. Checkpoint GO; customer_go false."
)

PASSPORT_STAGES: Final[tuple[str, ...]] = (
    "ingest",
    "ifc",
    "ids",
    "drawing",
    "cross-doc",
    "clash",
    "report",
)

FormatDisposition = Literal["read", "rejected", "not_submitted"]

OFFICE_CAP_BYTES: Final = 500 * 1024 * 1024
CUSTOMER_MODEL_CAP_BYTES: Final = int(1.5 * 1024 * 1024 * 1024)
SPF_CAP_BYTES: Final = 256 * 1024 * 1024

_NATIVE_CLOSED: Final[frozenset[str]] = frozenset({".rvt", ".rte", ".nwd", ".nwc", ".lir", ".spr"})
_NATIVE_REASON: Final = (
    "closed format without a free reader; native RVT/NWD/LIRA parser is not implemented"
)
_SIZE_REASON: Final = "exceeds size limit"
_READ_SUFFIXES: Final[frozenset[str]] = frozenset(
    {
        ".ifc",
        ".ifczip",
        ".ids",
        ".xml",
        ".pdf",
        ".docx",
        ".xlsx",
        ".json",
        ".txt",
        ".png",
        ".jpg",
        ".jpeg",
    }
)


def classify_submitted_source(
    *,
    name: str,
    size_bytes: int | None = None,
    disposition: FormatDisposition | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """One passport/format-coverage row for a submitted file."""

    suffix = Path(name.replace("\\", "/").split("/")[-1]).suffix.lower()
    if disposition is None:
        if suffix in _NATIVE_CLOSED:
            disposition = "rejected"
            reason = reason or _NATIVE_REASON
        elif (
            size_bytes is not None and suffix in {".ifc", ".ifczip"} and size_bytes > SPF_CAP_BYTES
        ):
            disposition = "rejected"
            reason = reason or (
                f"{_SIZE_REASON} (SPF cap {SPF_CAP_BYTES} bytes; "
                f"customer model cap {CUSTOMER_MODEL_CAP_BYTES})"
            )
        elif (
            size_bytes is not None
            and suffix in {".docx", ".xlsx"}
            and size_bytes > OFFICE_CAP_BYTES
        ):
            disposition = "rejected"
            reason = reason or f"{_SIZE_REASON} (office cap {OFFICE_CAP_BYTES} bytes)"
        elif suffix in _READ_SUFFIXES:
            disposition = "read"
            reason = reason or "read"
        else:
            disposition = "rejected"
            reason = reason or "format not supported"
    return {
        "name_class": suffix or "unknown",
        "suffix": suffix,
        "size_bytes": size_bytes,
        "disposition": disposition,
        "reason": reason,
        "office_cap_bytes": OFFICE_CAP_BYTES,
        "customer_model_cap_bytes": CUSTOMER_MODEL_CAP_BYTES,
        "spf_cap_bytes": SPF_CAP_BYTES,
    }


def format_coverage_table(sources: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    rows = [classify_submitted_source(**_source_kwargs(item)) for item in sources]
    submitted = len(rows)
    read = sum(1 for row in rows if row["disposition"] == "read")
    rejected = sum(1 for row in rows if row["disposition"] == "rejected")
    return {
        "artifact_type": "format_coverage",
        "claim_boundary": CLAIM_BOUNDARY,
        "is_sla": False,
        "submitted": submitted,
        "read": read,
        "rejected": rejected,
        "rows": rows,
    }


def _source_kwargs(item: Mapping[str, Any]) -> dict[str, Any]:
    name = str(item.get("name") or item.get("path") or item.get("filename") or "")
    size = item.get("size_bytes")
    size_i = int(size) if isinstance(size, (int, float)) else None
    disposition = item.get("disposition")
    reason = str(item["reason"]) if item.get("reason") else None
    disp: FormatDisposition | None
    if disposition in {"read", "rejected", "not_submitted"}:
        disp = disposition
    else:
        disp = None
    return {"name": name, "size_bytes": size_i, "disposition": disp, "reason": reason}


def build_run_passport(
    *,
    sources: Sequence[Mapping[str, Any]] = (),
    stage_timings_ms: Mapping[str, int] | None = None,
    git_sha: str = "",
    rules_version: str = "",
    report_id: str | None = None,
    timing_basis: str = "sources_only",
) -> dict[str, Any]:
    timings = dict(stage_timings_ms or {})
    stages = []
    cumulative = 0
    for name in PASSPORT_STAGES:
        ms = int(timings.get(name, 0))
        cumulative += ms
        stages.append({"name": name, "duration_ms": ms, "cumulative_ms": cumulative})
    coverage = format_coverage_table(sources)
    basis = (timing_basis or "sources_only").strip() or "sources_only"
    return {
        "schema_version": "1.0.0",
        "artifact_type": "run_passport",
        "report_id": report_id,
        "git_sha": git_sha,
        "rules_version": rules_version,
        "checkpoint": CHECKPOINT,
        "customer_go": CUSTOMER_GO,
        "is_sla": False,
        "stage_timing_basis": basis,
        "claim_boundary": CLAIM_BOUNDARY,
        "disclaimer": (
            "замер на этом прогоне и этой машине; не SLA, не гарантия времени "
            "на комплекте заказчика"
        ),
        "stages": stages,
        "format_coverage": coverage,
    }


def sources_from_report(report: Any) -> list[dict[str, Any]]:
    """Best-effort source list for a persisted report (no customer filenames required)."""

    items: list[dict[str, Any]] = []
    ifc_path = getattr(report, "ifc_path", None)
    if ifc_path is not None:
        name = Path(str(ifc_path)).name or "model.ifc"
        size = None
        try:
            path = Path(ifc_path)
            if path.is_file():
                size = path.stat().st_size
        except OSError:
            size = None
        items.append({"name": name, "size_bytes": size})
        if size is not None and size > SPF_CAP_BYTES:
            items[-1]["disposition"] = "read"
            items[-1]["reason"] = "opened on disk (RocksDB); over SPF RAM cap; not a silent skip"
    for asset in getattr(report, "drawing_assets", ()) or ():
        filename = (
            getattr(asset, "stored_filename", None)
            or getattr(asset, "sheet_id", None)
            or "drawing.bin"
        )
        items.append({"name": str(filename)})
    return items


PASSPORT_TRACE_TOOL: Final = "run_passport"


def passport_trace(passport: Mapping[str, Any]) -> dict[str, Any]:
    """Persist the run passport on the report without touching summary.passed."""

    return {
        "tool": PASSPORT_TRACE_TOOL,
        "status": "ok",
        "verdict_impact": "none",
        "passport": dict(passport),
    }


def passport_from_traces(traces: Sequence[Any] | None) -> dict[str, Any] | None:
    """Last ``run_passport`` trace wins. Missing traces → caller rebuilds sources-only."""

    if not traces:
        return None
    found: dict[str, Any] | None = None
    for item in traces:
        if not isinstance(item, Mapping):
            continue
        if item.get("tool") != PASSPORT_TRACE_TOOL:
            continue
        payload = item.get("passport")
        if isinstance(payload, Mapping) and payload.get("artifact_type") == "run_passport":
            found = dict(payload)
    return found


def stages_are_monotonic(passport: Mapping[str, Any]) -> bool:
    previous = -1
    for stage in passport.get("stages") or ():
        if not isinstance(stage, Mapping):
            return False
        cumulative = int(stage.get("cumulative_ms") or 0)
        if cumulative < previous:
            return False
        previous = cumulative
    return True
