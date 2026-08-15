"""Clash, quantity, load and logic checks extracted from AnalyzeProjectPackageUseCase."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path

from aerobim.application.services.capability_policy import build_signoff_policy
from aerobim.application.services.spatial_predicates import issues_from_clash_results
from aerobim.domain.consistency import PackageManifest, claims_from_area_requirements
from aerobim.domain.errors import ClashCapabilityError
from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    ClashResult,
    FindingCategory,
    ParsedRequirement,
    Severity,
    ValidationIssue,
    ValidationRequest,
)
from aerobim.domain.ports import (
    ClashDetector,
    LoadEvidenceVerifier,
    LogicConsistencyAnalyzer,
    QuantityConsistencyChecker,
)

_logger = logging.getLogger("aerobim.analyze")


class ClashDetectionRunner:
    def __init__(
        self,
        *,
        clash_detector: ClashDetector | None,
        require_clash: bool,
        clash_affects_pass: bool,
        signoff_profile: str,
        require_bsi_schema: bool,
        require_mep_system_clash: bool,
        quantity_consistency_checker: QuantityConsistencyChecker | None = None,
        load_evidence_verifier: LoadEvidenceVerifier | None = None,
        logic_consistency_analyzer: LogicConsistencyAnalyzer | None = None,
    ) -> None:
        self._clash_detector = clash_detector
        self._require_clash = require_clash
        self._clash_affects_pass = clash_affects_pass
        self._signoff_profile = signoff_profile
        self._require_bsi_schema = require_bsi_schema
        self._require_mep_system_clash = require_mep_system_clash
        self._quantity_consistency_checker = quantity_consistency_checker
        self._load_evidence_verifier = load_evidence_verifier
        self._logic_consistency_analyzer = logic_consistency_analyzer

    def effective_clash_affects_pass(self) -> bool:
        return build_signoff_policy(
            profile=self._signoff_profile,
            require_clash=self._require_clash,
            clash_affects_pass=self._clash_affects_pass,
            require_bsi_schema=self._require_bsi_schema,
            require_mep_system_clash=self._require_mep_system_clash,
        ).clash_affects_pass

    def run_clash_detection(
        self, ifc_path: Path
    ) -> tuple[tuple[ClashResult, ...], CapabilityStatus, list[ValidationIssue]]:
        if self._clash_detector is None:
            if self._require_clash:
                issue = ValidationIssue(
                    rule_id="AEROBIM-CLASH-CAPABILITY",
                    severity=Severity.ERROR,
                    message="Clash detection required but detector is not configured",
                    category=FindingCategory.SPATIAL,
                    source_id="clash",
                )
                return (
                    (),
                    CapabilityStatus(CapabilityState.FAILED, "clash detector not configured"),
                    [issue],
                )
            return (
                (),
                CapabilityStatus(CapabilityState.SKIPPED, "clash detector not configured"),
                [],
            )
        try:
            results = tuple(self._clash_detector.detect(ifc_path))
            return (
                results,
                CapabilityStatus(CapabilityState.OK),
                issues_from_clash_results(
                    results,
                    affects_pass=self.effective_clash_affects_pass(),
                ),
            )
        except ClashCapabilityError as exc:
            skipped = exc.status == "skipped"
            if skipped and self._require_clash:
                state = CapabilityState.FAILED
            else:
                state = CapabilityState.SKIPPED if skipped else CapabilityState.FAILED
            severity = Severity.ERROR if state == CapabilityState.FAILED else Severity.WARNING
            issue = ValidationIssue(
                rule_id="AEROBIM-CLASH-CAPABILITY",
                severity=severity,
                message=f"Clash detection capability {exc.status}: {exc.reason}",
                category=FindingCategory.SPATIAL,
                source_id="clash",
            )
            return (), CapabilityStatus(state, exc.reason), [issue]
        except Exception as exc:  # noqa: BLE001
            issue = ValidationIssue(
                rule_id="AEROBIM-CLASH-CAPABILITY",
                severity=Severity.ERROR,
                message=f"Clash detection capability failed: {exc}",
                category=FindingCategory.SPATIAL,
                source_id="clash",
            )
            return (
                (),
                CapabilityStatus(CapabilityState.FAILED, str(exc)),
                [issue],
            )

    def run_quantity_consistency(
        self,
        ifc_path: Path,
        requirements: Sequence[ParsedRequirement],
    ) -> tuple[list[ValidationIssue], CapabilityStatus | None]:
        claims = claims_from_area_requirements(requirements)
        if not claims:
            return [], None
        if self._quantity_consistency_checker is None:
            return (
                [],
                CapabilityStatus(
                    CapabilityState.NOT_VERIFIED,
                    "QuantityConsistencyChecker not configured while area claims present",
                ),
            )
        try:
            return list(
                self._quantity_consistency_checker.check(ifc_path, claims)
            ), CapabilityStatus(CapabilityState.OK, "quantity consistency evaluated")
        except Exception as exc:
            _logger.exception("Quantity consistency check failed for %s", ifc_path)
            return (
                [
                    ValidationIssue(
                        rule_id="AEROBIM-QTY-ERROR",
                        severity=Severity.ERROR,
                        message=f"Quantity consistency infrastructure failure: {exc}",
                        category=FindingCategory.IFC_VALIDATION,
                        source_id="quantity-consistency",
                    )
                ],
                CapabilityStatus(
                    CapabilityState.FAILED,
                    f"Quantity consistency infrastructure failure: {exc}",
                ),
            )

    def run_load_evidence(
        self, request: ValidationRequest
    ) -> tuple[list[ValidationIssue], CapabilityStatus]:
        if request.calculation_source is None:
            return (
                [],
                CapabilityStatus(
                    CapabilityState.SKIPPED, "numeric calculation match not evaluated"
                ),
            )
        if self._load_evidence_verifier is None:
            return (
                [],
                CapabilityStatus(CapabilityState.SKIPPED, "LoadEvidenceVerifier not configured"),
            )
        try:
            issues = list(self._load_evidence_verifier.verify(request))
        except Exception as exc:
            _logger.exception("Load evidence verify failed for request %s", request.request_id)
            return (
                [
                    ValidationIssue(
                        rule_id="AEROBIM-LOAD-ERROR",
                        severity=Severity.ERROR,
                        message=f"Load evidence infrastructure failure: {exc}",
                        category=FindingCategory.CROSS_DOCUMENT,
                        source_id="load-evidence",
                    )
                ],
                CapabilityStatus(
                    CapabilityState.FAILED,
                    f"Load evidence infrastructure failure: {exc}",
                ),
            )
        mismatches = [i for i in issues if i.rule_id == "AEROBIM-LOAD-MISMATCH"]
        unevaluated = any(
            i.rule_id
            in {
                "AEROBIM-LOAD-FORMAT",
                "AEROBIM-LOAD-SCHEMA",
                "AEROBIM-LOAD-JSON",
                "AEROBIM-LOAD-ROW",
            }
            for i in issues
        )
        evaluated_ok = any(i.rule_id == "AEROBIM-LOAD-OK" for i in issues)
        if mismatches:
            capability = CapabilityStatus(
                CapabilityState.FAILED,
                f"{len(mismatches)} load match failure(s)",
            )
        elif unevaluated or not evaluated_ok:
            capability = CapabilityStatus(
                CapabilityState.NOT_VERIFIED,
                "Load evidence present but сверка not fully evaluated",
            )
        else:
            capability = CapabilityStatus(
                CapabilityState.OK,
                "Load evidence numeric match evaluated",
            )
        return issues, capability

    def run_logic_consistency(self, request: ValidationRequest) -> list[ValidationIssue]:
        if self._logic_consistency_analyzer is None:
            return []
        has_req = bool(
            request.requirement_source.text.strip() or request.requirement_source.path is not None
        )
        manifest = PackageManifest(
            request_id=request.request_id,
            ifc_path=request.ifc_path,
            has_requirement_source=has_req,
            has_technical_spec=request.technical_spec_source is not None,
            has_calculation_source=request.calculation_source is not None,
            has_ids=request.ids_path is not None,
            drawing_count=len(request.drawing_sources),
            drawing_sheet_ids=tuple((source.sheet_id or "") for source in request.drawing_sources),
            pd_section_path=request.pd_section_path,
            rd_section_path=request.rd_section_path,
            revision=request.revision,
            stage=request.stage,
        )
        return list(self._logic_consistency_analyzer.analyze(manifest))
