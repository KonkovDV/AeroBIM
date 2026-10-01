"""Signature envelope and package-completeness checks."""

from __future__ import annotations

import json

from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    FindingCategory,
    Severity,
    ValidationIssue,
    ValidationRequest,
)
from aerobim.domain.ports import DocumentSignatureAuditor, PackageInventoryLoader


class SignatureAuditRunner:
    def __init__(
        self,
        *,
        document_signature_auditor: DocumentSignatureAuditor | None,
        package_inventory_loader: PackageInventoryLoader | None,
    ) -> None:
        self._document_signature_auditor = document_signature_auditor
        self._package_inventory_loader = package_inventory_loader

    def run_signature_audit(
        self, request: ValidationRequest
    ) -> tuple[CapabilityStatus | None, list[ValidationIssue]]:
        should_run = request.require_signature_audit or request.signature_envelope_path is not None
        if not should_run:
            return None, []

        from aerobim.domain.signature_immutability import (
            CLAIM_BOUNDARY,
            missing_envelope_result,
        )

        auditor = self._document_signature_auditor
        if auditor is None:
            if request.require_signature_audit:
                reason = (
                    "signature audit required but DocumentSignatureAuditor not configured; "
                    f"{CLAIM_BOUNDARY}"
                )
                return (
                    CapabilityStatus(CapabilityState.FAILED, reason),
                    [
                        ValidationIssue(
                            rule_id="AEROBIM-SIGNATURE-MISSING",
                            severity=Severity.ERROR,
                            message=reason,
                            category=FindingCategory.IFC_VALIDATION,
                            source_id="signature-audit",
                            origin="deterministic",
                            evidence_refs=("claim_boundary:signature_ENG_PARTIAL",),
                        )
                    ],
                )
            return None, []

        if request.ifc_path is None:
            if request.require_signature_audit:
                reason = f"signature audit required but ifc_path omitted; {CLAIM_BOUNDARY}"
                return (
                    CapabilityStatus(CapabilityState.FAILED, reason),
                    [
                        ValidationIssue(
                            rule_id="AEROBIM-SIGNATURE-MISSING",
                            severity=Severity.ERROR,
                            message=reason,
                            category=FindingCategory.IFC_VALIDATION,
                            source_id="signature-audit",
                            origin="deterministic",
                            evidence_refs=("claim_boundary:signature_ENG_PARTIAL",),
                        )
                    ],
                )
            return None, []

        result = auditor.audit(
            request.ifc_path,
            envelope_path=request.signature_envelope_path,
            required_roles=request.required_signer_roles,
        )
        capability = result.to_capability_status()
        issues: list[ValidationIssue] = []
        if request.require_signature_audit and "missing_envelope" in result.reasons:
            failed = missing_envelope_result(reason="missing_envelope")
            capability = CapabilityStatus(
                CapabilityState.FAILED,
                "; ".join([*failed.reasons, failed.claim_boundary]),
            )
            issues.append(
                ValidationIssue(
                    rule_id="AEROBIM-SIGNATURE-MISSING",
                    severity=Severity.ERROR,
                    message=(
                        "Required detached signature envelope missing next to content "
                        f"(or at signature_envelope_path); {CLAIM_BOUNDARY}"
                    ),
                    category=FindingCategory.IFC_VALIDATION,
                    source_id="signature-audit",
                    origin="deterministic",
                    evidence_refs=("claim_boundary:signature_ENG_PARTIAL",),
                )
            )
        elif result.overall_status == "failed":
            issues.append(
                ValidationIssue(
                    rule_id="AEROBIM-SIGNATURE-AUDIT",
                    severity=Severity.ERROR,
                    message=(
                        "Detached signature envelope audit failed "
                        f"({', '.join(result.reasons)}); {CLAIM_BOUNDARY}"
                    ),
                    category=FindingCategory.IFC_VALIDATION,
                    source_id="signature-audit",
                    origin="deterministic",
                    evidence_refs=("claim_boundary:signature_ENG_PARTIAL",),
                )
            )
        return capability, issues

    def run_package_completeness(
        self, request: ValidationRequest
    ) -> tuple[CapabilityStatus | None, list[ValidationIssue]]:
        should_run = (
            request.require_package_completeness or request.package_inventory_path is not None
        )
        if not should_run:
            return None, []

        from aerobim.domain.package_completeness import CLAIM_BOUNDARY

        loader = self._package_inventory_loader
        inventory_path = request.package_inventory_path
        if inventory_path is None:
            reason = (
                "package completeness required but package_inventory_path not provided; "
                f"{CLAIM_BOUNDARY}"
            )
            return (
                CapabilityStatus(CapabilityState.FAILED, reason),
                [
                    ValidationIssue(
                        rule_id="AEROBIM-PACKAGE-INVENTORY-MISSING",
                        severity=Severity.ERROR,
                        message=reason,
                        category=FindingCategory.CROSS_DOCUMENT,
                        source_id="package-completeness",
                        origin="deterministic",
                        evidence_refs=("claim_boundary:package_completeness_ENG_PARTIAL",),
                    )
                ],
            )
        if loader is None:
            reason = (
                "package completeness requested but PackageInventoryLoader not configured; "
                f"{CLAIM_BOUNDARY}"
            )
            return (
                CapabilityStatus(CapabilityState.FAILED, reason),
                [
                    ValidationIssue(
                        rule_id="AEROBIM-PACKAGE-INVENTORY-MISSING",
                        severity=Severity.ERROR,
                        message=reason,
                        category=FindingCategory.CROSS_DOCUMENT,
                        source_id="package-completeness",
                        origin="deterministic",
                        evidence_refs=("claim_boundary:package_completeness_ENG_PARTIAL",),
                    )
                ],
            )

        try:
            report = loader.assess(inventory_path)
        except FileNotFoundError:
            reason = f"Package inventory not found at {inventory_path}; {CLAIM_BOUNDARY}"
            return (
                CapabilityStatus(CapabilityState.FAILED, reason),
                [
                    ValidationIssue(
                        rule_id="AEROBIM-PACKAGE-INVENTORY-MISSING",
                        severity=Severity.ERROR,
                        message=reason,
                        category=FindingCategory.CROSS_DOCUMENT,
                        source_id="package-completeness",
                        origin="deterministic",
                        evidence_refs=("claim_boundary:package_completeness_ENG_PARTIAL",),
                    )
                ],
            )
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
            reason = f"Package inventory unreadable ({exc}); {CLAIM_BOUNDARY}"
            return (
                CapabilityStatus(CapabilityState.FAILED, reason),
                [
                    ValidationIssue(
                        rule_id="AEROBIM-PACKAGE-INVENTORY-UNREADABLE",
                        severity=Severity.ERROR,
                        message=reason,
                        category=FindingCategory.CROSS_DOCUMENT,
                        source_id="package-completeness",
                        origin="deterministic",
                        evidence_refs=("claim_boundary:package_completeness_ENG_PARTIAL",),
                    )
                ],
            )

        return report.to_capability_status(), list(report.issues)
