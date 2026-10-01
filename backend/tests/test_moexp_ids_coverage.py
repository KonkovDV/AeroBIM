from __future__ import annotations

import unittest
from pathlib import Path

from aerobim.infrastructure.adapters.ifc_tester_ids_validator import IfcTesterIdsValidator
from aerobim.infrastructure.adapters.xml_ids_document_auditor import XmlIdsDocumentAuditor
from aerobim.tools.export_moexp_ids_coverage import (
    KIND_ATTRIBUTES,
    KIND_CLASSIFICATION,
    KIND_OTHER,
    STATUS_FAIL,
    STATUS_LOAD_ERROR,
    STATUS_PASS,
    STATUS_UNKNOWN,
    STATUS_UNSUPPORTED,
    attach_by_kind,
    build_moexp_ids_coverage,
    classify_ids_kind,
    classify_specification,
    default_fixture_ifc,
    default_pack_dir,
    discover_ids,
    evaluate_ids_file,
    render_moexp_ids_coverage_markdown,
    specification_row_from_reporter,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


class MoexpIdsCoverageUnitTests(unittest.TestCase):
    def test_classify_priority(self) -> None:
        self.assertEqual(
            classify_specification(unsupported=True, load_error=None, spec_passed=True),
            STATUS_UNSUPPORTED,
        )
        self.assertEqual(
            classify_specification(unsupported=False, load_error="boom", spec_passed=True),
            STATUS_LOAD_ERROR,
        )
        self.assertEqual(
            classify_specification(unsupported=False, load_error=None, spec_passed=True),
            STATUS_PASS,
        )
        self.assertEqual(
            classify_specification(unsupported=False, load_error=None, spec_passed=False),
            STATUS_FAIL,
        )
        self.assertEqual(
            classify_specification(unsupported=False, load_error=None, spec_passed=None),
            STATUS_UNKNOWN,
        )

    def test_missing_reporter_status_is_not_a_pass(self) -> None:
        row = specification_row_from_reporter({"name": "Drift"})
        self.assertIsNone(row["passed_on_fixture"])
        self.assertEqual(row["status"], STATUS_UNKNOWN)
        self.assertEqual(row["status_drift"], "missing_or_null_status")

    def test_string_false_reporter_status_is_not_a_pass(self) -> None:
        row = specification_row_from_reporter({"name": "Drift", "status": "false"})
        self.assertIsNone(row["passed_on_fixture"])
        self.assertEqual(row["status"], STATUS_UNKNOWN)
        self.assertEqual(row["status_drift"], "non_bool_status")

    def test_bool_true_reporter_status_is_pass(self) -> None:
        row = specification_row_from_reporter({"name": "Ok", "status": True})
        self.assertIs(row["passed_on_fixture"], True)
        self.assertEqual(row["status"], STATUS_PASS)
        self.assertNotIn("status_drift", row)

    def test_no_ids_status_true_default_in_backend_src(self) -> None:
        root = Path(__file__).resolve().parents[1] / "src"
        pattern = 'get("status"' + ", True)"
        alt = "get('status'" + ", True)"
        hits: list[str] = []
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if pattern in text or alt in text:
                hits.append(str(path.relative_to(root)))
        self.assertEqual(hits, [])

    def test_classify_ids_kind_from_official_filename(self) -> None:
        self.assertEqual(
            classify_ids_kind("IDS_v1.0_Требования_МОГЭ_к_ЦИМ_АР_v3.2.ids"),
            KIND_ATTRIBUTES,
        )
        self.assertEqual(
            classify_ids_kind("IDS_v1.1_Проверка_КСИ_элементов_ЦИМ_МОГЭ_АР_v3.2.ids"),
            KIND_CLASSIFICATION,
        )
        self.assertEqual(classify_ids_kind("notes.txt"), KIND_OTHER)

    def test_attach_by_kind_splits_without_rerun(self) -> None:
        payload = attach_by_kind(
            {
                "summary": {},
                "files": [
                    {
                        "file_name": "IDS_v1.0_Требования_МОГЭ_к_ЦИМ_АР_v3.2.ids",
                        "specification_count": 10,
                        "counts": {
                            STATUS_PASS: 0,
                            STATUS_FAIL: 10,
                            STATUS_UNSUPPORTED: 0,
                            STATUS_LOAD_ERROR: 0,
                        },
                    },
                    {
                        "file_name": "IDS_v1.1_Проверка_КСИ_элементов_ЦИМ_МОГЭ_АР_v3.2.ids",
                        "specification_count": 8,
                        "counts": {
                            STATUS_PASS: 0,
                            STATUS_FAIL: 8,
                            STATUS_UNSUPPORTED: 0,
                            STATUS_LOAD_ERROR: 0,
                        },
                    },
                ],
            }
        )
        by_kind = payload["summary"]["by_kind"]
        self.assertEqual(by_kind[KIND_ATTRIBUTES]["specifications"], 10)
        self.assertEqual(by_kind[KIND_CLASSIFICATION]["specifications"], 8)
        self.assertEqual(payload["schema_version"], "1.2.0")
        self.assertIn("content_sha256", payload)

    def test_render_states_boundaries(self) -> None:
        md = render_moexp_ids_coverage_markdown(
            {
                "claim_level": "official_ids_engine_coverage",
                "customer_accuracy_not_established": True,
                "closes_rt002_customer_profile": False,
                "claim_boundary": "not product accuracy",
                "source_page": "https://www.moexp.ru/services/tekhnologii-informatsionnogo-modelirovaniya/",
                "summary": {
                    "ids_file_count": 1,
                    "specification_count": 2,
                    "executable": 2,
                    "executable_pass_on_fixture": 0,
                    "executable_fail_on_fixture": 2,
                    "unsupported": 0,
                    "load_error": 0,
                    "unknown_or_skipped": 0,
                    "by_domain": {
                        "oks": {
                            "files": 1,
                            "specifications": 2,
                            "executable_pass_on_fixture": 0,
                            "executable_fail_on_fixture": 2,
                            "unsupported": 0,
                            "load_error": 0,
                        }
                    },
                    "by_kind": {
                        "attributes": {
                            "files": 1,
                            "specifications": 2,
                            "executable_pass_on_fixture": 0,
                            "executable_fail_on_fixture": 2,
                            "unsupported": 0,
                            "load_error": 0,
                        }
                    },
                },
                "icmm_note": "ICMM 3.3 is PDF-only",
                "generated_at": "2026-08-13T00:00:00+00:00",
                "content_sha256": "abc",
                "machine": {"system": "test"},
            }
        )
        self.assertIn("moexp.ru", md)
        self.assertIn("not product accuracy", md)
        self.assertIn("closes_rt002_customer_profile:** `False`", md)
        self.assertIn("By pack kind", md)
        self.assertIn("| attributes |", md)
        self.assertIn("Unknown / skipped status", md)


class MoexpIdsPackPresenceTests(unittest.TestCase):
    def test_official_pack_is_present(self) -> None:
        pack = default_pack_dir(_repo_root())
        files = discover_ids(pack)
        self.assertGreaterEqual(len(files), 24)
        domains = {path.parent.name for path in files}
        self.assertEqual(domains, {"ad-uds", "nis", "oks"})
        source = pack.parent / "SOURCE.md"
        self.assertTrue(source.is_file())
        text = source.read_text(encoding="utf-8")
        self.assertIn("moexp.ru/services/tekhnologii-informatsionnogo-modelirovaniya", text)


class MoexpIdsIfcTesterLiveTests(unittest.TestCase):
    def test_smallest_official_ids_runs_and_emits_issue_on_fixture(self) -> None:
        root = _repo_root()
        pack = default_pack_dir(root)
        ifc = default_fixture_ifc(root)
        smallest = min(discover_ids(pack), key=lambda path: path.stat().st_size)
        auditor = XmlIdsDocumentAuditor()
        row = evaluate_ids_file(smallest, ifc_path=ifc, auditor=auditor)
        self.assertIsNone(row["load_error"])
        self.assertEqual(row["unsupported_facet_count"], 0)
        self.assertGreaterEqual(len(row["specifications"]), 1)
        statuses = {spec["status"] for spec in row["specifications"]}
        self.assertTrue(statuses <= {STATUS_PASS, STATUS_FAIL})
        issues = IfcTesterIdsValidator().validate(smallest, ifc)
        self.assertIsInstance(issues, list)
        if STATUS_FAIL in statuses:
            self.assertGreater(len(issues), 0)

    def test_build_payload_from_one_file_keeps_honesty_flags(self) -> None:
        root = _repo_root()
        pack = default_pack_dir(root)
        ifc = default_fixture_ifc(root)
        smallest = min(discover_ids(pack), key=lambda path: path.stat().st_size)
        auditor = XmlIdsDocumentAuditor()
        row = evaluate_ids_file(smallest, ifc_path=ifc, auditor=auditor)
        coverage = build_moexp_ids_coverage(pack_dir=pack, ifc_path=ifc, files=[row])
        self.assertEqual(coverage["claim_level"], "official_ids_engine_coverage")
        self.assertTrue(coverage["customer_accuracy_not_established"])
        self.assertFalse(coverage["closes_rt002_customer_profile"])
        self.assertTrue(coverage["public_moexp_ids_present"])
        self.assertIn("content_sha256", coverage)
        self.assertEqual(coverage["summary"]["ids_file_count"], 1)


if __name__ == "__main__":
    unittest.main()
