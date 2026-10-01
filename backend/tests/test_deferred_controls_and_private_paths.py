#!/usr/bin/env python3
"""Focused tests for deferred-controls registry and private-path gate scripts."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
_SCRIPTS = _BACKEND / "scripts"


class DeferredControlsScriptTests(unittest.TestCase):
    def test_overdue_deferred_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp) / "waivers.json"
            registry.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0.0",
                        "waivers": [
                            {
                                "id": "x",
                                "state": "deferred",
                                "activates_on": "2026-08-01",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    str(_SCRIPTS / "verify_deferred_controls.py"),
                    "--registry",
                    str(registry),
                    "--today",
                    "2026-08-09",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 1)
            self.assertIn("deferred past activates_on", proc.stderr)

    def test_future_deferred_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp) / "waivers.json"
            registry.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0.0",
                        "waivers": [
                            {
                                "id": "y",
                                "state": "deferred",
                                "activates_on": "2026-08-25",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    str(_SCRIPTS / "verify_deferred_controls.py"),
                    "--registry",
                    str(registry),
                    "--today",
                    "2026-08-09",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0)

    def test_active_with_false_policy_flags_fails(self) -> None:
        """N-58: registry must read the mechanism file, not only its own state field."""

        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp) / "waivers.json"
            policy = Path(tmp) / "policy.json"
            registry.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0.0",
                        "waivers": [
                            {
                                "id": "A4",
                                "state": "active",
                                "activates_on": "2026-08-09",
                                "policy_flags": ["enforce_ci", "fail_on_unverifiable_signature"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            policy.write_text(
                json.dumps(
                    {
                        "enforce_ci": False,
                        "fail_on_unverifiable_signature": False,
                    }
                ),
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    str(_SCRIPTS / "verify_deferred_controls.py"),
                    "--registry",
                    str(registry),
                    "--policy",
                    str(policy),
                    "--today",
                    "2026-08-09",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 1)
            self.assertIn("state=active but enforce_ci=false", proc.stderr)

    def test_policy_numeric_mismatch_fails(self) -> None:
        """N-43: deferred registry watches max_commits_behind in the mechanism file."""

        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp) / "waivers.json"
            mechanism = Path(tmp) / "baseline_integrity_policy.json"
            mechanism.write_text(
                json.dumps({"max_commits_behind": 1}),
                encoding="utf-8",
            )
            registry.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0.0",
                        "waivers": [
                            {
                                "id": "N43",
                                "state": "deferred",
                                "activates_on": "2026-08-25",
                                "policy_numeric": {
                                    "file": str(mechanism),
                                    "field": "max_commits_behind",
                                    "when_deferred": 50,
                                    "when_active": 1,
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    str(_SCRIPTS / "verify_deferred_controls.py"),
                    "--registry",
                    str(registry),
                    "--today",
                    "2026-08-09",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 1)
            self.assertIn("max_commits_behind=1", proc.stderr)
            self.assertIn("expected 50", proc.stderr)


class LiveRegistrySmokeTests(unittest.TestCase):
    def test_repo_registry_passes_today(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(_SCRIPTS / "verify_deferred_controls.py"),
                "--registry",
                str(_BACKEND.parent / "governance/deferred_controls_registry.json"),
                "--policy",
                str(_BACKEND.parent / "governance/commit_signing_policy.json"),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)

    def test_n47_and_n59_stay_active(self) -> None:
        registry = json.loads(
            (_BACKEND.parent / "governance/deferred_controls_registry.json").read_text(
                encoding="utf-8"
            )
        )
        by_id = {str(item.get("id")): item for item in (registry.get("waivers") or [])}
        self.assertEqual(by_id["N47-ruf100"]["state"], "active")
        self.assertEqual(by_id["N59-trusted-keys-already-trusted-signer"]["state"], "active")

    def test_n47_ruff_select_includes_ruf100(self) -> None:
        with (_BACKEND / "pyproject.toml").open("rb") as handle:
            payload = tomllib.load(handle)
        select = payload["tool"]["ruff"]["lint"]["select"]
        self.assertIn("RUF100", select)

    def test_n59_policy_flag_and_cliff_sha(self) -> None:
        policy = json.loads(
            (_BACKEND.parent / "governance/commit_signing_policy.json").read_text(encoding="utf-8")
        )
        self.assertTrue(policy.get("require_author_signature_on_trusted_keys_dir"))
        self.assertEqual(
            str(policy.get("n59_enforced_after") or ""),
            "433e0644860812f2b733c96ecab714a141550f2f",
        )

    def test_private_path_gate_clean(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(_SCRIPTS / "verify_no_private_tracked_paths.py")],
            check=False,
            capture_output=True,
            text=True,
            cwd=str(_BACKEND.parent),
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)


if __name__ == "__main__":
    unittest.main()
