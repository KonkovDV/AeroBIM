#!/usr/bin/env python3
"""Focused tests for deferred-controls registry and private-path gate scripts."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
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


class LiveRegistrySmokeTests(unittest.TestCase):
    def test_repo_registry_passes_today(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(_SCRIPTS / "verify_deferred_controls.py"),
                "--registry",
                str(_BACKEND.parent / "governance/deferred_controls_registry.json"),
                "--today",
                "2026-08-09",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)

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
