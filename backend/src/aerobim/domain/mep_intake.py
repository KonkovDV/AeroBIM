"""MEP customer intake assessment (RT-003 / MEP-CLASH-001) — domain pure."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aerobim.domain.mep import FederatedMepScope


@dataclass(frozen=True)
class MepCustomerIntakeResult:
    ready: bool
    status: str
    """blocked_customer_data | fixture_only | not_verified | ready_for_experiment"""
    gap_id: str
    reason: str
    checks: dict[str, bool]
    affects_pass: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reason": self.reason,
            "gap_id": self.gap_id,
            "affects_pass": self.affects_pass,
            "ready": self.ready,
            "checks": dict(self.checks),
        }


def assess_mep_customer_intake(
    scope: FederatedMepScope | None,
    *,
    matrix_path_exists: bool,
    matrix_synthetic: bool,
) -> MepCustomerIntakeResult:
    """Fail-closed intake: fixture/template never equals customer-validated."""

    gap_id = "MEP-CLASH-001"
    if scope is None:
        return MepCustomerIntakeResult(
            ready=False,
            status="blocked_customer_data",
            gap_id=gap_id,
            reason="federated MEP model and customer rules are required",
            checks={
                "federated_scope_present": False,
                "federated_ifc_paths": False,
                "scope_memo": False,
                "expert_signoff": False,
                "matrix_present": matrix_path_exists,
                "matrix_customer_signed": False,
            },
        )

    checks = {
        "federated_scope_present": True,
        "federated_ifc_paths": len(scope.federated_ifc_paths) >= 1,
        "scope_memo": bool(scope.scope_memo_ref),
        "expert_signoff": bool(scope.expert_signed_by and scope.expert_signed_at),
        "matrix_present": matrix_path_exists,
        "matrix_customer_signed": matrix_path_exists and not matrix_synthetic,
        "status_verified": scope.verified,
        "status_eng_fixture": scope.eng_fixture,
    }

    if scope.eng_fixture:
        return MepCustomerIntakeResult(
            ready=False,
            status="fixture_only",
            gap_id=gap_id,
            reason=(
                "ENG_FIXTURE federated scope — engineering demo only; not customer RT-003 evidence"
            ),
            checks=checks,
        )

    if not scope.verified or not checks["matrix_customer_signed"]:
        return MepCustomerIntakeResult(
            ready=False,
            status="blocked_customer_data",
            gap_id=gap_id,
            reason="federated MEP model and customer rules are required",
            checks=checks,
        )

    return MepCustomerIntakeResult(
        ready=True,
        status="ready_for_experiment",
        gap_id=gap_id,
        reason=(
            "Customer federated scope + signed matrix present — "
            "system-aware clash still requires geometry_verified evidence"
        ),
        checks=checks,
        affects_pass=True,
    )


__all__ = ["MepCustomerIntakeResult", "assess_mep_customer_intake"]
