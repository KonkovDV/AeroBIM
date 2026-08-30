"""Samolet answers 2026-08-25 — upload caps, remark shape, roles, intake honesty."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aerobim.core.config.settings import Settings
from aerobim.core.security.upload_limits import (
    SAMOLET_STATED_MODEL_BYTES,
    SAMOLET_STATED_OFFICE_BYTES,
    classify_upload_kind,
    upload_limit_bytes,
)
from aerobim.domain.auth_roles import HITL_REVIEWER_ROLES, VIEWER_ROLES
from aerobim.domain.models import (
    ComparisonOperator,
    FindingCategory,
    Severity,
    ValidationIssue,
)
from aerobim.domain.samolet_mvp_answers import samolet_mvp_answers_payload
from aerobim.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator


class UploadLimitClassificationTests(unittest.TestCase):
    def test_ifc_is_model_pdf_is_office(self) -> None:
        self.assertEqual(classify_upload_kind("a.ifc"), "model")
        self.assertEqual(classify_upload_kind("note.pdf"), "office")
        self.assertEqual(classify_upload_kind("sheet.xlsx"), "office")

    def test_envelope_caps_typed_limit(self) -> None:
        self.assertEqual(
            upload_limit_bytes(
                "a.ifc",
                max_office_bytes=500_000_000,
                max_model_bytes=1_500_000_000,
                envelope_bytes=16,
            ),
            16,
        )

    def test_office_below_model_cap(self) -> None:
        self.assertEqual(
            upload_limit_bytes(
                "a.pdf",
                max_office_bytes=SAMOLET_STATED_OFFICE_BYTES,
                max_model_bytes=SAMOLET_STATED_MODEL_BYTES,
                envelope_bytes=SAMOLET_STATED_MODEL_BYTES,
            ),
            SAMOLET_STATED_OFFICE_BYTES,
        )


class SettingsUploadLimitTests(unittest.TestCase):
    def test_constructor_envelope_wins_for_existing_tests(self) -> None:
        settings = Settings(
            application_name="aerobim-test",
            environment="test",
            host="127.0.0.1",
            port=8080,
            storage_dir=Path("."),
            debug=True,
            max_upload_bytes=16,
        )
        self.assertEqual(settings.upload_limit_for_filename("pilot.ifc"), 16)

    def test_from_env_pilot_applies_stated_caps(self) -> None:
        env = {
            "AEROBIM_ENV": "development",
            "AEROBIM_SIGNOFF_PROFILE": "samolet_pilot",
            "AEROBIM_LLM_ADVISORY_ENABLED": "false",
        }
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop("AEROBIM_APPLY_SAMOLET_UPLOAD_CAPS", None)
            os.environ.pop("AEROBIM_MAX_OFFICE_BYTES", None)
            os.environ.pop("AEROBIM_MAX_MODEL_BYTES", None)
            os.environ.pop("AEROBIM_MAX_UPLOAD_BYTES", None)
            os.environ.pop("AEROBIM_MAX_IFC_BYTES", None)
            settings = Settings.from_env()
        self.assertEqual(settings.max_office_bytes, SAMOLET_STATED_OFFICE_BYTES)
        self.assertEqual(settings.max_model_bytes, SAMOLET_STATED_MODEL_BYTES)
        self.assertEqual(settings.max_ifc_bytes, 256 * 1024 * 1024)
        self.assertEqual(settings.upload_limit_for_filename("a.pdf"), SAMOLET_STATED_OFFICE_BYTES)
        self.assertEqual(settings.upload_limit_for_filename("a.ifc"), SAMOLET_STATED_MODEL_BYTES)

    def test_from_env_can_disable_stated_caps(self) -> None:
        env = {
            "AEROBIM_ENV": "development",
            "AEROBIM_SIGNOFF_PROFILE": "samolet_pilot",
            "AEROBIM_APPLY_SAMOLET_UPLOAD_CAPS": "0",
            "AEROBIM_LLM_ADVISORY_ENABLED": "false",
        }
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop("AEROBIM_MAX_OFFICE_BYTES", None)
            os.environ.pop("AEROBIM_MAX_MODEL_BYTES", None)
            os.environ.pop("AEROBIM_MAX_UPLOAD_BYTES", None)
            settings = Settings.from_env()
        self.assertEqual(settings.max_office_bytes, 256 * 1024 * 1024)
        self.assertEqual(settings.max_model_bytes, 256 * 1024 * 1024)


class RemarkShapeTests(unittest.TestCase):
    def test_three_part_body_does_not_invent_clause(self) -> None:
        issue = ValidationIssue(
            rule_id="QTO-001",
            severity=Severity.ERROR,
            message="Area mismatch",
            ifc_entity="IFCSPACE",
            category=FindingCategory.IFC_VALIDATION,
            property_set="Qto_SpaceBaseQuantities",
            property_name="NetFloorArea",
            operator=ComparisonOperator.GREATER_OR_EQUAL,
            expected_value="25",
            observed_value="20",
            unit="m2",
            element_guid="guid-1",
            target_ref="Space:A101",
        )
        ru = TemplateRemarkGenerator(locale="ru").generate(issue)
        self.assertIn("Замечание по модели", ru.title)
        self.assertIn("Area mismatch", ru.title)
        self.assertIn("Суть:", ru.body)
        self.assertIn("Норма/СТО:", ru.body)
        self.assertIn("пункт нормы не привязан", ru.body)
        self.assertIn("Локация:", ru.body)
        self.assertIn("GUID guid-1", ru.body)
        self.assertIn("этаж: нет в пространственном индексе", ru.body)
        self.assertIn("ось: нет в пространственном индексе", ru.body)
        self.assertIn("не менее", ru.body)

        bound = ValidationIssue(
            rule_id=issue.rule_id,
            severity=issue.severity,
            message=issue.message,
            ifc_entity=issue.ifc_entity,
            category=issue.category,
            property_set=issue.property_set,
            property_name=issue.property_name,
            operator=issue.operator,
            expected_value=issue.expected_value,
            observed_value=issue.observed_value,
            unit=issue.unit,
            norm_source="СП 63",
            norm_clause="п. 8.1",
        )
        with_clause = TemplateRemarkGenerator(locale="ru").generate(bound)
        self.assertIn("СП 63 п. 8.1", with_clause.body)
        self.assertNotIn("пункт нормы не привязан", with_clause.body)


class RoleAliasTests(unittest.TestCase):
    def test_expert_is_reviewer_user_is_viewer(self) -> None:
        self.assertIn("expert", HITL_REVIEWER_ROLES)
        self.assertIn("aerobim:expert", HITL_REVIEWER_ROLES)
        self.assertIn("user", VIEWER_ROLES)
        self.assertNotIn("user", HITL_REVIEWER_ROLES)
        self.assertNotIn("viewer", HITL_REVIEWER_ROLES)


class SamoletAnswersHonestyTests(unittest.TestCase):
    def _repo(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def test_capabilities_payload_keeps_blockers_open(self) -> None:
        payload = samolet_mvp_answers_payload()
        self.assertFalse(payload["closes_rt001"])
        self.assertFalse(payload["closes_rt002"])
        self.assertFalse(payload["closes_rt003"])
        self.assertFalse(payload["share_ingested_in_git"])
        self.assertTrue(payload["share_url_received"])
        self.assertNotIn("share_url", payload)
        self.assertEqual(payload["checkpoint"], "NO_GO")
        self.assertEqual(payload["native_rvt_nwd"], "not_implemented")
        self.assertTrue(payload["speech_forbid_no_customer_data"])
        self.assertTrue(payload["customer_stated_closed_cloud"])
        self.assertFalse(payload["axis_nearest_grid_intersection"])
        self.assertEqual(payload["peak_packs_per_day_mvp"], "5-10")
        self.assertIn("IfcSpatialIndex", str(payload["remark_shape"]))
        self.assertEqual(payload["native_dwg"], "not_implemented")
        self.assertEqual(payload["native_lir"], "not_implemented")
        self.assertEqual(payload["team_brief_received_at"], "2026-08-26")
        self.assertEqual(
            payload["dataset_classes"],
            ["tz", "dwg", "ifc", "calculations", "scans", "typical_errors"],
        )
        self.assertEqual(payload["raster_scans"], "optional_ocr_not_labeled_corpus")

    def test_answers_doc_and_workplan_stay_no_go(self) -> None:
        repo = self._repo()
        faq = (repo / "docs" / "demo" / "KT3_JURY_FAQ_2026_08_25.md").read_text(encoding="utf-8")
        runbook = (repo / "docs" / "demo" / "KT3_OPERATOR_RUNBOOK_2026_08_25.md").read_text(
            encoding="utf-8"
        )
        workplan = (repo / "docs" / "quality" / "KT3_IN_REPO_WORKPLAN_2026_08_27.md").read_text(
            encoding="utf-8"
        )
        for text in (faq, runbook, workplan):
            self.assertIn("closes_rt001: false", text)
            self.assertIn("NO_GO", text)
            self.assertNotIn("closes_rt001: true", text)

    def test_intake_share_does_not_flip_gates(self) -> None:
        path = self._repo() / "audit" / "evidence" / "customer-intake-gate.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(payload["share_url_received"])
        self.assertIsNone(payload.get("share_url"))
        self.assertFalse(payload["share_ingested_in_git"])
        self.assertFalse(payload["closes_rt001"])
        gates = payload["gates"]
        self.assertFalse(gates["nda_signed"])
        self.assertFalse(gates["customer_package_in_samples_customer"])
        self.assertEqual(payload["status"], "BLOCKED_NO_CUSTOMER_DATA")
        speech = payload.get("speech")
        self.assertIsInstance(speech, dict)
        self.assertTrue(speech["forbid_no_customer_data_phrase"])
        self.assertTrue(speech["channel_received"])
        self.assertFalse(speech["hashed_pack_in_git"])

    def test_catalog_share_metadata_stays_unconfirmed(self) -> None:
        path = self._repo() / "samples" / "benchmarks" / "samolet-typical-errors-catalog.json"
        catalog = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(catalog["customer_confirmed_patterns"], 0)
        self.assertFalse(catalog["customer_share_ingested"])
        self.assertEqual(catalog["catalog_status"], "synthetic-scaffold")
        self.assertNotIn("customer_share_url", catalog)

    def test_working_tree_does_not_republish_share_host(self) -> None:
        """Pack-share host locator must not sit in the public working tree."""

        import sys

        scripts = self._repo() / "scripts"
        sys.path.insert(0, str(scripts))
        try:
            from kitchen_denylist import (  # type: ignore[import-not-found]
                denylist_materialized,
                lint_guard_files_have_no_literals,
                lint_kitchen_tokens,
            )
        finally:
            if sys.path and sys.path[0] == str(scripts):
                sys.path.pop(0)
        if not denylist_materialized():
            self.skipTest(
                "kitchen denylist not materialized (GitHub secrets or .local); "
                "fail-closed production path is unchanged"
            )
        self.assertEqual(lint_kitchen_tokens(), [])
        self.assertEqual(lint_guard_files_have_no_literals(), [])


class SplitUploadApiTests(unittest.TestCase):
    def test_office_cap_rejects_pdf_above_office_limit(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        from aerobim.infrastructure.di.bootstrap import bootstrap_container
        from aerobim.presentation.http.api import create_http_app

        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(
                application_name="aerobim-test",
                environment="test",
                host="127.0.0.1",
                port=8080,
                storage_dir=Path(tmp),
                debug=True,
                allow_anonymous_dev=True,
                max_upload_bytes=10_000,
                max_office_bytes=32,
                max_model_bytes=10_000,
            )
            container = bootstrap_container(settings)
            client = TestClient(create_http_app(container))
            response = client.post(
                "/v1/uploads",
                files={"file": ("note.pdf", b"%PDF-1.4\n" + b"X" * 40, "application/pdf")},
            )
            self.assertEqual(response.status_code, 413, response.text)


if __name__ == "__main__":
    unittest.main()
