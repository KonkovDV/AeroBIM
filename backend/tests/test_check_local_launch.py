"""Clone/laptop preflight stays fail-closed on Store stub and closed sign-off."""

from __future__ import annotations

import json
import unittest
from io import StringIO
from pathlib import Path

from aerobim.tools.check_local_launch import (
    Check,
    collect_checks,
    emit_preflight,
    worst_exit,
)
from aerobim.tools.seed_smoke_report import repo_root


class CheckLocalLaunchTests(unittest.TestCase):
    def _base(self, **overrides: object) -> list[Check]:
        payload = {
            "env": {},
            "version_info": (3, 12),
            "executable": r"C:\Python312\python.exe",
            "root": repo_root(),
            "is_windows": True,
        }
        payload.update(overrides)
        return collect_checks(**payload)  # type: ignore[arg-type]

    def test_cpython_312_is_info(self) -> None:
        checks = self._base()
        python = next(item for item in checks if item.id == "python_version")
        self.assertTrue(python.ok)
        self.assertEqual(python.level, "info")

    def test_python_311_is_fatal(self) -> None:
        checks = self._base(version_info=(3, 11))
        python = next(item for item in checks if item.id == "python_version")
        self.assertFalse(python.ok)
        self.assertEqual(python.level, "fatal")
        self.assertEqual(worst_exit(checks), 2)

    def test_python_313_is_warn_not_fatal(self) -> None:
        checks = self._base(version_info=(3, 13))
        python = next(item for item in checks if item.id == "python_version")
        self.assertFalse(python.ok)
        self.assertEqual(python.level, "warn")
        self.assertEqual(worst_exit(checks), 1)

    def test_store_stub_is_fatal(self) -> None:
        checks = self._base(executable=r"C:\Users\x\AppData\Local\Microsoft\WindowsApps\python.exe")
        stub = next(item for item in checks if item.id == "python_store_stub")
        self.assertFalse(stub.ok)
        self.assertEqual(stub.level, "fatal")

    def test_customer_pilot_is_fatal(self) -> None:
        checks = self._base(env={"AEROBIM_SIGNOFF_PROFILE": "customer_pilot"})
        signoff = next(item for item in checks if item.id == "signoff_profile")
        self.assertFalse(signoff.ok)
        self.assertEqual(signoff.level, "fatal")

    def test_production_env_is_fatal(self) -> None:
        checks = self._base(env={"AEROBIM_ENV": "production"})
        aerobim_env = next(item for item in checks if item.id == "aerobim_env")
        self.assertFalse(aerobim_env.ok)
        self.assertEqual(aerobim_env.level, "fatal")

    def test_py_launcher_default_313_warns(self) -> None:
        checks = self._base(py_launcher_text="-V:3.13 *  C:\\Python313\\python.exe\n")
        launcher = next(item for item in checks if item.id == "py_launcher_default")
        self.assertFalse(launcher.ok)
        self.assertEqual(launcher.level, "warn")

    def test_review_shell_without_npm_is_fatal(self) -> None:
        checks = self._base(review_shell=True, npm_path=None, ports_busy={8080: False})
        npm = next(item for item in checks if item.id == "npm")
        self.assertFalse(npm.ok)
        self.assertEqual(npm.level, "fatal")

    def test_emit_prints_only_failures(self) -> None:
        stream = StringIO()
        code = emit_preflight(
            stream=stream,
            checks=[
                Check("python_version", True, "info", "CPython 3.12"),
                Check("signoff_profile", False, "fatal", "closed contour"),
            ],
        )
        self.assertEqual(code, 2)
        text = stream.getvalue()
        self.assertIn("FATAL signoff_profile", text)
        self.assertNotIn("python_version", text)

    def test_package_json_declares_node_20(self) -> None:
        payload = json.loads(
            (Path(repo_root()) / "frontend" / "package.json").read_text(encoding="utf-8")
        )
        self.assertGreaterEqual(int(str(payload["engines"]["node"]).lstrip(">=").split(".")[0]), 20)

    def test_uvloop_on_windows_from_linux_lock_is_fatal(self) -> None:
        checks = self._base(uvloop_present=True)
        item = next(row for row in checks if row.id == "uvloop_on_windows")
        self.assertFalse(item.ok)
        self.assertEqual(item.level, "fatal")
        self.assertIn("requirements-win-lock.txt", item.message)

    def test_npmrc_engine_strict(self) -> None:
        text = (Path(repo_root()) / "frontend" / ".npmrc").read_text(encoding="utf-8")
        self.assertIn("engine-strict=true", text)


if __name__ == "__main__":
    unittest.main()
