"""WP-05: deterministic package completeness (fail-closed missing section)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.application.services.capability_policy import build_signoff_policy
from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    GeneratedRemark,
    ReportCapabilities,
    RequirementSource,
    Severity,
    ValidationRequest,
)
from aerobim.domain.package_completeness import (
    CLAIM_BOUNDARY,
    INVENTORY_SCHEMA_V1,
    PackageInventory,
    assess_package_completeness,
)
from aerobim.infrastructure.adapters.json_package_inventory_loader import (
    JsonPackageInventoryLoader,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPLETE_INVENTORY = REPO_ROOT / "samples" / "packages" / "residential-complete-inventory.json"
MISSING_PZ_INVENTORY = REPO_ROOT / "samples" / "packages" / "residential-missing-pz-inventory.json"


class _Empty:
    def extract(self, _source):
        return []

    def synthesize(self, _source):
        return []

    def analyze(self, _source):
        return []

    def validate(self, *_args, **_kwargs):
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


def _build_use_case() -> AnalyzeProjectPackageUseCase:
    return AnalyzeProjectPackageUseCase(
        requirement_extractor=_Empty(),
        narrative_rule_synthesizer=_Empty(),
        drawing_analyzer=_Empty(),
        ifc_validator=_Empty(),
        ids_validator=_Empty(),
        remark_generator=_Remark(),
        audit_report_store=_Store(),
        signoff_profile="fixture",
        package_inventory_loader=JsonPackageInventoryLoader(),
    )


class PackageCompletenessDomainTests(unittest.TestCase):
    def test_missing_mandatory_section_is_precise_error(self) -> None:
        payload = json.loads(MISSING_PZ_INVENTORY.read_text(encoding="utf-8"))
        inventory = PackageInventory.from_mapping(payload)
        report = assess_package_completeness(inventory)
        missing = [i for i in report.issues if i.rule_id == "AEROBIM-PACKAGE-MISSING-SECTION"]
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0].severity, Severity.ERROR)
        self.assertIn("PZ", missing[0].message)
        self.assertEqual(missing[0].target_ref, "PZ")
        self.assertEqual(report.missing_pd_sections, ("PZ",))
        self.assertEqual(report.to_capability_status().status, CapabilityState.FAILED)
        self.assertNotIn("WARNING", missing[0].message)

    def test_complete_inventory_passes(self) -> None:
        payload = json.loads(COMPLETE_INVENTORY.read_text(encoding="utf-8"))
        self.assertEqual(payload.get("schema"), INVENTORY_SCHEMA_V1)
        report = assess_package_completeness(PackageInventory.from_mapping(payload))
        errors = [i for i in report.issues if i.severity is Severity.ERROR]
        self.assertEqual(errors, [])
        self.assertEqual(report.to_capability_status().status, CapabilityState.OK)
        self.assertIn("native DWG", CLAIM_BOUNDARY)

    def test_native_rvt_declared_is_error_not_supported_claim(self) -> None:
        inventory = PackageInventory.from_mapping(
            {
                "schema": INVENTORY_SCHEMA_V1,
                "project_id": "rvt-honesty",
                "mandatory_pd_sections": ["AR"],
                "require_pd_rd_pairing": False,
                "require_specifications": False,
                "require_schedules": False,
                "require_sheet_ciphers": False,
                "artifacts": [
                    {
                        "artifact_id": "pd-ar",
                        "role": "pd_section",
                        "discipline": "AR",
                        "format": "rvt",
                        "cipher": "AR-001",
                    }
                ],
            }
        )
        report = assess_package_completeness(inventory)
        issues = [i for i in report.issues if i.rule_id == "AEROBIM-PACKAGE-UNSUPPORTED-FORMAT"]
        self.assertEqual(len(issues), 1)
        self.assertIn("RVT", issues[0].message.upper())
        self.assertNotIn("rvt_supported", issues[0].message)

    def test_native_dwg_declared_is_error_not_supported_claim(self) -> None:
        inventory = PackageInventory.from_mapping(
            {
                "schema": INVENTORY_SCHEMA_V1,
                "project_id": "dwg-honesty",
                "mandatory_pd_sections": ["AR"],
                "require_pd_rd_pairing": False,
                "require_specifications": False,
                "require_schedules": False,
                "require_sheet_ciphers": False,
                "artifacts": [
                    {
                        "artifact_id": "pd-ar",
                        "role": "pd_section",
                        "discipline": "AR",
                        "format": "dwg",
                        "cipher": "AR-001",
                    }
                ],
            }
        )
        report = assess_package_completeness(inventory)
        dwg_issues = [i for i in report.issues if i.rule_id == "AEROBIM-PACKAGE-UNSUPPORTED-FORMAT"]
        self.assertEqual(len(dwg_issues), 1)
        self.assertIn("native DWG", dwg_issues[0].message)
        self.assertNotIn("DWG-ready", dwg_issues[0].message)

    def test_declared_docx_is_accepted_exchange_format(self) -> None:
        inventory = PackageInventory.from_mapping(
            {
                "schema": INVENTORY_SCHEMA_V1,
                "project_id": "office-honesty",
                "mandatory_pd_sections": ["AR"],
                "require_pd_rd_pairing": False,
                "require_specifications": False,
                "require_schedules": False,
                "require_sheet_ciphers": False,
                "artifacts": [
                    {
                        "artifact_id": "pd-ar-brief",
                        "role": "pd_section",
                        "discipline": "AR",
                        "format": "docx",
                        "cipher": "AR-001",
                    }
                ],
            }
        )
        report = assess_package_completeness(inventory)
        unknown = [i for i in report.issues if i.rule_id == "AEROBIM-PACKAGE-FORMAT-UNKNOWN"]
        unsupported = [
            i for i in report.issues if i.rule_id == "AEROBIM-PACKAGE-UNSUPPORTED-FORMAT"
        ]
        self.assertEqual(unknown, [])
        self.assertEqual(unsupported, [])

    def test_numeric_section_code_does_not_hide_discipline(self) -> None:
        inventory = PackageInventory.from_mapping(
            {
                "schema": INVENTORY_SCHEMA_V1,
                "project_id": "pp87-volume-label",
                "mandatory_pd_sections": ["AR"],
                "require_pd_rd_pairing": False,
                "require_specifications": False,
                "require_schedules": False,
                "require_sheet_ciphers": False,
                "artifacts": [
                    {
                        "artifact_id": "pd-ar",
                        "role": "pd_section",
                        "discipline": "AR",
                        "section_code": "3",
                        "format": "pdf",
                    }
                ],
            }
        )
        report = assess_package_completeness(inventory)
        missing = [i for i in report.issues if i.rule_id == "AEROBIM-PACKAGE-MISSING-SECTION"]
        self.assertEqual(missing, [])
        self.assertEqual(report.missing_pd_sections, ())

    def test_kr_present_does_not_satisfy_mandatory_kzh(self) -> None:
        inventory = PackageInventory.from_mapping(
            {
                "schema": INVENTORY_SCHEMA_V1,
                "project_id": "kr-not-kzh",
                "mandatory_pd_sections": ["AR", "KZH"],
                "require_pd_rd_pairing": False,
                "require_specifications": False,
                "require_schedules": False,
                "require_sheet_ciphers": False,
                "artifacts": [
                    {
                        "artifact_id": "pd-ar",
                        "role": "pd_section",
                        "discipline": "AR",
                        "format": "pdf",
                    },
                    {
                        "artifact_id": "pd-kr",
                        "role": "pd_section",
                        "discipline": "KR",
                        "format": "pdf",
                    },
                ],
            }
        )
        report = assess_package_completeness(inventory)
        missing = [i for i in report.issues if i.rule_id == "AEROBIM-PACKAGE-MISSING-SECTION"]
        notice = [i for i in report.issues if i.rule_id == "AEROBIM-PACKAGE-KR-NOT-KZH"]
        self.assertEqual([i.target_ref for i in missing], ["KZH"])
        self.assertEqual(len(notice), 1)
        self.assertEqual(notice[0].severity, Severity.WARNING)
        self.assertIn("KR does not fill", notice[0].message)
        self.assertEqual(report.to_capability_status().status, CapabilityState.FAILED)

    def test_kr_cipher_cyrillic_alias_is_accepted(self) -> None:
        inventory = PackageInventory.from_mapping(
            {
                "schema": INVENTORY_SCHEMA_V1,
                "project_id": "kr-cipher",
                "mandatory_pd_sections": ["KR"],
                "require_pd_rd_pairing": False,
                "require_specifications": False,
                "require_schedules": False,
                "require_sheet_ciphers": True,
                "artifacts": [
                    {
                        "artifact_id": "pd-kr",
                        "role": "pd_section",
                        "discipline": "KR",
                        "format": "pdf",
                        "cipher": "СИН-КР-01",
                    }
                ],
            }
        )
        report = assess_package_completeness(inventory)
        mismatch = [i for i in report.issues if i.rule_id == "AEROBIM-PACKAGE-CIPHER-MISMATCH"]
        missing = [i for i in report.issues if i.rule_id == "AEROBIM-PACKAGE-MISSING-SECTION"]
        self.assertEqual(mismatch, [])
        self.assertEqual(missing, [])


class PackageCompletenessUseCaseWiringTests(unittest.TestCase):
    def test_missing_section_fixture_fails_analyze(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ifc = Path(tmp) / "model.ifc"
            ifc.write_text("ISO-10303-21;\nEND-ISO-10303-21;\n", encoding="utf-8")
            ids = Path(tmp) / "dummy.ids"
            ids.write_text("<ids/>", encoding="utf-8")
            report = _build_use_case().execute(
                ValidationRequest(
                    request_id="pkg-missing-pz",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(text="Wall FireRating == REI 60"),
                    ids_path=ids,
                    package_inventory_path=MISSING_PZ_INVENTORY,
                    require_package_completeness=True,
                )
            )
            missing = [i for i in report.issues if i.rule_id == "AEROBIM-PACKAGE-MISSING-SECTION"]
            self.assertEqual(len(missing), 1)
            self.assertIn("PZ", missing[0].message)
            assert report.capabilities is not None
            self.assertEqual(
                report.capabilities.package_completeness.status, CapabilityState.FAILED
            )
            self.assertFalse(report.summary.passed)
            policy = build_signoff_policy(profile="fixture")
            self.assertIn(
                "package_completeness",
                policy.failed_capabilities_blocking_pass(report.capabilities),
            )

    def test_complete_inventory_sets_ok_capability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ifc = Path(tmp) / "model.ifc"
            ifc.write_text("ISO-10303-21;\nEND-ISO-10303-21;\n", encoding="utf-8")
            ids = Path(tmp) / "dummy.ids"
            ids.write_text("<ids/>", encoding="utf-8")
            report = _build_use_case().execute(
                ValidationRequest(
                    request_id="pkg-complete",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(text="Wall FireRating == REI 60"),
                    ids_path=ids,
                    package_inventory_path=COMPLETE_INVENTORY,
                    require_package_completeness=True,
                )
            )
            assert report.capabilities is not None
            self.assertEqual(report.capabilities.package_completeness.status, CapabilityState.OK)
            self.assertFalse(
                any(i.rule_id == "AEROBIM-PACKAGE-MISSING-SECTION" for i in report.issues)
            )

    def test_soft_opt_in_skipped_when_not_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ifc = Path(tmp) / "model.ifc"
            ifc.write_text("ISO-10303-21;\nEND-ISO-10303-21;\n", encoding="utf-8")
            ids = Path(tmp) / "dummy.ids"
            ids.write_text("<ids/>", encoding="utf-8")
            report = _build_use_case().execute(
                ValidationRequest(
                    request_id="pkg-skip",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(text="Wall FireRating == REI 60"),
                    ids_path=ids,
                )
            )
            assert report.capabilities is not None
            self.assertEqual(
                report.capabilities.package_completeness.status, CapabilityState.SKIPPED
            )

    def test_failed_package_completeness_blocks_pass_under_hard_profile(self) -> None:
        caps = ReportCapabilities(
            package_completeness=CapabilityStatus(CapabilityState.FAILED, "missing PZ")
        )
        for profile in ("samolet_pilot", "production"):
            policy = build_signoff_policy(profile=profile)
            self.assertIn(
                "package_completeness",
                policy.failed_capabilities_blocking_pass(caps),
            )


class JsonPackageInventoryLoaderTests(unittest.TestCase):
    def test_loader_assesses_fixture(self) -> None:
        loader = JsonPackageInventoryLoader()
        report = loader.assess(MISSING_PZ_INVENTORY)
        self.assertIn("PZ", report.missing_pd_sections)
        self.assertEqual(report.to_capability_status().status, CapabilityState.FAILED)


if __name__ == "__main__":
    unittest.main()
