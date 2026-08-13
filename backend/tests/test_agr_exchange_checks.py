"""AGR exchange-shape checks (class 1). Not moscow_agr profile."""

from __future__ import annotations

import unittest
from pathlib import Path

from aerobim.domain.agr_exchange_checks import (
    RULE_FILENAME,
    RULE_PROXY,
    RULE_SCHEMA,
    RULE_VIEW,
    collect_agr_exchange_issues,
    split_five_field_filename,
)
from aerobim.domain.ids_schema_gate import parse_ifc_view_definition
from aerobim.tools.run_agr_exchange_fixture import run_manifest

REPO = Path(__file__).resolve().parents[2]
MANIFEST = REPO / "samples" / "agr" / "exchange-fixture-manifest.json"
RV = REPO / "samples" / "ifc" / "wall-ifc4-referenceview.ifc"
PROXY = REPO / "samples" / "ifc" / "wall-with-building-element-proxy.ifc"
DTV = REPO / "samples" / "ifc" / "wall-pset-qto-pass.ifc"


class FilenameShapeTests(unittest.TestCase):
    def test_five_fields_with_inner_dash(self) -> None:
        parts = split_five_field_filename("MSK_AGR_AR-01_IFC4-RV_20260814.ifc")
        self.assertEqual(parts, ("MSK", "AGR", "AR-01", "IFC4-RV", "20260814"))

    def test_too_few_fields(self) -> None:
        self.assertIsNone(split_five_field_filename("MSK_AGR.ifc"))


class HeaderAndProxyTests(unittest.TestCase):
    def test_reference_view_parsed(self) -> None:
        header = RV.read_text(encoding="utf-8")
        self.assertEqual(parse_ifc_view_definition(header), "ReferenceView")

    def test_pass_ifc4_referenceview(self) -> None:
        text = RV.read_text(encoding="utf-8")
        issues = collect_agr_exchange_issues(
            filename="MSK_AGR_AR-01_IFC4-RV_20260814.ifc",
            header_text=text,
            body_text=text,
            size_bytes=len(text.encode("utf-8")),
        )
        self.assertEqual(issues, ())

    def test_design_transfer_view_fails(self) -> None:
        text = DTV.read_text(encoding="utf-8")
        issues = collect_agr_exchange_issues(
            filename="MSK_AGR_AR-01_IFC4-RV_20260814.ifc",
            header_text=text,
            body_text=text,
            size_bytes=100,
        )
        self.assertEqual([issue.rule_id for issue in issues], [RULE_VIEW])

    def test_proxy_fails(self) -> None:
        text = PROXY.read_text(encoding="utf-8")
        issues = collect_agr_exchange_issues(
            filename="MSK_AGR_AR-01_IFC4-RV_20260814.ifc",
            header_text=text,
            body_text=text,
            size_bytes=100,
        )
        self.assertEqual([issue.rule_id for issue in issues], [RULE_PROXY])

    def test_colon_in_filename_fails(self) -> None:
        text = RV.read_text(encoding="utf-8")
        issues = collect_agr_exchange_issues(
            filename="bad:name.ifc",
            header_text=text,
            body_text=text,
            size_bytes=100,
        )
        self.assertIn(RULE_FILENAME, [issue.rule_id for issue in issues])

    def test_ifc4x3_fails_schema_only_when_view_ok(self) -> None:
        text = (REPO / "samples" / "ifc" / "wall-pset-ifc4x3.ifc").read_text(encoding="utf-8")
        issues = collect_agr_exchange_issues(
            filename="MSK_AGR_AR-01_IFC4-RV_20260814.ifc",
            header_text=text,
            body_text=text,
            size_bytes=100,
        )
        self.assertEqual([issue.rule_id for issue in issues], [RULE_SCHEMA])


class ManifestRunTests(unittest.TestCase):
    def test_manifest_expectations_match(self) -> None:
        payload = run_manifest(MANIFEST, root=REPO)
        self.assertEqual(payload["summary"]["case_count"], 5)
        self.assertEqual(
            payload["summary"]["cases_matching_expect"],
            payload["summary"]["case_count"],
        )


if __name__ == "__main__":
    unittest.main()
