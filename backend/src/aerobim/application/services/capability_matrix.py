"""Honest report-capability matrix assembly (extracted from AnalyzeProjectPackageUseCase).

Pure function of contour results + configuration flags; never defaults a
capability to OK without an explicit probe (RT-POST-06).
"""

from __future__ import annotations

from collections.abc import Sequence

from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    DrawingSource,
    ParsedRequirement,
    ReportCapabilities,
    ValidationIssue,
)

RASTER_DRAWING_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}
RASTER_DRAWING_FORMATS = {"pdf", "png", "jpg", "jpeg", "webp", "image", "raster"}


def build_report_capabilities(
    *,
    requirements: Sequence[ParsedRequirement],
    ifc_issues: Sequence[ValidationIssue],
    ids_path,
    ids_issues: Sequence[ValidationIssue],
    clash_capability: CapabilityStatus,
    drawing_sources: Sequence[DrawingSource],
    drawing_annotation_count: int = 0,
    schema_issues: Sequence[ValidationIssue] = (),
    ids_audit_issues: Sequence[ValidationIssue] = (),
    schema_request_id: str | None = None,
    norm_rule_packs: CapabilityStatus | None = None,
    section_pairing: CapabilityStatus | None = None,
    dwg_dxf: CapabilityStatus | None = None,
    mep_system_clash: CapabilityStatus | None = None,
    calculation_match: CapabilityStatus | None = None,
    quantity_capability: CapabilityStatus | None = None,
    ids_validator_configured: bool,
    ifc_schema_validator_configured: bool,
    require_bsi_schema: bool,
    raster_analyzer_configured: bool,
) -> ReportCapabilities:
    ifc_validation = (
        CapabilityStatus(CapabilityState.OK)
        if requirements
        else CapabilityStatus(CapabilityState.SKIPPED, "no IFC property requirements")
    )
    quantity = quantity_capability or CapabilityStatus(
        CapabilityState.SKIPPED, "quantity consistency not evaluated"
    )
    if quantity_capability is not None and quantity_capability.status is CapabilityState.FAILED:
        ifc_validation = quantity_capability
    # RT-POST-06: never default unit_scale to OK without an explicit probe.
    unit_scale = CapabilityStatus(
        CapabilityState.NOT_VERIFIED,
        "IFC unit scale not probed",
    )
    for issue in ifc_issues:
        if issue.rule_id == "AEROBIM-UNIT-SCALE":
            unit_scale = CapabilityStatus(
                CapabilityState.FAILED,
                issue.message,
            )
            break
        if issue.rule_id == "AEROBIM-UNIT-SCALE-OK":
            unit_scale = CapabilityStatus(CapabilityState.OK, issue.message)
            break

    if ids_path is None:
        ids_capability = CapabilityStatus(CapabilityState.SKIPPED, "IDS validation not requested")
    elif not ids_validator_configured:
        ids_capability = CapabilityStatus(
            CapabilityState.FAILED, "IDS validation requested but no validator configured"
        )
    elif ids_audit_issues:
        ids_capability = CapabilityStatus(
            CapabilityState.FAILED,
            ids_audit_issues[0].message if ids_audit_issues else "IDS audit failed",
        )
    elif any(issue.rule_id == "AEROBIM-IDS-ERROR" for issue in ids_issues):
        ids_error = next(issue for issue in ids_issues if issue.rule_id == "AEROBIM-IDS-ERROR")
        ids_capability = CapabilityStatus(CapabilityState.FAILED, ids_error.message)
    else:
        ids_capability = CapabilityStatus(CapabilityState.OK)

    if not ifc_schema_validator_configured and schema_request_id is None:
        if require_bsi_schema:
            ifc_schema = CapabilityStatus(
                CapabilityState.FAILED,
                "IFC schema pre-gate required but not configured",
            )
        else:
            ifc_schema = CapabilityStatus(
                CapabilityState.SKIPPED, "IFC schema pre-gate not configured"
            )
    elif schema_issues:
        ifc_schema = CapabilityStatus(
            CapabilityState.FAILED,
            schema_issues[0].message if schema_issues else "schema pre-gate failed",
            external_ref=schema_request_id,
        )
    elif require_bsi_schema:
        # Submit ACK / local cert id must never green-pass required schema.
        if schema_request_id is None:
            ifc_schema = CapabilityStatus(
                CapabilityState.NOT_VERIFIED,
                "IFC schema required: SPF pre-gate only; bSI/schema certificate not obtained",
            )
        else:
            ifc_schema = CapabilityStatus(
                CapabilityState.NOT_VERIFIED,
                ("IFC schema required: bSI/schema submit ACK only; validation result not verified"),
                external_ref=schema_request_id,
            )
    else:
        ifc_schema = CapabilityStatus(
            CapabilityState.NOT_VERIFIED,
            external_ref=schema_request_id,
            reason=(
                "SPF FILE_SCHEMA pre-gate only (not full EXPRESS / bSI)"
                if not schema_request_id
                else "SPF / submit ACK only (not full EXPRESS / bSI)"
            ),
        )

    raster_requested = any(
        (source.path and source.path.suffix.lower() in RASTER_DRAWING_SUFFIXES)
        or (source.format or "").strip().lower() in RASTER_DRAWING_FORMATS
        for source in drawing_sources
    )
    if not raster_requested:
        raster_capability = CapabilityStatus(CapabilityState.SKIPPED, "no raster drawing sources")
    elif not raster_analyzer_configured:
        raster_capability = CapabilityStatus(
            CapabilityState.FAILED,
            "raster drawing analysis requested but analyzer not configured",
        )
    elif drawing_annotation_count <= 0:
        # Requested OCR path with zero yield must not look like a clean OK.
        raster_capability = CapabilityStatus(
            CapabilityState.FAILED,
            "raster drawing analysis produced zero annotations",
        )
    else:
        raster_capability = CapabilityStatus(CapabilityState.OK)

    return ReportCapabilities(
        clash=clash_capability,
        ids=ids_capability,
        ifc_validation=ifc_validation,
        unit_scale=unit_scale,
        raster=raster_capability,
        ifc_schema=ifc_schema,
        norm_rule_packs=norm_rule_packs
        or CapabilityStatus(CapabilityState.SKIPPED, "norm rule packs not requested"),
        section_pairing=section_pairing
        or CapabilityStatus(CapabilityState.SKIPPED, "PD/RD section pairing not requested"),
        dwg_dxf=dwg_dxf
        or CapabilityStatus(CapabilityState.MISSING, "DWG/DXF native analysis not implemented"),
        mep_system_clash=mep_system_clash
        or CapabilityStatus(
            CapabilityState.NOT_VERIFIED,
            "MEP system graph provider DI-wired but unconfigured (MEP-CLASH-001); "
            "federated MEP IFC + scope memo required",
        ),
        calculation_match=calculation_match
        or CapabilityStatus(CapabilityState.SKIPPED, "numeric calculation match not evaluated"),
        quantity=quantity,
    )
