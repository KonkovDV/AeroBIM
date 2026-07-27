"""Package ingestion contour services (extracted from AnalyzeProjectPackageUseCase).

Owns document hydration, drawing/CAD/raster annotation collection, narrative
rule synthesis and norm-pack loading. Honesty semantics preserved: unsupported
DWG never masked by DXF success, configured-but-missing packs fail closed.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

from aerobim.application.services.capability_matrix import (
    RASTER_DRAWING_FORMATS,
    RASTER_DRAWING_SUFFIXES,
)
from aerobim.domain.derived_cad_provenance import (
    find_derived_provenance_sidecar,
    verify_derived_provenance_sidecar,
)
from aerobim.domain.ingestion import stamp_requirement_source
from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    DrawingAnnotation,
    DrawingAsset,
    DrawingRegionRef,
    DrawingSource,
    FindingCategory,
    ParsedRequirement,
    RequirementSource,
    RulePackStatus,
    Severity,
    SourceKind,
    ValidationIssue,
    ValidationRequest,
)
from aerobim.domain.ports import (
    CadModelIngestor,
    DrawingAnalyzer,
    MultimodalDrawingPipeline,
    NarrativeRuleSynthesizer,
    NormRulePackLoader,
    OfficeDocumentIngestor,
    RasterDrawingAnalyzer,
)

CAD_DRAWING_SUFFIXES = {".dxf", ".dwg"}
DRAWING_ASSET_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}
OFFICE_SUFFIXES = {".docx", ".xlsx", ".pptx", ".doc", ".xls", ".odt", ".ods"}

_logger = logging.getLogger("aerobim.analyze")


class PackageIngestionService:
    """INGESTION contour collectors, parameterized by the injected ports."""

    def __init__(
        self,
        *,
        drawing_analyzer: DrawingAnalyzer,
        narrative_rule_synthesizer: NarrativeRuleSynthesizer,
        raster_drawing_analyzer: RasterDrawingAnalyzer | None = None,
        multimodal_drawing_pipeline: MultimodalDrawingPipeline | None = None,
        cad_model_ingestor: CadModelIngestor | None = None,
        office_document_ingestor: OfficeDocumentIngestor | None = None,
        norm_rule_pack_loader: NormRulePackLoader | None = None,
        default_norm_rule_pack_path: Path | None = None,
    ) -> None:
        self._drawing_analyzer = drawing_analyzer
        self._narrative_rule_synthesizer = narrative_rule_synthesizer
        self._raster_drawing_analyzer = raster_drawing_analyzer
        self._multimodal_drawing_pipeline = multimodal_drawing_pipeline
        self._cad_model_ingestor = cad_model_ingestor
        self._office_document_ingestor = office_document_ingestor
        self._norm_rule_pack_loader = norm_rule_pack_loader
        self._default_norm_rule_pack_path = default_norm_rule_pack_path

    def maybe_hydrate_office_requirement_source(
        self, request: ValidationRequest
    ) -> ValidationRequest:
        source = request.requirement_source
        if source.text.strip() or source.path is None or self._office_document_ingestor is None:
            return request
        if source.path.suffix.lower() not in OFFICE_SUFFIXES:
            return request
        hydrated = self._office_document_ingestor.ingest(source.path)
        return replace(
            request,
            requirement_source=replace(
                source,
                text=hydrated.text,
                source_kind=hydrated.source_kind,
                doc_type=hydrated.doc_type or source.doc_type,
            ),
        )

    def run_cad_ingest(
        self, request: ValidationRequest
    ) -> tuple[tuple[DrawingAnnotation, ...], CapabilityStatus, list[ValidationIssue]]:
        cad_sources = [
            source
            for source in request.drawing_sources
            if source.path is not None
            and (
                source.path.suffix.lower() in CAD_DRAWING_SUFFIXES
                or (source.format or "").strip().lower() in {"dxf", "dwg", "cad"}
            )
        ]
        if not cad_sources:
            return (
                (),
                CapabilityStatus(CapabilityState.MISSING, "native DWG parser is not implemented"),
                [],
            )
        if self._cad_model_ingestor is None:
            return (
                (),
                CapabilityStatus(
                    CapabilityState.FAILED,
                    "CAD sources present but CadModelIngestor not configured",
                ),
                [
                    ValidationIssue(
                        rule_id="AEROBIM-CAD-INGEST",
                        severity=Severity.WARNING,
                        message=(
                            "CAD drawing sources present but CadModelIngestor is not configured"
                        ),
                        category=FindingCategory.DRAWING_VALIDATION,
                        source_id="cad-ingest",
                    )
                ],
            )

        annotations: list[DrawingAnnotation] = []
        issues: list[ValidationIssue] = []
        saw_dwg = False
        saw_supported_dxf = False
        saw_verified_derived_dwg = False
        all_dwg_supported = True
        last_reason: str | None = None
        last_dwg_reason: str | None = None
        for source in cad_sources:
            assert source.path is not None
            is_dwg = source.path.suffix.lower() == ".dwg" or (
                (source.format or "").strip().lower() == "dwg"
            )
            if is_dwg:
                saw_dwg = True
            result = self._cad_model_ingestor.ingest(source.path, sheet_id=source.sheet_id)
            last_reason = result.reason
            if result.supported:
                if result.format_resolved == "dwg":
                    pass
                else:
                    saw_supported_dxf = True
                annotations.extend(result.annotations)
            elif is_dwg or result.format_resolved == "dwg":
                # DWG conversion MVP: an explicitly declared + hash-verified derived
                # substitute registers the pair instead of failing the package.
                # Declared-but-unverifiable provenance is worse than none (fail-closed).
                verified, derived_issues = self._assess_dwg_derived_route(source.path)
                issues.extend(derived_issues)
                if verified:
                    saw_verified_derived_dwg = True
                    continue
                all_dwg_supported = False
                derived_warning = next(
                    (issue for issue in derived_issues if issue.severity is Severity.WARNING),
                    None,
                )
                last_dwg_reason = (
                    derived_warning.message if derived_warning is not None else result.reason
                )
                if derived_warning is None:
                    issues.append(
                        ValidationIssue(
                            rule_id="AEROBIM-CAD-DWG",
                            severity=Severity.WARNING,
                            message=result.reason or "Native DWG ingest not configured",
                            category=FindingCategory.DRAWING_VALIDATION,
                            source_id=source.path.name if source.path is not None else "cad",
                        )
                    )
            else:
                issues.append(
                    ValidationIssue(
                        rule_id="AEROBIM-CAD-DXF",
                        severity=Severity.WARNING,
                        message=result.reason or "DXF ingest failed",
                        category=FindingCategory.DRAWING_VALIDATION,
                        source_id=source.path.name if source.path is not None else "cad",
                    )
                )

        if saw_dwg and not all_dwg_supported:
            # RT-D: unparsed DWG must not be masked by a successful sibling DXF.
            capability = CapabilityStatus(
                CapabilityState.FAILED,
                last_dwg_reason
                or last_reason
                or "Package contains unsupported/unparsed DWG; DXF success does not clear DWG",
            )
        elif saw_verified_derived_dwg:
            # Derived route: hash-verified substitute pair registered — never OK
            # (analysis refers to the derived file, not the native DWG).
            capability = CapabilityStatus(
                CapabilityState.NOT_VERIFIED,
                "DWG via hash-verified derived substitute (source_dwg_sha256↔derived_sha256); "
                "native DWG not parsed",
            )
        elif saw_supported_dxf:
            # Partial delivery: DXF only — never OK until ODA DWG evidenced.
            capability = CapabilityStatus(
                CapabilityState.NOT_VERIFIED,
                "DXF ingest via CadModelIngestor (ezdxf); native DWG not verified",
            )
        else:
            capability = CapabilityStatus(
                CapabilityState.FAILED,
                last_reason or "CAD ingest produced no supported parse",
            )
        return tuple(annotations), capability, issues

    def _assess_dwg_derived_route(self, dwg_path: Path) -> tuple[bool, tuple[ValidationIssue, ...]]:
        """Check the DWG sidecar (``*.derived-provenance.json``) for a verified pair.

        Returns ``(verified, issues)``. No sidecar → ``(False, ())`` — caller keeps
        the legacy unsupported-DWG path. Verified sidecar → INFO registration issue
        (+ WARNING when recomputed conversion QA reports losses). Failing sidecar
        or failed QA → WARNING with mismatches (worse than absent: fail-closed).
        """

        sidecar = find_derived_provenance_sidecar(dwg_path)
        if sidecar is None:
            return False, ()
        verification = verify_derived_provenance_sidecar(sidecar)
        if not verification.verified:
            return False, (
                ValidationIssue(
                    rule_id="AEROBIM-CAD-DWG-DERIVED",
                    severity=Severity.WARNING,
                    message=(
                        "DWG derived-provenance sidecar failed hash verification: "
                        + "; ".join(verification.mismatches)
                    ),
                    category=FindingCategory.DRAWING_VALIDATION,
                    source_id=dwg_path.name,
                    evidence_refs=(f"sidecar:{sidecar.name}",),
                ),
            )
        provenance = verification.provenance
        assert provenance is not None
        registration = ValidationIssue(
            rule_id="AEROBIM-CAD-DWG-DERIVED",
            severity=Severity.INFO,
            message=(
                "Analysis refers to the derived file "
                f"{provenance.derived_format}:{(provenance.derived_sha256 or '')[:12]} "
                f"converted from DWG sha256:{(provenance.source_dwg_sha256 or '')[:12]} "
                f"via {provenance.conversion_tool or 'undeclared tool'}; "
                "native DWG is not parsed"
            ),
            category=FindingCategory.DRAWING_VALIDATION,
            source_id=dwg_path.name,
            evidence_refs=(
                f"sidecar:{sidecar.name}",
                f"source_dwg_sha256:{provenance.source_dwg_sha256}",
                f"derived_sha256:{provenance.derived_sha256}",
            ),
        )
        qa = verification.conversion_qa
        if qa is not None and qa.status == "warning":
            # Loss within the agreed policy: route stays, expert sees the diff.
            return True, (
                registration,
                ValidationIssue(
                    rule_id="AEROBIM-CAD-DWG-QA",
                    severity=Severity.WARNING,
                    message="DWG conversion loss report: " + "; ".join(qa.reasons),
                    category=FindingCategory.DRAWING_VALIDATION,
                    source_id=dwg_path.name,
                    evidence_refs=(f"sidecar:{sidecar.name}",),
                ),
            )
        return True, (registration,)

    def collect_norm_pack_requirements(
        self,
        request: ValidationRequest,
    ) -> tuple[list[ParsedRequirement], CapabilityStatus]:
        # Precedence: explicit request/manifest paths win; otherwise fall back to
        # the operator-configured env default (AEROBIM_NORM_RULE_PACK). Nothing is
        # hardcoded, and a configured-but-missing default fails closed.
        if request.norm_rule_pack_paths:
            return self.load_norm_packs(
                request.norm_rule_pack_paths, source="request manifest", tolerant=False
            )
        if self._default_norm_rule_pack_path is not None:
            return self.load_norm_packs(
                (self._default_norm_rule_pack_path,),
                source="env AEROBIM_NORM_RULE_PACK",
                tolerant=True,
            )
        return [], CapabilityStatus(CapabilityState.SKIPPED, "norm rule packs not requested")

    def load_norm_packs(
        self,
        pack_paths: Sequence[Path],
        *,
        source: str,
        tolerant: bool,
    ) -> tuple[list[ParsedRequirement], CapabilityStatus]:
        if self._norm_rule_pack_loader is None:
            raise RuntimeError("Norm rule packs requested but no loader is configured")

        requirements: list[ParsedRequirement] = []
        pack_refs: list[str] = []
        non_approved = False
        seen_packs: set[tuple[str, str]] = set()
        for pack_path in pack_paths:
            try:
                pack = self._norm_rule_pack_loader.load(pack_path)
            except (FileNotFoundError, ValueError, OSError) as exc:
                # Requested or configured packs that fail to load must never look
                # like a clean skip/pass: surface FAILED capability (fail-closed).
                return [], CapabilityStatus(
                    CapabilityState.FAILED,
                    f"norm rule pack unavailable via {source}: {pack_path.name}: {exc}",
                )
            identity = (pack.pack_id, pack.version)
            if identity in seen_packs:
                raise ValueError(
                    f"Duplicate norm rule pack requested: {pack.pack_id}@{pack.version}"
                )
            seen_packs.add(identity)
            requirements.extend(pack.rules)
            if pack.status is not RulePackStatus.APPROVED or pack.advisory_only:
                non_approved = True
            pack_refs.append(
                f"{pack.pack_id}@{pack.version}[{pack.status.value}] sha256:{pack.sha256[:12]}"
            )
        # Ensure every norm-pack rule carries a pack-manifest approval badge.
        stamped: list[ParsedRequirement] = []
        for requirement in requirements:
            if requirement.approval_status is None:
                stamped.append(replace(requirement, approval_status="synthetic"))
            elif non_approved and requirement.approval_status == "customer_approved":
                # Draft/synthetic load path cannot surface customer_approved badges.
                stamped.append(replace(requirement, approval_status="synthetic"))
            else:
                stamped.append(requirement)
        requirements = stamped
        reason = f"loaded {len(pack_refs)} rule pack(s) via {source}: {', '.join(pack_refs)}"
        if non_approved:
            reason += (
                "; advisory: non-approved/draft pack(s) — not for deterministic sign-off "
                "(RT-002 open; customer_approved capability not granted)"
            )
        return requirements, CapabilityStatus(CapabilityState.OK, reason)

    def collect_synthesized_requirements(
        self, request: ValidationRequest
    ) -> list[ParsedRequirement]:
        synthesized: list[ParsedRequirement] = []
        for source in (request.technical_spec_source, request.calculation_source):
            if source is None:
                continue
            if not source.text.strip() and source.path is None:
                continue
            synthesized.extend(self._narrative_rule_synthesizer.synthesize(source))
        return synthesized

    def collect_drawing_annotations(
        self, request: ValidationRequest
    ) -> tuple[list[DrawingAnnotation], list[DrawingRegionRef], int]:
        annotations: list[DrawingAnnotation] = []
        regions: list[DrawingRegionRef] = []
        raster_yield = 0
        for drawing_source in request.drawing_sources:
            if self.has_structured_drawing_input(drawing_source):
                annotations.extend(self._drawing_analyzer.analyze(drawing_source))
            if self.is_raster_drawing_source(drawing_source):
                before = len(annotations)
                if self._multimodal_drawing_pipeline is not None:
                    result = self._multimodal_drawing_pipeline.analyze(drawing_source, mode="auto")
                    annotations.extend(result.annotations)
                    regions.extend(result.regions)
                elif self._raster_drawing_analyzer is not None:
                    annotations.extend(self.collect_raster_annotations(drawing_source))
                # else: requested raster without analyzer → empty yield; FAILED in capabilities
                raster_yield += len(annotations) - before
        return annotations, regions, raster_yield

    def collect_drawing_assets(self, request: ValidationRequest) -> list[DrawingAsset]:
        assets: list[DrawingAsset] = []
        for index, drawing_source in enumerate(request.drawing_sources, start=1):
            if drawing_source.path is None:
                continue
            suffix = drawing_source.path.suffix.lower()
            if suffix not in DRAWING_ASSET_SUFFIXES:
                continue
            assets.append(
                DrawingAsset(
                    asset_id=f"drawing-{index:03d}",
                    sheet_id=drawing_source.sheet_id or drawing_source.path.stem.upper(),
                    page_number=1 if suffix != ".pdf" else None,
                    media_type=(
                        "application/pdf"
                        if suffix == ".pdf"
                        else "image/webp"
                        if suffix == ".webp"
                        else "image/jpeg"
                        if suffix in {".jpg", ".jpeg"}
                        else "image/png"
                    ),
                    source_path=drawing_source.path,
                )
            )
        return assets

    def collect_raster_annotations(
        self,
        drawing_source: DrawingSource,
    ) -> list[DrawingAnnotation]:
        if drawing_source.path is None:
            raise ValueError("Raster drawing analysis requires a drawing file path")
        if self._raster_drawing_analyzer is None:
            raise RuntimeError(
                "Raster drawing analysis requested but no raster drawing analyzer is configured"
            )
        try:
            return list(
                self._raster_drawing_analyzer.analyze_image(
                    drawing_source.path,
                    sheet_id=drawing_source.sheet_id,
                )
            )
        except Exception as exc:  # noqa: BLE001 — empty/unreadable PDF must not crash
            _logger.exception("Raster drawing analysis failed for %s", drawing_source.path)
            # Zero yield → capabilities.raster FAILED (not silent OK / PASS).
            _ = exc
            return []

    def has_structured_drawing_input(self, drawing_source: DrawingSource) -> bool:
        if drawing_source.text.strip():
            return True
        if drawing_source.path is None:
            return False
        suffix = drawing_source.path.suffix.lower()
        if suffix in RASTER_DRAWING_SUFFIXES or suffix in CAD_DRAWING_SUFFIXES:
            return False
        return True

    def is_raster_drawing_source(self, drawing_source: DrawingSource) -> bool:
        if drawing_source.format and drawing_source.format.lower() in RASTER_DRAWING_FORMATS:
            return True
        if drawing_source.path is None:
            return False
        return drawing_source.path.suffix.lower() in RASTER_DRAWING_SUFFIXES

    def collect_identity_sources(self, request: ValidationRequest) -> list[RequirementSource]:
        """Stamp package-level identity onto requirement and drawing sources."""

        sources: list[RequirementSource] = []
        doc_status = request.doc_status
        status_value = doc_status if isinstance(doc_status, str) else None
        for source in (
            request.requirement_source,
            request.technical_spec_source,
            request.calculation_source,
        ):
            if source is None:
                continue
            sources.append(
                stamp_requirement_source(
                    source,
                    revision=source.revision or request.revision,
                    stage=source.stage or request.stage,
                    doc_type=source.doc_type or source.source_kind.value,
                    doc_status=source.doc_status or status_value,
                    source_id=source.source_id or source.source_kind.value,
                )
            )
        for drawing in request.drawing_sources:
            sheet = drawing.sheet_id or (
                drawing.path.name if drawing.path is not None else "drawing"
            )
            sources.append(
                RequirementSource(
                    text=drawing.text,
                    path=drawing.path,
                    source_kind=SourceKind.STRUCTURED_TEXT,
                    source_id=sheet,
                    revision=drawing.revision or request.revision,
                    stage=request.stage,
                    doc_type=drawing.doc_type or "drawing",
                    sha256=drawing.sha256,
                    doc_status=status_value,
                )
            )
        return sources
