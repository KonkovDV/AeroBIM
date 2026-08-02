"""WP-03: detached signature envelope foundation (not legal УКЭП)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from aerobim.application.services.capability_policy import build_signoff_policy
from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    FindingCategory,
    GeneratedRemark,
    ReportCapabilities,
    RequirementSource,
    Severity,
    ValidationIssue,
    ValidationRequest,
)
from aerobim.domain.signature_immutability import (
    CLAIM_BOUNDARY,
    ENVELOPE_SCHEMA_V1,
    SignatureEnvelope,
    SignatureSigner,
    assess_signature_envelope,
    content_sha256_hex,
)
from aerobim.infrastructure.adapters.json_detached_signature_auditor import (
    JsonDetachedSignatureAuditor,
)


class _Empty:
    def extract(self, _source):
        return []

    def synthesize(self, _source):
        return []

    def analyze(self, _source):
        return []


class _Remark:
    def generate(self, issue):
        return GeneratedRemark(title=issue.rule_id, body=issue.message)


class _Store:
    def __init__(self) -> None:
        self.report = None

    def save(self, report):
        self.report = report
        return report.report_id

    def get(self, report_id):
        if self.report is not None and self.report.report_id == report_id:
            return self.report
        return None


def _write_pair(
    directory: Path,
    *,
    content: bytes = b"wp03-fixture-bytes\n",
    roles: tuple[str, ...] = ("author", "reviewer"),
    tamper_hash: str | None = None,
    omit_roles: tuple[str, ...] = (),
) -> tuple[Path, Path, str]:
    content_path = directory / "doc.bin"
    content_path.write_bytes(content)
    digest = content_sha256_hex(content_path)
    signers = [
        {
            "role": role,
            "subject": f"{role}@example.invalid",
            "cert_not_before": "2026-01-01T00:00:00+00:00",
            "cert_not_after": "2027-01-01T00:00:00+00:00",
            "signature_alg": "fixture-placeholder",
            "signature_value": "not-a-cryptographic-signature",
        }
        for role in roles
        if role not in omit_roles
    ]
    envelope = {
        "schema": ENVELOPE_SCHEMA_V1,
        "content_sha256": tamper_hash if tamper_hash is not None else digest,
        "signing_time": "2026-07-15T12:00:00+00:00",
        "signers": signers,
    }
    envelope_path = content_path.with_suffix(content_path.suffix + ".sig.json")
    envelope_path.write_text(json.dumps(envelope), encoding="utf-8")
    return content_path, envelope_path, digest


def _build_use_case(
    *,
    advisory_issues: tuple[ValidationIssue, ...] = (),
) -> AnalyzeProjectPackageUseCase:
    empty = _Empty()
    return AnalyzeProjectPackageUseCase(
        requirement_extractor=empty,
        narrative_rule_synthesizer=empty,
        drawing_analyzer=empty,
        ifc_validator=MagicMock(validate=MagicMock(return_value=[])),
        ids_validator=MagicMock(validate=MagicMock(return_value=[])),
        remark_generator=_Remark(),
        audit_report_store=_Store(),
        document_signature_auditor=JsonDetachedSignatureAuditor(),
        advisory_issues=advisory_issues,
        signoff_profile="fixture",
    )


class SignatureImmutabilityDomainTests(unittest.TestCase):
    def test_good_envelope_matching_hash_and_roles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            content_path, _, digest = _write_pair(Path(tmp))
            envelope = SignatureEnvelope.from_mapping(
                json.loads(
                    content_path.with_suffix(content_path.suffix + ".sig.json").read_text(
                        encoding="utf-8"
                    )
                )
            )
            result = assess_signature_envelope(
                envelope, digest, ("author", "reviewer"), signing_time=envelope.signing_time
            )
            self.assertTrue(result.structure_ok)
            self.assertTrue(result.integrity_ok)
            self.assertTrue(result.roles_complete)
            self.assertTrue(result.validity_window_ok)
            self.assertEqual(result.overall_status, "ok")
            self.assertEqual(result.trust_chain_status, "not_verified")
            self.assertIn("not_verified", result.claim_boundary.lower() + CLAIM_BOUNDARY.lower())
            self.assertNotIn("УКЭП проверена", result.claim_boundary)

    def test_tampered_content_fails_integrity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            content_path, _, digest = _write_pair(
                Path(tmp), tamper_hash="0" * 64
            )
            envelope = SignatureEnvelope.from_mapping(
                json.loads(
                    content_path.with_suffix(content_path.suffix + ".sig.json").read_text(
                        encoding="utf-8"
                    )
                )
            )
            result = assess_signature_envelope(envelope, digest, ("author",))
            self.assertFalse(result.integrity_ok)
            self.assertEqual(result.overall_status, "failed")
            self.assertIn("content_sha256_mismatch", result.reasons)
            self.assertEqual(result.trust_chain_status, "not_verified")

    def test_incomplete_roles_fail(self) -> None:
        envelope = SignatureEnvelope(
            schema=ENVELOPE_SCHEMA_V1,
            content_sha256="abc",
            signers=(SignatureSigner(role="author"),),
        )
        result = assess_signature_envelope(envelope, "abc", ("author", "reviewer"))
        self.assertFalse(result.roles_complete)
        self.assertEqual(result.overall_status, "failed")
        self.assertEqual(result.trust_chain_status, "not_verified")

    def test_trust_chain_always_not_verified(self) -> None:
        envelope = SignatureEnvelope(
            schema=ENVELOPE_SCHEMA_V1,
            content_sha256="deadbeef",
            signers=(SignatureSigner(role="author"),),
        )
        result = assess_signature_envelope(envelope, "deadbeef", ())
        self.assertEqual(result.trust_chain_status, "not_verified")
        self.assertIn("trust_chain_not_verified", result.reasons)

    def test_missing_envelope_fields_structure_not_ok(self) -> None:
        envelope = SignatureEnvelope(schema="", content_sha256="", signers=())
        result = assess_signature_envelope(envelope, "x", ())
        self.assertFalse(result.structure_ok)
        self.assertEqual(result.overall_status, "failed")


class JsonDetachedSignatureAuditorTests(unittest.TestCase):
    def test_adapter_good_and_missing(self) -> None:
        auditor = JsonDetachedSignatureAuditor()
        with tempfile.TemporaryDirectory() as tmp:
            content_path, envelope_path, _ = _write_pair(Path(tmp))
            ok = auditor.audit(
                content_path,
                envelope_path=envelope_path,
                required_roles=("author", "reviewer"),
            )
            self.assertEqual(ok.overall_status, "ok")
            self.assertEqual(ok.trust_chain_status, "not_verified")

            missing = auditor.audit(Path(tmp) / "no-such.bin", required_roles=("author",))
            self.assertEqual(missing.overall_status, "failed")
            self.assertIn("missing_envelope", missing.reasons)

            # Original bytes must remain unchanged after audit.
            before = content_path.read_bytes()
            auditor.audit(content_path, required_roles=("author",))
            self.assertEqual(content_path.read_bytes(), before)


class SignatureUseCaseWiringTests(unittest.TestCase):
    def test_missing_signature_when_required_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ifc = Path(tmp) / "model.ifc"
            ifc.write_text("ISO-10303-21;\nEND-ISO-10303-21;\n", encoding="utf-8")
            ids = Path(tmp) / "dummy.ids"
            ids.write_text("<ids/>", encoding="utf-8")
            report = _build_use_case().execute(
                ValidationRequest(
                    request_id="sig-missing",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="Wall FireRating == REI 60",
                    ),
                    ids_path=ids,
                    require_signature_audit=True,
                    required_signer_roles=("author",),
                )
            )
            self.assertTrue(
                any(i.rule_id == "AEROBIM-SIGNATURE-MISSING" for i in report.issues)
            )
            assert report.capabilities is not None
            self.assertEqual(
                report.capabilities.qualified_signature.status, CapabilityState.FAILED
            )
            self.assertFalse(report.summary.passed)
            policy = build_signoff_policy(profile="fixture")
            self.assertIn(
                "qualified_signature",
                policy.failed_capabilities_blocking_pass(report.capabilities),
            )

    def test_good_envelope_sets_not_verified_capability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            content_path, envelope_path, _ = _write_pair(Path(tmp))
            # Analyze path expects IFC; reuse content path as ifc_path for audit target.
            ifc = content_path
            ids = Path(tmp) / "dummy.ids"
            ids.write_text("<ids/>", encoding="utf-8")
            # Need at least one requirement for analyze path when ids present is ok.
            report = _build_use_case().execute(
                ValidationRequest(
                    request_id="sig-ok",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(text="Wall FireRating == REI 60"),
                    ids_path=ids,
                    signature_envelope_path=envelope_path,
                    required_signer_roles=("author", "reviewer"),
                )
            )
            assert report.capabilities is not None
            self.assertEqual(
                report.capabilities.qualified_signature.status,
                CapabilityState.NOT_VERIFIED,
            )
            reason = report.capabilities.qualified_signature.reason or ""
            self.assertIn("not_verified", reason)
            self.assertNotIn("УКЭП проверена", reason)

    def test_advisory_off_equals_on_summary_passed(self) -> None:
        """Signature audit is deterministic; advisory must not flip summary.passed."""

        with tempfile.TemporaryDirectory() as tmp:
            content_path, envelope_path, _ = _write_pair(Path(tmp))
            ids = Path(tmp) / "dummy.ids"
            ids.write_text("<ids/>", encoding="utf-8")
            request = ValidationRequest(
                request_id="sig-off-on",
                ifc_path=content_path,
                requirement_source=RequirementSource(text="Wall FireRating == REI 60"),
                ids_path=ids,
                signature_envelope_path=envelope_path,
                required_signer_roles=("author", "reviewer"),
            )
            off = _build_use_case().execute(request)
            advisory = (
                ValidationIssue(
                    rule_id="ADVISORY-FAKE",
                    severity=Severity.ERROR,
                    message="advisory noise",
                    category=FindingCategory.IFC_VALIDATION,
                    origin="advisory",
                ),
            )
            on = _build_use_case(advisory_issues=advisory).execute(request)
            self.assertEqual(off.summary.passed, on.summary.passed)

    def test_default_capability_is_missing_non_blocking(self) -> None:
        caps = ReportCapabilities()
        self.assertEqual(caps.qualified_signature.status, CapabilityState.MISSING)
        policy = build_signoff_policy(profile="development")
        self.assertTrue(policy.summary_passed(error_count=0, capabilities=caps))

    def test_failed_qualified_signature_blocks_pass(self) -> None:
        caps = ReportCapabilities(
            qualified_signature=CapabilityStatus(
                CapabilityState.FAILED, "missing_envelope"
            )
        )
        for profile in ("development", "fixture", "samolet_pilot", "production"):
            policy = build_signoff_policy(profile=profile)
            self.assertFalse(policy.summary_passed(error_count=0, capabilities=caps), profile)


if __name__ == "__main__":
    unittest.main()
