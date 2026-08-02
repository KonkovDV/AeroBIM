"""WP-01: runtime baseline completeness and JUnit parsing."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.tools.export_runtime_baseline import (
    completeness_errors,
    export_runtime_baseline,
    parse_pytest_junit,
)


class ParsePytestJunitTests(unittest.TestCase):
    def test_parses_suite_counts(self) -> None:
        xml = """<?xml version="1.0" encoding="utf-8"?>
        <testsuite name="pytest" tests="10" skipped="2" failures="1" errors="0">
        </testsuite>
        """
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "junit.xml"
            path.write_text(xml, encoding="utf-8")
            parsed = parse_pytest_junit(path)
        self.assertEqual(parsed["tests_collected"], 10)
        self.assertEqual(parsed["tests_passed"], 7)
        self.assertEqual(parsed["tests_skipped"], 2)
        self.assertEqual(parsed["tests_failed"], 1)


class CompletenessErrorsTests(unittest.TestCase):
    def _complete(self) -> dict:
        return {
            "schema_version": "1.2.0",
            "commit_sha": "abc123",
            "tree_sha": "def456",
            "backend": {
                "tests_collected": 100,
                "tests_passed": 90,
                "tests_skipped": 8,
                "tests_failed": 0,
            },
            "frontend": {"tests_passed": 29},
            "quality_gates": {
                "ruff": "PASS",
                "mypy": "PASS",
                "pytest": "PASS",
                "vitest": "PASS",
                "build": "PASS",
            },
            "environment": {
                "python_version": "3.12.0",
                "platform": "test",
                "lockfile_sha256": "0" * 64,
            },
            "metrics": {"extraction_macro_f1": 0.86},
        }

    def test_complete_baseline_has_no_errors(self) -> None:
        self.assertEqual(completeness_errors(self._complete()), [])

    def test_unknown_gate_is_incomplete(self) -> None:
        payload = self._complete()
        payload["quality_gates"]["ruff"] = "UNKNOWN"
        errors = completeness_errors(payload)
        self.assertTrue(any("quality_gates.ruff" in e for e in errors))

    def test_null_passed_is_incomplete(self) -> None:
        payload = self._complete()
        payload["backend"]["tests_passed"] = None
        errors = completeness_errors(payload)
        self.assertTrue(any("tests_passed" in e for e in errors))

    def test_zero_passed_is_incomplete(self) -> None:
        payload = self._complete()
        payload["backend"]["tests_passed"] = 0
        errors = completeness_errors(payload)
        self.assertTrue(any("tests_passed is 0" in e for e in errors))


class ExportRuntimeBaselineSchemaTests(unittest.TestCase):
    def test_schema_includes_environment_and_null_counts_by_default(self) -> None:
        backend = Path(__file__).resolve().parents[1]
        baseline = export_runtime_baseline(
            backend_root=backend,
            commit_sha="testsha",
            tree_sha="testtree",
            environment={
                "python_version": "3.12.0",
                "platform": "test",
                "lockfile_sha256": "abc",
            },
        )
        self.assertEqual(baseline["schema_version"], "1.2.0")
        self.assertEqual(baseline["commit_sha"], "testsha")
        self.assertEqual(baseline["tree_sha"], "testtree")
        backend_block = baseline["backend"]
        assert isinstance(backend_block, dict)
        self.assertIsNone(backend_block["tests_passed"])
        self.assertIsNone(backend_block["tests_skipped"])
        self.assertIsNone(backend_block["tests_failed"])
        self.assertIn("environment", baseline)
        self.assertIn("claim_boundary", baseline)
        dumped = json.dumps(baseline)
        self.assertIn("UNKNOWN", dumped)


if __name__ == "__main__":
    unittest.main()
