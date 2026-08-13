"""Stale-norm citation warnings (GOST R 21.101-2020 superseded 2026-04-01)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from aerobim.domain.package_completeness import (
    INVENTORY_SCHEMA_V1,
    PackageInventory,
    assess_package_completeness,
)
from aerobim.domain.stale_norm_citations import (
    RULE_SUPERSEDED,
    CitingSource,
    NormDocument,
    collect_stale_citation_issues,
    warn_if_using_superseded_edition,
)

REPO = Path(__file__).resolve().parents[2]
CATALOG = REPO / "samples" / "config" / "norm-citation-catalog.json"
SOURCES = REPO / "samples" / "config" / "norm-citation-sources.json"


def _quiet_inventory(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": INVENTORY_SCHEMA_V1,
        "project_id": "t",
        "mandatory_pd_sections": [],
        "require_pd_rd_pairing": False,
        "require_specifications": False,
        "require_schedules": False,
        "require_sheet_ciphers": False,
        "check_technical_spec_floor_partition_topics": False,
        "check_unjustified_pd_calculations": False,
        "artifacts": [],
    }
    payload.update(overrides)
    return payload


class WarnIfUsingSupersededEditionTests(unittest.TestCase):
    def test_historical_pack_before_cutoff_is_silent(self) -> None:
        self.assertIsNone(
            warn_if_using_superseded_edition(
                edition="21.101-2020",
                package_developed_on="2026-03-31",
            )
        )

    def test_pack_after_cutoff_still_labeled_2020_warns(self) -> None:
        issue = warn_if_using_superseded_edition(
            edition="21.101-2020",
            package_developed_on="2026-05-01",
        )
        assert issue is not None
        self.assertEqual(issue.rule_id, RULE_SUPERSEDED)
        self.assertEqual(issue.expected_value, "21.101-2026")

    def test_missing_developed_on_with_2020_warns(self) -> None:
        issue = warn_if_using_superseded_edition(
            edition="21.101-2020",
            package_developed_on=None,
        )
        self.assertIsNotNone(issue)

    def test_2026_label_is_silent(self) -> None:
        self.assertIsNone(
            warn_if_using_superseded_edition(
                edition="21.101-2026",
                package_developed_on="2026-05-01",
            )
        )


class CatalogScanTests(unittest.TestCase):
    def test_moscow_agr_citation_warns(self) -> None:
        documents = tuple(
            NormDocument.from_mapping(item)
            for item in json.loads(CATALOG.read_text(encoding="utf-8"))["documents"]
        )
        sources = tuple(
            CitingSource.from_mapping(item)
            for item in json.loads(SOURCES.read_text(encoding="utf-8"))["sources"]
        )
        issues = collect_stale_citation_issues(documents, sources)
        self.assertTrue(issues)
        self.assertEqual(issues[0].rule_id, RULE_SUPERSEDED)
        self.assertIn("21.101-2020", issues[0].observed_value or "")

    def test_citation_before_replacement_date_is_silent(self) -> None:
        documents = (
            NormDocument(
                doc_id="GOST_R_21.101-2020",
                aliases=("21.101-2020",),
                status="superseded",
                replaced_by="GOST_R_21.101-2026",
                replaced_on="2026-04-01",
            ),
        )
        sources = (
            CitingSource(
                source_id="old",
                title="Draft before cutoff",
                cites=("21.101-2020",),
                as_of="2026-03-01",
            ),
        )
        self.assertEqual(collect_stale_citation_issues(documents, sources), ())


class PackageCompletenessStaleEditionTests(unittest.TestCase):
    def test_explicit_2020_after_cutoff_emits_warning_not_error(self) -> None:
        inventory = PackageInventory.from_mapping(
            _quiet_inventory(
                documentation_standard_edition="21.101-2020",
                package_developed_on="2026-05-01",
            )
        )
        report = assess_package_completeness(inventory)
        stale = [issue for issue in report.issues if issue.rule_id == RULE_SUPERSEDED]
        self.assertEqual(len(stale), 1)
        self.assertFalse(any(issue.severity.value == "error" for issue in report.issues))
        self.assertEqual(report.to_capability_status().status.value, "ok")


if __name__ == "__main__":
    unittest.main()
