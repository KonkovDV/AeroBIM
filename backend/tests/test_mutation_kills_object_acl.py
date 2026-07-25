"""H1.1 mutation-kill tests for domain/object_acl.py (cosmic-ray survivors).

Baseline run (tests/mutation/object_acl.toml): 103 mutants, 42 survived.
Verification run with this file added: 103 mutants = 33 non-viable
(SyntaxError: ``*`` keyword-only marker mutated into a binary operator) +
36 killed + 34 survived. Survivor triage:

* 33x ``ReplaceBinaryOperator_BitOr_*`` on ``str | None`` annotations —
  equivalent mutants: the module uses ``from __future__ import annotations``,
  so annotation expressions are never evaluated at runtime.
* 1x ``ReplaceOrWithAnd`` on the ``if not a or not b`` guard in
  ``_tenants_match`` — equivalent through every caller: when exactly one side
  is empty the fallthrough ``casefold`` comparison still returns False, and
  both-empty is caught by both variants. The guard is defense in depth.

Effective mutation score (equivalents excluded): 36/36 = 1.0 ≥ 0.85 target.
The pre-existing gaps killed by this file are named per test below.
"""

from __future__ import annotations

import dataclasses
import unittest
from datetime import UTC, datetime
from pathlib import Path

from aerobim.domain.models import (
    AnalyzeProjectPackageJob,
    JobStatus,
    ValidationReport,
    ValidationSummary,
)
from aerobim.domain.object_acl import (
    AuthPrincipal,
    principal_may_access_job,
    principal_may_access_norm_pack,
    principal_may_access_report,
)


def _report(tenant_id: str | None) -> ValidationReport:
    return ValidationReport(
        report_id="a" * 32,
        request_id="req",
        ifc_path=Path("sample.ifc"),
        created_at=datetime.now(tz=UTC).isoformat(),
        requirements=(),
        issues=(),
        summary=ValidationSummary(
            requirement_count=0,
            issue_count=0,
            error_count=0,
            warning_count=0,
            passed=True,
        ),
        tenant_id=tenant_id,
    )


def _job(tenant_id: str | None) -> AnalyzeProjectPackageJob:
    return AnalyzeProjectPackageJob(
        job_id="b" * 32,
        request_id="req",
        status=JobStatus.QUEUED,
        created_at=datetime.now(tz=UTC).isoformat(),
        tenant_id=tenant_id,
    )


class AuthPrincipalImmutabilityTests(unittest.TestCase):
    def test_principal_is_frozen(self) -> None:
        """Kills ``@dataclass(frozen=True)`` -> ``frozen=False``."""
        principal = AuthPrincipal(tenant_id="tenant-a", subject="s")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            principal.tenant_id = "tenant-b"  # type: ignore[misc]


class AclDisabledAllowsAccessTests(unittest.TestCase):
    """Kills ``return True`` -> ``return False`` on the enforce=False branches."""

    def test_report_access_allowed_when_acl_off(self) -> None:
        self.assertTrue(
            principal_may_access_report(
                enforce_object_acl=False,
                principal=AuthPrincipal(tenant_id="tenant-a"),
                report=_report("tenant-b"),
            )
        )

    def test_job_access_allowed_when_acl_off(self) -> None:
        self.assertTrue(
            principal_may_access_job(
                enforce_object_acl=False,
                principal=AuthPrincipal(tenant_id="tenant-a"),
                job=_job("tenant-b"),
            )
        )

    def test_norm_pack_access_allowed_when_acl_off(self) -> None:
        self.assertTrue(
            principal_may_access_norm_pack(
                enforce_object_acl=False,
                principal=AuthPrincipal(tenant_id="tenant-a"),
                tenant_id="tenant-b",
            )
        )


class UnboundResourceDeniedTests(unittest.TestCase):
    """Kills ``return False`` -> ``return True`` on legacy/unbound resources."""

    def test_report_without_tenant_denied_under_acl(self) -> None:
        for legacy_tenant in (None, "", "   "):
            with self.subTest(tenant=legacy_tenant):
                self.assertFalse(
                    principal_may_access_report(
                        enforce_object_acl=True,
                        principal=AuthPrincipal(tenant_id="tenant-a"),
                        report=_report(legacy_tenant),
                    )
                )

    def test_job_without_tenant_denied_under_acl(self) -> None:
        for legacy_tenant in (None, "", "   "):
            with self.subTest(tenant=legacy_tenant):
                self.assertFalse(
                    principal_may_access_job(
                        enforce_object_acl=True,
                        principal=AuthPrincipal(tenant_id="tenant-a"),
                        job=_job(legacy_tenant),
                    )
                )

    def test_norm_pack_without_tenant_denied_under_acl(self) -> None:
        for legacy_tenant in (None, "", "   "):
            with self.subTest(tenant=legacy_tenant):
                self.assertFalse(
                    principal_may_access_norm_pack(
                        enforce_object_acl=True,
                        principal=AuthPrincipal(tenant_id="tenant-a"),
                        tenant_id=legacy_tenant,
                    )
                )


class UnboundPrincipalDeniedTests(unittest.TestCase):
    """Kills ``return False`` -> ``return True`` in the ``_tenants_match`` guard."""

    def test_principal_without_tenant_denied_for_bound_resources(self) -> None:
        for empty_tenant in (None, "", "   "):
            principal = AuthPrincipal(tenant_id=empty_tenant)
            with self.subTest(tenant=empty_tenant):
                self.assertFalse(
                    principal_may_access_report(
                        enforce_object_acl=True,
                        principal=principal,
                        report=_report("tenant-a"),
                    )
                )
                self.assertFalse(
                    principal_may_access_job(
                        enforce_object_acl=True,
                        principal=principal,
                        job=_job("tenant-a"),
                    )
                )
                self.assertFalse(
                    principal_may_access_norm_pack(
                        enforce_object_acl=True,
                        principal=principal,
                        tenant_id="tenant-a",
                    )
                )


if __name__ == "__main__":
    unittest.main()
