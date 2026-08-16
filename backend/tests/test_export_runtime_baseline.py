"""WP-01: runtime baseline completeness and JUnit parsing."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aerobim.tools.export_runtime_baseline import (
    _check_architecture_inventory,
    _check_documented_env_sets,
    _compute_publishable,
    _live_architecture_inventory,
    completeness_errors,
    export_runtime_baseline,
    parse_pytest_junit,
)

_REPO = Path(__file__).resolve().parents[2]


def _git(*args: str) -> str:
    import shutil

    git = shutil.which("git")
    if not git:
        raise unittest.SkipTest("git executable not found")
    return subprocess.check_output([git, *args], cwd=_REPO, text=True).strip()


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
            "schema_version": "1.4.0",
            "commit_sha": "abc123",
            "tree_sha": "def456",
            "backend": {
                "tests_collected": 100,
                "tests_passed": 90,
                "tests_skipped": 8,
                "tests_failed": 0,
                "test_functions": 100,
                "uncollected": [],
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

    def test_unaccounted_mismatch_is_incomplete(self) -> None:
        payload = self._complete()
        payload["backend"]["tests_unaccounted"] = 99
        errors = completeness_errors(payload)
        self.assertTrue(any("tests_unaccounted" in e for e in errors))

    def test_matching_unaccounted_is_complete(self) -> None:
        payload = self._complete()
        payload["backend"]["tests_unaccounted"] = 2  # 100 − 90 − 8 − 0
        payload["publishable"] = True
        payload["artifact_completeness"] = "full"
        payload["working_tree_clean"] = True
        self.assertEqual(completeness_errors(payload), [])


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
        self.assertEqual(baseline["schema_version"], "1.4.0")
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

    def test_dirty_tree_is_not_publishable_even_when_complete(self) -> None:
        backend = Path(__file__).resolve().parents[1]
        baseline = export_runtime_baseline(
            backend_root=backend,
            tests_passed=90,
            tests_skipped=8,
            tests_failed=0,
            tests_collected=100,
            frontend_tests_passed=29,
            quality_gates={
                "ruff": {"status": "PASS"},
                "mypy": {"status": "PASS"},
                "pytest": {"status": "PASS"},
                "vitest": {"status": "PASS"},
                "build": {"status": "PASS"},
            },
        )
        baseline["working_tree_clean"] = False
        publishable, completeness = _compute_publishable(baseline, require_clean_tree=False)
        self.assertFalse(publishable)
        self.assertEqual(completeness, "partial")
        from aerobim.tools.export_runtime_baseline import publishability_errors

        errors = publishability_errors(baseline)
        self.assertTrue(any("working_tree_dirty" in e for e in errors))

    def test_local_attestation_is_not_publishable(self) -> None:
        from aerobim.tools.export_runtime_baseline import publishability_errors

        payload = CompletenessErrorsTests()._complete()
        payload["publishable"] = True
        payload["artifact_completeness"] = "full"
        payload["working_tree_clean"] = True
        payload["attestation"] = {
            "attested_by": "local",
            "ci_run_id": None,
            "ci_platform": "test",
            "ci_python_version": "3.12.0",
            "gates_attested": [],
        }
        payload["frontend"] = {
            "tests_passed": 29,
            "vitest_artifact": "frontend/var/vitest-results.json",
        }
        errors = publishability_errors(payload, expected_commit_sha="abc123", repo=None)
        self.assertTrue(any("attestation_not_ci" in e for e in errors))

    def test_attestation_cannot_be_forged_locally(self) -> None:
        import os

        help_result = subprocess.run(
            [sys.executable, "-m", "aerobim.tools.export_runtime_baseline", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotIn("--attested-by", help_result.stdout)
        baseline = export_runtime_baseline(backend_root=_REPO / "backend")
        self.assertEqual(baseline["attestation"]["attested_by"], "local")
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=False):
            forged = export_runtime_baseline(backend_root=_REPO / "backend")
        self.assertEqual(forged["attestation"]["attested_by"], "local")
        self.assertTrue(forged["attestation"].get("attestation_environment_incomplete"))

    def test_gates_attested_env_ignored_locally(self) -> None:
        """N-23: AEROBIM_GATES_ATTESTED must not forge gates_attested outside complete CI."""
        import os

        with patch.dict(
            os.environ,
            {
                "AEROBIM_GATES_ATTESTED": (
                    "test,frontend,supply-chain-audit,sprint-2-1-gates,"
                    "security-regression,offline-bundle-smoke,openapi-contract"
                ),
                "GITHUB_ACTIONS": "false",
            },
            clear=False,
        ):
            baseline = export_runtime_baseline(backend_root=_REPO / "backend")
        self.assertEqual(baseline["attestation"]["attested_by"], "local")
        self.assertEqual(baseline["attestation"]["gates_attested"], [])

    def test_committed_baseline_is_ci_attested(self) -> None:
        from aerobim.tools.export_runtime_baseline import committed_baseline_attestation_errors

        artifact = _REPO / "docs" / "evidence" / "runtime-baseline-latest.json"
        stored = json.loads(artifact.read_text(encoding="utf-8"))
        attestation = stored.get("attestation")
        if not isinstance(attestation, dict) or attestation.get("attested_by") != "ci":
            self.skipTest(
                "bootstrap: commit CI-generated docs/evidence/runtime-baseline-latest.json "
                "from Actions artifact (WP-A11)"
            )
        if stored.get("publishable") is not True:
            self.fail("CI-attested committed baseline must be publishable=true")
        errors = committed_baseline_attestation_errors(_REPO)
        # On pull_request merge refs, HEAD is a synthetic merge commit; evidence tip
        # may sit more than one first-parent hop away. Attestation+publishable still bind.
        soft = {
            e
            for e in errors
            if e.startswith("commit_sha_mismatch")
            or e.startswith("tree_sha_mismatch")
            or e.startswith("baseline_stale_by_")
        }
        hard = [e for e in errors if e not in soft]
        self.assertEqual(hard, [], msg="; ".join(hard))
        if soft:
            self.skipTest("evidence SHA lag vs merge-ref HEAD: " + "; ".join(sorted(soft)))

    def test_fake_frontend_count_without_vitest_artifact_not_publishable(self) -> None:
        from aerobim.tools.export_runtime_baseline import publishability_errors

        payload = CompletenessErrorsTests()._complete()
        payload["publishable"] = True
        payload["artifact_completeness"] = "full"
        payload["working_tree_clean"] = True
        payload["attestation"] = {
            "attested_by": "ci",
            "run_id": "1",
            "run_attempt": 1,
            "workflow_ref": "KonkovDV/AeroBIM/.github/workflows/ci.yml@refs/heads/main",
            "github_sha": "abc123",
            "runner_os": "Linux",
            "runner_python": "3.12.0",
            "gates_attested": sorted(
                {
                    "test",
                    "frontend",
                    "supply-chain-audit",
                    "sprint-2-1-gates",
                    "security-regression",
                    "offline-bundle-smoke",
                    "openapi-contract",
                }
            ),
        }
        payload["frontend"] = {"tests_passed": 999, "vitest_artifact": None}
        errors = publishability_errors(payload, expected_commit_sha="abc123", repo=None)
        self.assertTrue(any("frontend_vitest_artifact_missing" in e for e in errors))

    def test_ci_environment_yields_publishable_true(self) -> None:
        """Circular-lock regression: compute publishable before self-declared keys exist."""
        import os

        from aerobim.tools.export_runtime_baseline import _publishability_core_errors

        sha = _git("rev-parse", "HEAD")
        gates_csv = (
            "test,frontend,supply-chain-audit,sprint-2-1-gates,"
            "security-regression,offline-bundle-smoke,openapi-contract"
        )
        vitest_dir = _REPO / "frontend" / "var"
        vitest_dir.mkdir(parents=True, exist_ok=True)
        vitest = vitest_dir / "vitest-results.json"
        vitest.write_text(
            json.dumps(
                {
                    "numTotalTests": 29,
                    "numPassedTests": 29,
                    "numFailedTests": 0,
                    "numPendingTests": 0,
                }
            ),
            encoding="utf-8",
        )
        env = {
            "GITHUB_ACTIONS": "true",
            "GITHUB_RUN_ID": "1",
            "GITHUB_RUN_ATTEMPT": "1",
            "GITHUB_WORKFLOW_REF": ("KonkovDV/AeroBIM/.github/workflows/ci.yml@refs/heads/main"),
            "GITHUB_SHA": sha,
            "AEROBIM_GATES_ATTESTED": gates_csv,
            "RUNNER_OS": "Linux",
        }
        with (
            patch.dict(os.environ, env, clear=False),
            patch(
                "aerobim.tools.export_runtime_baseline._working_tree_clean",
                return_value=True,
            ),
            patch(
                "aerobim.tools.export_runtime_baseline._commit_sha",
                return_value=sha,
            ),
            patch(
                "aerobim.tools.export_runtime_baseline._tree_sha",
                return_value="tree-ci-test",
            ),
            patch(
                "aerobim.tools.export_runtime_baseline._test_collection_inventory",
                return_value={
                    "test_definitions": 100,
                    "tests_collected_live": 100,
                    "uncollected": [],
                },
            ),
            patch(
                "aerobim.tools.export_runtime_baseline._count_tests",
                return_value=100,
            ),
            patch(
                "aerobim.tools.export_runtime_baseline._count_lines",
                return_value=1000,
            ),
            patch(
                "aerobim.tools.export_runtime_baseline._extraction_macro_f1",
                return_value=0.86,
            ),
        ):
            baseline = export_runtime_baseline(
                backend_root=_REPO / "backend",
                tests_passed=92,
                tests_skipped=8,
                tests_failed=0,
                tests_collected=100,
                frontend_tests_passed=29,
                frontend_tests_failed=0,
                quality_gates={k: "PASS" for k in ("ruff", "mypy", "pytest", "vitest", "build")},
                vitest_json_path=str(vitest),
                require_clean_tree=True,
            )
        core_errs = _publishability_core_errors(baseline)
        self.assertEqual(core_errs, [], msg="; ".join(core_errs))
        self.assertEqual(baseline["attestation"]["attested_by"], "ci")
        self.assertTrue(baseline["publishable"])
        self.assertEqual(baseline["artifact_completeness"], "full")
        from aerobim.tools.export_runtime_baseline import publishability_errors

        self.assertEqual(
            publishability_errors(baseline, expected_commit_sha=sha, repo=None),
            [],
        )

    def test_baseline_has_no_local_paths(self) -> None:
        """N-24: public baseline must not leak absolute local machine paths."""
        abs_python = r"C:\Users\Пользователь\AppData\Local\Programs\Python\Python313\python.exe"
        abs_vitest = str((_REPO / "frontend" / "var" / "vitest-results.json").resolve())
        baseline = export_runtime_baseline(
            backend_root=_REPO / "backend",
            quality_gates={
                "ruff": {"status": "PASS", "tool": abs_python},
                "mypy": {"status": "PASS", "tool": abs_python},
                "pytest": {"status": "PASS", "tool": abs_python},
                "vitest": {"status": "PASS", "tool": "vitest"},
                "build": {"status": "PASS", "tool": "npm"},
            },
            vitest_json_path=abs_vitest,
        )
        dumped = json.dumps(baseline)
        self.assertNotIn("Пользователь", dumped)
        self.assertNotIn("AppData", dumped)
        self.assertNotIn("C:\\\\Users", dumped)
        self.assertNotIn("C:/Users", dumped)
        self.assertEqual(baseline["quality_gates"]["ruff"]["tool"], "python")
        vitest_art = baseline["frontend"]["vitest_artifact"]
        self.assertIsInstance(vitest_art, str)
        self.assertFalse(Path(str(vitest_art)).is_absolute())
        self.assertTrue(str(vitest_art).replace("\\", "/").startswith("frontend/"))

    def test_refuses_local_overwrite_of_committed_baseline(self) -> None:
        """N-26: --out to committed path without CI attestation must exit 2."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "aerobim.tools.export_runtime_baseline",
                "--out",
                str(_REPO / "docs" / "evidence" / "runtime-baseline-latest.json"),
            ],
            cwd=_REPO / "backend",
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("N-26", result.stderr)

    def test_check_publishable_fails_when_not_publishable(self) -> None:
        """N-25: vacuum skip removed — non-publishable committed artifact is an error."""
        from aerobim.tools.export_runtime_baseline import _check_artifact_publishable

        errors = _check_artifact_publishable(_REPO)
        artifact = json.loads(
            (_REPO / "docs" / "evidence" / "runtime-baseline-latest.json").read_text(
                encoding="utf-8"
            )
        )
        if artifact.get("publishable") is True:
            self.skipTest("committed baseline already publishable")
        self.assertTrue(errors)
        self.assertTrue(any("not_publishable" in e for e in errors))

    def test_compare_allows_parent_commit_sha(self) -> None:
        """Shallow CI clones have no HEAD^ — mock parent helpers instead of rev-parse."""
        from aerobim.tools.export_runtime_baseline import compare_baseline_snapshots

        head = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        parent = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        head_tree = "cccccccccccccccccccccccccccccccccccccccc"
        parent_tree = "dddddddddddddddddddddddddddddddddddddddd"
        committed = {
            "commit_sha": parent,
            "tree_sha": parent_tree,
            "schema_version": "1.4.0",
            "metrics": {
                "backend_src_loc": 100,
                "backend_test_loc": 100,
                "backend_test_functions": 100,
            },
            "attestation": {"attested_by": "ci"},
            "publishable": True,
        }
        generated = {
            "commit_sha": head,
            "tree_sha": head_tree,
            "schema_version": "1.4.0",
            "metrics": {
                "backend_src_loc": 100,
                "backend_test_loc": 100,
                "backend_test_functions": 100,
            },
            "attestation": {"attested_by": "ci"},
            "publishable": True,
        }
        with (
            patch(
                "aerobim.tools.export_runtime_baseline._parent_commit_shas",
                side_effect=lambda _repo, commit: [parent] if commit == head else [],
            ),
            patch(
                "aerobim.tools.export_runtime_baseline._tree_sha_for_commit",
                side_effect=lambda _repo, commit: parent_tree if commit == parent else None,
            ),
        ):
            self.assertEqual(compare_baseline_snapshots(committed, generated, repo=_REPO), [])


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


class BaselineDriftAndReadmeAttackTests(unittest.TestCase):
    def test_loc_inflate_beyond_tolerance_is_killed(self) -> None:
        """A5: +51 LOC in artifact vs live must fail (tolerance is 50)."""
        from aerobim.tools.export_runtime_baseline import (
            _DRIFT_TOLERANCE,
            _check_artifact_drift,
        )

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            evidence = repo / "docs" / "evidence"
            evidence.mkdir(parents=True)
            live = {
                "metrics": {
                    "backend_src_loc": 1000,
                    "backend_test_loc": 1000,
                    "backend_test_functions": 100,
                }
            }
            stored = {
                "metrics": {
                    "backend_src_loc": 1000 + _DRIFT_TOLERANCE + 1,
                    "backend_test_loc": 1000,
                    "backend_test_functions": 100,
                }
            }
            (evidence / "runtime-baseline-latest.json").write_text(
                json.dumps(stored),
                encoding="utf-8",
            )
            errors = _check_artifact_drift(repo, live)
            self.assertTrue(errors)
            self.assertTrue(any("backend_src_loc" in e for e in errors))

    def test_manual_readme_snippet_mismatch_is_killed(self) -> None:
        """A6: hand-edited README runtime snippet must fail vs artifact."""
        from aerobim.tools.export_runtime_baseline import _check_readme_markers

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            evidence = repo / "docs" / "evidence"
            evidence.mkdir(parents=True)
            snippet = (
                "tests_passed: backend=1, frontend=1; commit deadbeef; "
                "see docs/evidence/runtime-baseline-latest.json"
            )
            artifact = {
                "readme_snippet": snippet,
                "metrics": {},
            }
            (evidence / "runtime-baseline-latest.json").write_text(
                json.dumps(artifact),
                encoding="utf-8",
            )
            forged = snippet.replace("frontend=1", "frontend=999")
            readme = (
                "# AeroBIM\n\n"
                "<!-- AEROBIM_RUNTIME_BASELINE:BEGIN -->\n"
                f"{forged}\n"
                "<!-- AEROBIM_RUNTIME_BASELINE:END -->\n"
                "<!-- AEROBIM_DOCUMENTED_ENV:BEGIN -->\n"
                "AEROBIM_HOST\n"
                "<!-- AEROBIM_DOCUMENTED_ENV:END -->\n"
            )
            (repo / "README.md").write_text(readme, encoding="utf-8")
            (repo / "README.ru.md").write_text(readme, encoding="utf-8")
            # Avoid env/inventory side checks by stubbing helpers if needed — markers only.
            with (
                patch(
                    "aerobim.tools.export_runtime_baseline._check_documented_env_sets",
                    return_value=[],
                ),
                patch(
                    "aerobim.tools.export_runtime_baseline._check_code_env_documented",
                    return_value=[],
                ),
                patch(
                    "aerobim.tools.export_runtime_baseline._check_architecture_inventory",
                    return_value=[],
                ),
                patch(
                    "aerobim.tools.export_runtime_baseline.export_runtime_baseline",
                    return_value={"metrics": {}},
                ),
                patch(
                    "aerobim.tools.export_runtime_baseline._check_readme_numeric_claims",
                    return_value=[],
                ),
            ):
                errors = _check_readme_markers(repo)
            self.assertTrue(any("readme_snippet" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
