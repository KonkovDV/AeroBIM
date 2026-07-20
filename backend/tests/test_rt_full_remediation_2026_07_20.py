"""RT-FULL remediation coverage — 2026-07-20."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from aerobim.application.services.capability_policy import build_signoff_policy
from aerobim.application.use_cases.validate_ifc_against_ids import ValidateIfcAgainstIdsUseCase
from aerobim.core.security.outbound_url import UnsafeOutboundUrlError, assert_safe_outbound_url
from aerobim.domain.models import (
    CapabilityState,
    RequirementSource,
    SourceKind,
    ValidationRequest,
)
from aerobim.infrastructure.adapters.docling_requirement_extractor import (
    StructuredRequirementExtractor,
)
from aerobim.infrastructure.adapters.in_memory_audit_store import InMemoryAuditStore
from aerobim.infrastructure.security.oidc_token_validator import (
    OidcTokenValidator,
    OidcValidationError,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


class BuildSignoffPolicyHardProfileTests(unittest.TestCase):
    def test_production_ignores_require_clash_false(self) -> None:
        policy = build_signoff_policy(profile="production", require_clash=False)
        self.assertTrue(policy.require_clash)
        self.assertTrue(policy.clash_affects_pass)
        self.assertTrue(policy.require_bsi_schema)
        self.assertTrue(policy.require_mep_system_clash)
        self.assertTrue(policy.enforce_object_acl)
        self.assertTrue(policy.audit_fail_closed)

    def test_development_allows_explicit_overrides(self) -> None:
        policy = build_signoff_policy(
            profile="development",
            require_clash=True,
            enforce_object_acl=True,
        )
        self.assertTrue(policy.require_clash)
        self.assertTrue(policy.enforce_object_acl)


class ValidateIfcProductionPolicyTests(unittest.TestCase):
    def test_production_profile_fails_when_capabilities_incomplete(self) -> None:
        store = InMemoryAuditStore()
        uc = ValidateIfcAgainstIdsUseCase(
            requirement_extractor=StructuredRequirementExtractor(),
            ifc_validator=MagicMock(validate=MagicMock(return_value=[])),
            audit_report_store=store,
            ids_validator=None,
            ifc_schema_validator=None,
            ids_document_auditor=None,
            signoff_profile="production",
            require_clash=False,  # ignored under production
        )
        with tempfile.TemporaryDirectory() as tmp:
            ifc = Path(tmp) / "model.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            ids = Path(tmp) / "req.ids"
            ids.write_text("<ids/>", encoding="utf-8")
            report = uc.execute(
                ValidationRequest(
                    request_id="rt-full-validate",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n",
                        path=None,
                        source_kind=SourceKind.STRUCTURED_TEXT,
                    ),
                    ids_path=ids,
                )
            )
        self.assertFalse(report.summary.passed)
        self.assertGreater(report.summary.error_count, 0)
        self.assertIsNotNone(report.capabilities.ids)
        assert report.capabilities.ids is not None
        self.assertIs(report.capabilities.ids.status, CapabilityState.FAILED)
        self.assertTrue(
            any(i.rule_id == "AEROBIM-IDS-AUDIT-CAPABILITY" for i in report.issues),
            report.issues,
        )


class OidcMissingKidTests(unittest.TestCase):
    def test_missing_kid_rejects(self) -> None:
        try:
            import jwt  # noqa: F401
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PyJWT not installed") from exc

        validator = OidcTokenValidator(
            issuer="https://idp.example.com/",
            audience="aerobim-api",
            jwks_url="https://idp.example.com/.well-known/jwks.json",
        )
        with (
            patch.object(
                validator,
                "fetch_jwks",
                return_value={"keys": [{"kid": "k1", "kty": "RSA"}]},
            ),
            patch("jwt.get_unverified_header", return_value={"alg": "RS256"}),
        ):
            with self.assertRaises(OidcValidationError) as ctx:
                validator.validate("header.payload.sig")
        self.assertIn("kid", str(ctx.exception).lower())


class OutboundCgnatBlockedTests(unittest.TestCase):
    def test_cgnat_literal_blocked(self) -> None:
        with self.assertRaises(UnsafeOutboundUrlError):
            assert_safe_outbound_url("https://100.64.1.2/jwks", resolve_dns=False)

    def test_cgnat_is_not_global(self) -> None:
        from aerobim.core.security.outbound_url import _is_blocked_ip

        self.assertTrue(_is_blocked_ip("100.64.0.1"))
        self.assertTrue(_is_blocked_ip("100.127.255.255"))


class ComposeProductionBindTests(unittest.TestCase):
    def test_production_compose_binds_loopback(self) -> None:
        text = (_repo_root() / "docker-compose.production.yml").read_text(encoding="utf-8")
        self.assertIn("127.0.0.1:8080:8080", text)
        self.assertNotIn('"8080:8080"', text)


if __name__ == "__main__":
    unittest.main()
