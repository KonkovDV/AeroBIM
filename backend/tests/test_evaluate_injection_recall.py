"""evaluate_injection_recall: CONTROL-diff attribution and Wilson aggregate."""

from __future__ import annotations

import unittest
from collections import Counter

from aerobim.tools.evaluate_injection_recall import (
    diff_issue_multisets,
    evaluate_manifest,
    issue_key,
)


def _issue(rule: str, observed: str = "1", guid: str = "g1") -> dict[str, str]:
    return {
        "rule_id": rule,
        "ifc_entity": "IFCWALL",
        "target_ref": "ALL",
        "property_name": "FireRating",
        "observed_value": observed,
        "element_guid": guid,
    }


def _manifest(classes: list[str], applied: bool = True) -> dict[str, object]:
    variants = [
        {
            "class": name,
            "applied": applied if name != "CONTROL" else True,
            "locator": "model.ifc" if name != "CONTROL" else None,
            "note": "unmutated-control" if name == "CONTROL" else "mutated",
        }
        for name in classes
    ]
    return {"artifact": "injection_manifest", "seed": 20260824, "variants": variants}


class IssueMultisetDiffTests(unittest.TestCase):
    def test_novel_and_vanished_are_counter_differences(self) -> None:
        baseline = Counter({issue_key(_issue("A")): 2, issue_key(_issue("B")): 1})
        variant = Counter({issue_key(_issue("A")): 1, issue_key(_issue("C")): 3})
        novel, vanished = diff_issue_multisets(baseline, variant)
        self.assertEqual(sum(novel.values()), 3)
        self.assertEqual(sum(vanished.values()), 2)

    def test_issue_key_ignores_message_wording(self) -> None:
        left = {**_issue("A"), "message": "wording one"}
        right = {**_issue("A"), "message": "wording two"}
        self.assertEqual(issue_key(left), issue_key(right))


class EvaluateManifestTests(unittest.TestCase):
    def test_killed_only_when_output_changes(self) -> None:
        manifest = _manifest(["CONTROL", "AREA_MISMATCH", "LEVEL_MISMATCH"])
        issues = {
            "CONTROL": [_issue("BASE")],
            "AREA_MISMATCH": [_issue("BASE"), _issue("NEW")],
            "LEVEL_MISMATCH": [_issue("BASE")],
        }
        result = evaluate_manifest(manifest, issues)
        rows = {row["class"]: row for row in result["rows"]}
        self.assertTrue(rows["AREA_MISMATCH"]["killed"])
        self.assertEqual(rows["AREA_MISMATCH"]["novel_issues"], 1)
        self.assertFalse(rows["LEVEL_MISMATCH"]["killed"])
        self.assertEqual(result["aggregate"]["killed"], 1)
        self.assertEqual(result["aggregate"]["trials"], 2)
        self.assertAlmostEqual(result["aggregate"]["recall_point"], 0.5)
        self.assertTrue(result["aggregate"]["wilson_95"]["defined"])
        self.assertLess(result["aggregate"]["wilson_95"]["lower"], 0.5)

    def test_vanished_issue_counts_as_killed_with_direction(self) -> None:
        manifest = _manifest(["CONTROL", "MISSING_ELEMENT"])
        issues = {
            "CONTROL": [_issue("BASE"), _issue("GONE")],
            "MISSING_ELEMENT": [_issue("BASE")],
        }
        result = evaluate_manifest(manifest, issues)
        row = result["rows"][0]
        self.assertTrue(row["killed"])
        self.assertEqual(row["vanished_issues"], 1)
        self.assertEqual(row["novel_issues"], 0)

    def test_not_applied_and_control_leave_denominator(self) -> None:
        manifest = _manifest(["CONTROL", "AREA_MISMATCH", "IDS_VIOLATION"], applied=True)
        manifest["variants"][2]["applied"] = False  # type: ignore[index]
        manifest["variants"][2]["note"] = "no-ids-token"  # type: ignore[index]
        issues = {
            "CONTROL": [_issue("BASE")],
            "AREA_MISMATCH": [_issue("BASE"), _issue("NEW")],
            "IDS_VIOLATION": [_issue("BASE")],
        }
        result = evaluate_manifest(manifest, issues)
        self.assertEqual(result["aggregate"]["trials"], 1)
        self.assertEqual(result["aggregate"]["killed"], 1)
        self.assertEqual(result["not_applied_classes"], ["IDS_VIOLATION"])

    def test_missing_control_baseline_fails_closed(self) -> None:
        manifest = _manifest(["AREA_MISMATCH"])
        with self.assertRaises(ValueError):
            evaluate_manifest(manifest, {"AREA_MISMATCH": [_issue("X")]})

    def test_analyze_error_counts_as_killed_fail_closed(self) -> None:
        manifest = _manifest(["CONTROL", "MISSING_ELEMENT"])
        issues = {"CONTROL": [_issue("BASE")], "MISSING_ELEMENT": []}
        result = evaluate_manifest(
            manifest, issues, {"MISSING_ELEMENT": "IfcOpenShellError: parse"}
        )
        row = result["rows"][0]
        self.assertTrue(row["killed"])
        self.assertIn("IfcOpenShellError", row["analyze_error"])
        self.assertEqual(result["aggregate"]["killed"], 1)

    def test_zero_applied_marks_recall_undefined(self) -> None:
        manifest = _manifest(["CONTROL", "IDS_VIOLATION"])
        manifest["variants"][1]["applied"] = False  # type: ignore[index]
        result = evaluate_manifest(manifest, {"CONTROL": [], "IDS_VIOLATION": []})
        self.assertFalse(result["aggregate"]["wilson_95"]["defined"])
        self.assertIsNone(result["aggregate"]["recall_point"])


if __name__ == "__main__":
    unittest.main()
