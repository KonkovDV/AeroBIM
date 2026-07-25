"""MEP federated scope loading, system-graph probe and clearance matrix evaluation.

Extracted from AnalyzeProjectPackageUseCase. Fail-closed semantics preserved:
the probe never invents ERROR without geometry + customer matrix, and jail /
missing-path violations surface as FAILED capability.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from aerobim.domain.mep import (
    FederatedMepScope,
    MepSystemGraph,
    MepSystemGraphProvider,
    load_federated_mep_scope,
)
from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    FindingCategory,
    Severity,
    ValidationIssue,
)

_logger = logging.getLogger("aerobim.analyze")


def is_expected_unconfigured_error(exc: BaseException) -> bool:
    """MEP/CAD honesty placeholders raise RuntimeError by design → NOT_VERIFIED."""

    text = str(exc).casefold()
    return (
        "not configured" in text
        or "mep-clash-001" in text
        or "scope memo" in text
        or "not injected" in text
    )


class MepScopeProbe:
    """Probe MEP system graph honestly against a federated scope declaration."""

    def __init__(
        self,
        provider: MepSystemGraphProvider | None,
        scope_path: Path | None,
        repo_root: Callable[[], Path],
    ) -> None:
        self._provider = provider
        self._scope_path = scope_path
        self._repo_root = repo_root

    def load_scope(self) -> FederatedMepScope | None:
        path = self._scope_path
        if path is None:
            return None
        if not path.exists():
            return None
        return load_federated_mep_scope(path)

    def probe(self, ifc_path: Path) -> tuple[CapabilityStatus, tuple[ValidationIssue, ...]]:
        from aerobim.core.security.path_jail import PathJailError, resolve_repo_relative_path

        scope = self.load_scope()
        if scope is not None and scope.allows_federated_graph:
            missing_paths: list[str] = []
            jail_errors: list[str] = []
            for item in scope.federated_ifc_paths:
                try:
                    candidate = resolve_repo_relative_path(item, repo_root=self._repo_root())
                except PathJailError as exc:
                    jail_errors.append(f"{item}: {exc}")
                    continue
                if not candidate.exists():
                    missing_paths.append(item)
            if jail_errors:
                return (
                    CapabilityStatus(
                        CapabilityState.FAILED,
                        "federated MEP scope path jail violation: " + "; ".join(jail_errors[:3]),
                    ),
                    (),
                )
            if missing_paths:
                return (
                    CapabilityStatus(
                        CapabilityState.FAILED,
                        "federated MEP scope lists missing IFC paths: "
                        + ", ".join(missing_paths[:5]),
                    ),
                    (),
                )
        if self._provider is None:
            reason = "MEP system graph provider not injected"
            if scope is not None:
                reason += f"; scope_status={scope.status}"
            return CapabilityStatus(CapabilityState.NOT_VERIFIED, reason), ()
        try:
            graph = self._provider.build(ifc_path)
        except Exception as exc:
            _logger.exception("MEP system graph probe failed for %s", ifc_path)
            if is_expected_unconfigured_error(exc):
                reason = str(exc)
                if scope is not None:
                    reason += f"; scope_status={scope.status}"
                return CapabilityStatus(CapabilityState.NOT_VERIFIED, reason), ()
            return (
                CapabilityStatus(
                    CapabilityState.FAILED,
                    f"MEP system graph infrastructure failure: {exc}",
                ),
                (),
            )
        if not graph.nodes:
            reason = "MEP system graph built empty; federated scope still required for sign-off"
            if scope is not None:
                reason += f"; scope_status={scope.status}"
            return CapabilityStatus(CapabilityState.NOT_VERIFIED, reason), ()

        mep_issues = self.evaluate_clearance_matrix(graph, scope)
        if any(
            issue.rule_id == "AEROBIM-MEP-MATRIX-MISSING" and issue.severity == Severity.ERROR
            for issue in mep_issues
        ):
            return (
                CapabilityStatus(
                    CapabilityState.FAILED,
                    "MEP clearance matrix required by scope but missing/unloadable",
                ),
                mep_issues,
            )
        synthetic = getattr(graph, "synthetic", False)
        suffix = (
            "; synthetic/eng_fixture graph — not customer evidence (RT-003 OPEN)"
            if synthetic
            else "; customer scope memo pending (RT-003 OPEN)"
        )
        if scope is not None:
            suffix += f"; scope_status={scope.status}"
            if scope.scope_memo_ref:
                suffix += f"; scope_memo_ref={scope.scope_memo_ref}"
        if mep_issues:
            suffix += f"; matrix_findings={len(mep_issues)}"
        return (
            CapabilityStatus(
                CapabilityState.NOT_VERIFIED,
                f"MEP graph probe returned {len(graph.nodes)} nodes{suffix}",
            ),
            mep_issues,
        )

    def evaluate_clearance_matrix(
        self,
        graph: MepSystemGraph,
        scope: FederatedMepScope | None,
    ) -> tuple[ValidationIssue, ...]:
        """Evaluate clearance matrix — never invents ERROR without geometry + customer matrix."""

        from aerobim.core.security.path_jail import PathJailError, resolve_repo_relative_path
        from aerobim.domain.mep import (
            evaluate_matrix_against_graph,
            load_mep_clearance_matrix,
            mep_finding_to_issue,
        )

        requires_matrix = scope is not None and (
            scope.verified or scope.eng_fixture or bool(scope.clearance_matrix_ref)
        )
        matrix_ref = scope.clearance_matrix_ref if scope is not None else None
        if not matrix_ref:
            if requires_matrix and scope is not None and (scope.verified or scope.eng_fixture):
                return (
                    ValidationIssue(
                        rule_id="AEROBIM-MEP-MATRIX-MISSING",
                        severity=Severity.ERROR,
                        message=(
                            "Scope requires clearance_matrix_ref but none configured "
                            "(fail-closed; RT-003)"
                        ),
                        category=FindingCategory.SPATIAL,
                        source_id="mep-clearance-matrix",
                        origin="deterministic",
                        evidence_refs=("claim_boundary:matrix_required",),
                    ),
                )
            return ()
        try:
            candidate = resolve_repo_relative_path(matrix_ref, repo_root=self._repo_root())
        except PathJailError as exc:
            return (
                ValidationIssue(
                    rule_id="AEROBIM-MEP-MATRIX-MISSING",
                    severity=Severity.ERROR,
                    message=f"MEP clearance matrix path jail violation: {exc}",
                    category=FindingCategory.SPATIAL,
                    source_id="mep-clearance-matrix",
                    origin="deterministic",
                ),
            )
        if not candidate.exists():
            return (
                ValidationIssue(
                    rule_id="AEROBIM-MEP-MATRIX-MISSING",
                    severity=Severity.ERROR if requires_matrix else Severity.WARNING,
                    message=f"MEP clearance matrix not found: {matrix_ref}",
                    category=FindingCategory.SPATIAL,
                    source_id="mep-clearance-matrix",
                    origin="deterministic",
                ),
            )
        try:
            matrix = load_mep_clearance_matrix(candidate)
            # Graph edges are co-presence only until a geometry probe exists.
            findings = evaluate_matrix_against_graph(graph, matrix)
        except Exception as exc:
            _logger.exception("MEP clearance matrix evaluation failed")
            return (
                ValidationIssue(
                    rule_id="AEROBIM-MEP-MATRIX-ERROR",
                    severity=Severity.ERROR if requires_matrix else Severity.WARNING,
                    message=f"MEP clearance matrix evaluation failed: {exc}",
                    category=FindingCategory.SPATIAL,
                    source_id="mep-clearance-matrix",
                    origin="deterministic",
                ),
            )
        return tuple(
            mep_finding_to_issue(
                finding,
                matrix_synthetic=bool(matrix.synthetic),
                geometry_verified=False,
            )
            for finding in findings
        )
