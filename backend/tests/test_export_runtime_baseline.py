"""WP-01: runtime baseline completeness and JUnit parsing."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.tools.export_runtime_baseline import (
    _check_architecture_inventory,
    _check_documented_env_sets,
    _live_architecture_inventory,
    completeness_errors,
    export_runtime_baseline,
    parse_pytest_junit,
)


class ParseVitestJsonTests(unittest.TestCase):
    def test_parses_vitest_counts(self) -> None:
        payload = {
            "numTotalTests": 32,
            "numPassedTests": 29,
            "numFailedTests": 1,
            "numPendingTests": 2,
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vitest.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            from aerobim.tools.export_runtime_baseline import parse_vitest_json

            parsed = parse_vitest_json(path)
        self.assertEqual(parsed["tests_passed"], 29)
        self.assertEqual(parsed["tests_failed"], 1)
        self.assertEqual(parsed["tests_skipped"], 2)


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
            "schema_version": "1.3.0",
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
                "ruff": {"status": "PASS"},
                "mypy": {"status": "PASS"},
                "pytest": {"status": "PASS"},
                "vitest": {"status": "PASS"},
                "build": {"status": "PASS"},
            },
            "environment": {
                "python_version": "3.12.0",
                "platform": "test",
                "lockfile_sha256": "0" * 64,
            },
            "metrics": {"extraction_macro_f1": 0.86},
        }

    def test_complete_baseline_has_no_errors(self) -> None:
        payload = self._complete()
        payload["publishable"] = True
        payload["artifact_completeness"] = "full"
        payload["working_tree_clean"] = True
        self.assertEqual(completeness_errors(payload), [])

    def test_unknown_gate_is_incomplete(self) -> None:
        payload = self._complete()
        payload["quality_gates"]["ruff"] = {"status": "UNKNOWN", "reason": "skipped"}
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
        self.assertEqual(baseline["schema_version"], "1.3.0")
        self.assertEqual(baseline["commit_sha"], "testsha")
        self.assertEqual(baseline["tree_sha"], "testtree")
        backend_block = baseline["backend"]
        assert isinstance(backend_block, dict)
        self.assertIsNone(backend_block["tests_passed"])
        self.assertIsNone(backend_block["tests_skipped"])
        self.assertIsNone(backend_block["tests_failed"])
        self.assertIn("environment", baseline)
        self.assertIn("claim_boundary", baseline)
        self.assertIn("documented_env_vars", baseline)
        self.assertIsInstance(baseline["documented_env_vars"], list)
        self.assertIn("architecture_inventory", baseline)
        inv = baseline["architecture_inventory"]
        assert isinstance(inv, dict)
        for key in ("public_domain_protocols", "adapter_modules", "di_tokens"):
            self.assertIsInstance(inv[key], int)
            self.assertGreater(inv[key], 0)
        dumped = json.dumps(baseline)
        self.assertIn("gate not executed", dumped)
        self.assertFalse(baseline.get("publishable"))


class DocumentedEnvSetTests(unittest.TestCase):
    def test_marker_noise_not_treated_as_env_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "docs" / "evidence").mkdir(parents=True)
            readme = (
                "## Configuration\n\n"
                "| Variable | Default | Description |\n"
                "|---|---|---|\n"
                "| `AEROBIM_HOST` | `127.0.0.1` | Bind |\n"
                "| `AEROBIM_PORT` | `8080` | Port |\n"
                "\n"
                "<!-- AEROBIM_DOCUMENTED_ENV:BEGIN -->\n"
                "AEROBIM_HOST\n"
                "AEROBIM_PORT\n"
                "<!-- AEROBIM_DOCUMENTED_ENV:END -->\n"
                "\n## Project Structure\n"
            )
            (repo / "README.md").write_text(readme, encoding="utf-8")
            (repo / "README.ru.md").write_text(readme, encoding="utf-8")
            errors = _check_documented_env_sets(repo)
            self.assertEqual(errors, [])

    def test_equal_counts_different_names_fail_with_symdiff(self) -> None:
        """Count equality must not pass — sets must match (symmetric difference)."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "docs" / "evidence").mkdir(parents=True)
            en = (
                "## Configuration\n\n"
                "| Variable | Default | Description |\n"
                "|---|---|---|\n"
                "| `AEROBIM_HOST` | `127.0.0.1` | Bind |\n"
                "| `AEROBIM_PORT` | `8080` | Port |\n"
                "\n"
                "<!-- AEROBIM_DOCUMENTED_ENV:BEGIN -->\n"
                "AEROBIM_HOST\n"
                "AEROBIM_PORT\n"
                "<!-- AEROBIM_DOCUMENTED_ENV:END -->\n"
                "\n## Other\n"
            )
            ru = (
                "## Configuration\n\n"
                "| Variable | Default | Description |\n"
                "|---|---|---|\n"
                "| `AEROBIM_HOST` | `127.0.0.1` | Bind |\n"
                "| `AEROBIM_DEBUG` | `false` | Debug |\n"
                "\n"
                "<!-- AEROBIM_DOCUMENTED_ENV:BEGIN -->\n"
                "AEROBIM_HOST\n"
                "AEROBIM_DEBUG\n"
                "<!-- AEROBIM_DOCUMENTED_ENV:END -->\n"
                "\n## Other\n"
            )
            (repo / "README.md").write_text(en, encoding="utf-8")
            (repo / "README.ru.md").write_text(ru, encoding="utf-8")
            errors = _check_documented_env_sets(repo)
            self.assertTrue(errors, "equal cardinality with different names must fail")
            blob = " ".join(errors)
            self.assertIn("symmetric_difference", blob)
            self.assertIn("AEROBIM_PORT", blob)
            self.assertIn("AEROBIM_DEBUG", blob)


class ArchitectureInventoryTests(unittest.TestCase):
    def test_live_inventory_matches_readme_needles(self) -> None:
        backend = Path(__file__).resolve().parents[1]
        repo = backend.parent
        live = _live_architecture_inventory(repo)
        self.assertEqual(live["public_domain_protocols"], 48)
        self.assertEqual(live["adapter_modules"], 72)
        self.assertEqual(live["di_tokens"], 63)
        # Without architecture_inventory in a temp artifact, check still validates README.
        errors = _check_architecture_inventory(repo)
        # Committed artifact must include live inventory after this gate lands.
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
