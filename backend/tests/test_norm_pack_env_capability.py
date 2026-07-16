from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.core.config.settings import Settings
from aerobim.core.security.path_jail import PathJailError
from aerobim.domain.models import (
    CapabilityState,
    GeneratedRemark,
    RequirementSource,
    ValidationReport,
    ValidationRequest,
)
from aerobim.infrastructure.adapters.json_norm_rule_pack_loader import JsonNormRulePackLoader
from aerobim.infrastructure.di.bootstrap import _resolve_default_norm_pack_path

REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_PACK = REPO_ROOT / "samples" / "rule-packs" / "residential-ar-reference-template.json"


class _Empty:
    def extract(self, _source):
        return []

    def synthesize(self, _source):
        return []

    def analyze(self, _source):
        return []


class _RemarkGenerator:
    def generate(self, issue):
        return GeneratedRemark(title=issue.rule_id, body=issue.message)


class _Store:
    def __init__(self) -> None:
        self.report: ValidationReport | None = None

    def save(self, report: ValidationReport) -> str:
        self.report = report
        return report.report_id

    def get(self, report_id: str) -> ValidationReport | None:
        if self.report is not None and self.report.report_id == report_id:
            return self.report
        return None


def _use_case(default_path: Path | None) -> AnalyzeProjectPackageUseCase:
    empty = _Empty()
    return AnalyzeProjectPackageUseCase(
        requirement_extractor=empty,
        narrative_rule_synthesizer=empty,
        drawing_analyzer=empty,
        ifc_validator=MagicMock(validate=MagicMock(return_value=[])),
        ids_validator=MagicMock(validate=MagicMock(return_value=[])),
        remark_generator=_RemarkGenerator(),
        audit_report_store=_Store(),
        norm_rule_pack_loader=JsonNormRulePackLoader(),
        default_norm_rule_pack_path=default_path,
    )


def _request(*, norm_paths: tuple[Path, ...] = ()) -> ValidationRequest:
    return ValidationRequest(
        request_id="norm-env",
        ifc_path=Path("synthetic.ifc"),
        requirement_source=RequirementSource(),
        norm_rule_pack_paths=norm_paths,
        ids_path=Path("dummy.ids"),  # keeps analysis running with zero norm rules
    )


class NormPackEnvCapabilityTests(unittest.TestCase):
    def test_no_env_and_no_request_is_skipped(self) -> None:
        report = _use_case(None).execute(_request())
        cap = report.capabilities.norm_rule_packs
        self.assertEqual(cap.status, CapabilityState.SKIPPED)

    def test_env_default_loads_and_flags_non_approved(self) -> None:
        report = _use_case(REFERENCE_PACK).execute(_request())
        cap = report.capabilities.norm_rule_packs
        self.assertEqual(cap.status, CapabilityState.OK)
        self.assertEqual(report.summary.requirement_count, 20)
        self.assertIn("env AEROBIM_NORM_RULE_PACK", cap.reason or "")
        self.assertIn("synthetic-template", cap.reason or "")
        self.assertIn("advisory", (cap.reason or "").lower())

    def test_env_default_missing_fails_closed(self) -> None:
        missing = REPO_ROOT / "samples" / "rule-packs" / "does-not-exist.json"
        report = _use_case(missing).execute(_request())
        cap = report.capabilities.norm_rule_packs
        self.assertEqual(cap.status, CapabilityState.FAILED)
        self.assertIn("does-not-exist.json", cap.reason or "")
        # Fail-closed capability must NOT be a silent skip.
        self.assertNotEqual(cap.status, CapabilityState.SKIPPED)
        self.assertFalse(report.summary.passed)

    def test_request_broken_pack_fails_closed_and_blocks_pass(self) -> None:
        missing = REPO_ROOT / "samples" / "rule-packs" / "does-not-exist.json"
        report = _use_case(None).execute(_request(norm_paths=(missing,)))
        cap = report.capabilities.norm_rule_packs
        self.assertEqual(cap.status, CapabilityState.FAILED)
        self.assertIn("request manifest", cap.reason or "")
        self.assertFalse(report.summary.passed)

    def test_no_packs_skipped_does_not_alone_force_fail(self) -> None:
        from aerobim.application.services.signoff_policy import failed_capabilities_blocking_pass

        report = _use_case(None).execute(_request())
        self.assertEqual(report.capabilities.norm_rule_packs.status, CapabilityState.SKIPPED)
        self.assertNotIn("norm_rule_packs", failed_capabilities_blocking_pass(report.capabilities))

    def test_request_paths_take_precedence_over_env_default(self) -> None:
        missing = REPO_ROOT / "samples" / "rule-packs" / "does-not-exist.json"
        report = _use_case(missing).execute(_request(norm_paths=(REFERENCE_PACK,)))
        cap = report.capabilities.norm_rule_packs
        self.assertEqual(cap.status, CapabilityState.OK)
        self.assertIn("request manifest", cap.reason or "")


class NormPackSettingsAndResolverTests(unittest.TestCase):
    def test_settings_reads_env_var(self) -> None:
        with patch.dict("os.environ", {"AEROBIM_NORM_RULE_PACK": "packs/customer-ar.json"}):
            settings = Settings.from_env()
        self.assertEqual(settings.norm_rule_pack_path, "packs/customer-ar.json")

    def test_settings_default_is_none(self) -> None:
        with patch.dict("os.environ", {}, clear=False):
            import os

            os.environ.pop("AEROBIM_NORM_RULE_PACK", None)
            settings = Settings.from_env()
        self.assertIsNone(settings.norm_rule_pack_path)

    def test_resolver_returns_none_when_unset(self) -> None:
        settings = _settings_with(norm_path=None)
        self.assertIsNone(_resolve_default_norm_pack_path(settings))

    def test_resolver_resolves_relative_within_jail(self) -> None:
        settings = _settings_with(norm_path="packs/customer-ar.json")
        resolved = _resolve_default_norm_pack_path(settings)
        self.assertIsNotNone(resolved)
        assert resolved is not None
        # Path separators are OS-specific; compare Path parts, not raw string suffix.
        self.assertEqual(resolved.parts[-2:], ("packs", "customer-ar.json"))

    def test_resolver_rejects_path_traversal(self) -> None:
        settings = _settings_with(norm_path="../escape.json")
        with self.assertRaises(PathJailError):
            _resolve_default_norm_pack_path(settings)


def _settings_with(*, norm_path: str | None) -> Settings:
    return Settings(
        application_name="test",
        environment="development",
        host="127.0.0.1",
        port=8080,
        storage_dir=Path("var/reports"),
        debug=True,
        norm_rule_pack_path=norm_path,
    )


if __name__ == "__main__":
    unittest.main()
