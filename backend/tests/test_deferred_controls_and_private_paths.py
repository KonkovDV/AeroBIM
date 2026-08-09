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
