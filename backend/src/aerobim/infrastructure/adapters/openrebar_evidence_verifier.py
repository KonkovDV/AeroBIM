"""OpenRebar external evidence verifier (C.2 ExternalEvidence port implementation)."""

from __future__ import annotations

import json
from collections.abc import Mapping

from aerobim.domain.models import FindingCategory, Severity, ValidationIssue, ValidationRequest

_OPENREBAR_REPORT_CONTRACT_ID = "OpenRebar.reinforcement.report.v1"


def build_openrebar_provenance_digest(report_payload: Mapping[str, object]) -> str:
    import hashlib

    canonical_payload = {
        "contractId": report_payload.get("contractId"),
        "schemaVersion": report_payload.get("schemaVersion"),
        "generatedAtUtc": report_payload.get("generatedAtUtc"),
        "isolineFileName": report_payload.get("isolineFileName"),
        "isolineFileFormat": report_payload.get("isolineFileFormat"),
        "metadata": report_payload.get("metadata"),
        "normativeProfile": report_payload.get("normativeProfile"),
        "analysisProvenance": report_payload.get("analysisProvenance"),
        "summary": report_payload.get("summary"),
    }
    normalized = json.dumps(
        canonical_payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class OpenRebarEvidenceVerifier:
    """Verify OpenRebar reinforcement report provenance against the validation request."""

    def verify(self, request: ValidationRequest) -> list[ValidationIssue]:
        if request.reinforcement_report_path is None:
            return []

        report_path = request.reinforcement_report_path
        if not report_path.exists():
            raise FileNotFoundError(report_path)

        try:
            report_payload = json.loads(report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid OpenRebar reinforcement report JSON: {report_path}") from exc

        if not isinstance(report_payload, dict):
            raise ValueError("OpenRebar reinforcement report must be a JSON object")

        return self._verify_payload(request, report_payload)

    def _verify_payload(
        self,
        request: ValidationRequest,
        report_payload: dict[str, object],
    ) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        contract_id = str(report_payload.get("contractId", "")).strip()
        metadata = report_payload.get("metadata")
        metadata_dict = metadata if isinstance(metadata, dict) else {}
        project_code = str(metadata_dict.get("projectCode", "")).strip()
        slab_id = str(metadata_dict.get("slabId", "")).strip() or None

        if contract_id != _OPENREBAR_REPORT_CONTRACT_ID:
            issues.append(
                ValidationIssue(
                    rule_id="OPENREBAR-CONTRACT",
                    severity=Severity.WARNING,
                    message=(
                        "OpenRebar report contractId is unexpected; downstream "
                        "integration guarantees may not hold."
                    ),
                    category=FindingCategory.CROSS_DOCUMENT,
                    target_ref=slab_id,
                    property_name="contractId",
                    expected_value=_OPENREBAR_REPORT_CONTRACT_ID,
                    observed_value=contract_id or "<missing>",
                )
            )

        optimization = report_payload.get("analysisProvenance")
        optimization_dict = optimization if isinstance(optimization, dict) else {}
        optimization_node = optimization_dict.get("optimization")
        optimization_payload = optimization_node if isinstance(optimization_node, dict) else {}
        fallback_solver_used = optimization_payload.get("anyFallbackMasterSolverUsed")
        master_problem_strategy = str(optimization_payload.get("masterProblemStrategy", "")).strip()

        if fallback_solver_used is True:
            issues.append(
                ValidationIssue(
                    rule_id="OPENREBAR-OPT-FALLBACK",
                    severity=Severity.WARNING,
                    message=(
                        "OpenRebar optimization used a fallback master solver; "
                        "waste metrics may deviate from the preferred HiGHS path."
                    ),
                    category=FindingCategory.CROSS_DOCUMENT,
                    target_ref=slab_id,
                    property_name=("analysisProvenance.optimization.anyFallbackMasterSolverUsed"),
                    expected_value="false",
                    observed_value="true",
                )
            )

        if "highs" not in master_problem_strategy.lower():
            issues.append(
                ValidationIssue(
                    rule_id="OPENREBAR-OPT-STRATEGY",
                    severity=Severity.WARNING,
                    message=(
                        "OpenRebar optimization master strategy does not indicate "
                        "HiGHS-backed solving."
                    ),
                    category=FindingCategory.CROSS_DOCUMENT,
                    target_ref=slab_id,
                    property_name="analysisProvenance.optimization.masterProblemStrategy",
                    expected_value="contains: highs",
                    observed_value=master_problem_strategy or "<missing>",
                )
            )

        if request.project_name and project_code:
            if request.project_name.strip().lower() != project_code.lower():
                issues.append(
                    ValidationIssue(
                        rule_id="OPENREBAR-PROJECT-CODE",
                        severity=Severity.WARNING,
                        message=(
                            "OpenRebar report projectCode differs from current "
                            "AeroBIM project context."
                        ),
                        category=FindingCategory.CROSS_DOCUMENT,
                        target_ref=slab_id,
                        property_name="metadata.projectCode",
                        expected_value=request.project_name,
                        observed_value=project_code,
                    )
                )

        observed_digest = build_openrebar_provenance_digest(report_payload)
        if request.reinforcement_source_digest:
            expected_digest = request.reinforcement_source_digest.strip().lower()
            if expected_digest and expected_digest != observed_digest:
                issues.append(
                    ValidationIssue(
                        rule_id="OPENREBAR-PROVENANCE-DIGEST",
                        severity=Severity.WARNING,
                        message=(
                            "OpenRebar provenance digest mismatch: reinforcement "
                            "model may be stale relative to current source package."
                        ),
                        category=FindingCategory.CROSS_DOCUMENT,
                        target_ref=slab_id,
                        property_name="reinforcementSourceDigest",
                        expected_value=expected_digest,
                        observed_value=observed_digest,
                    )
                )
        else:
            issues.append(
                ValidationIssue(
                    rule_id="OPENREBAR-PROVENANCE-REFERENCE-MISSING",
                    severity=Severity.WARNING,
                    message=(
                        "OpenRebar reference digest is missing; stale reinforcement "
                        "detection is disabled for this run."
                    ),
                    category=FindingCategory.CROSS_DOCUMENT,
                    target_ref=slab_id,
                    property_name="reinforcementSourceDigest",
                    expected_value="provided",
                    observed_value=observed_digest,
                )
            )

        threshold = request.reinforcement_waste_warning_threshold_percent
        if threshold is not None:
            summary_payload = report_payload.get("summary")
            summary_dict = summary_payload if isinstance(summary_payload, dict) else {}
            raw_total_waste = summary_dict.get("totalWastePercent")
            total_waste = (
                float(raw_total_waste)
                if isinstance(raw_total_waste, int | float)
                else _to_float(str(raw_total_waste))
                if raw_total_waste is not None
                else None
            )

            if total_waste is None:
                issues.append(
                    ValidationIssue(
                        rule_id="OPENREBAR-WASTE-METRIC-MISSING",
                        severity=Severity.WARNING,
                        message=(
                            "OpenRebar report summary does not contain a parseable "
                            "totalWastePercent value."
                        ),
                        category=FindingCategory.CROSS_DOCUMENT,
                        target_ref=slab_id,
                        property_name="summary.totalWastePercent",
                        expected_value="numeric",
                        observed_value="<missing>",
                    )
                )
            elif total_waste > threshold:
                issues.append(
                    ValidationIssue(
                        rule_id="OPENREBAR-WASTE-THRESHOLD",
                        severity=Severity.WARNING,
                        message=(
                            "OpenRebar total waste exceeds the configured AeroBIM "
                            "warning threshold."
                        ),
                        category=FindingCategory.CROSS_DOCUMENT,
                        target_ref=slab_id,
                        property_name="summary.totalWastePercent",
                        expected_value=f"<= {threshold:g}",
                        observed_value=f"{total_waste:g}",
                        unit="%",
                    )
                )

        return issues


def _to_float(raw: str) -> float | None:
    try:
        return float(raw.replace(",", "."))
    except ValueError:
        return None
