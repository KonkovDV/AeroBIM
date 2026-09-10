from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.tools.run_it_mentor_stand import (
    CLAIM_BOUNDARY,
    default_storage_dir,
    print_stand_card,
)
from aerobim.tools.run_live_review_smoke import (
    build_backend_env,
    ensure_frontend_dependencies,
    frontend_vite_installed,
    repo_root,
)
from aerobim.tools.seed_smoke_report import SMOKE_TENANT_ID


class ItMentorStandTests(unittest.TestCase):
    def test_default_storage_is_isolated_under_local(self) -> None:
        storage = default_storage_dir()
        self.assertEqual(storage, repo_root() / ".local" / "mentor-demo-stand")
        self.assertNotEqual(storage, repo_root() / "backend" / "var" / "reports")

    def test_stand_reuses_anonymous_dev_env_and_does_not_claim_customer_go(self) -> None:
        env = build_backend_env(
            base_env={"PATH": "example", "AEROBIM_API_BEARER_TOKEN": "secret"},
            storage_dir=Path("c:/tmp/mentor-stand"),
            port=8080,
            frontend_origin="http://127.0.0.1:5173",
        )
        self.assertEqual(env["AEROBIM_ENV"], "development")
        self.assertEqual(env["AEROBIM_ALLOW_ANONYMOUS_DEV"], "true")
        self.assertEqual(env["AEROBIM_API_TENANT_ID"], SMOKE_TENANT_ID)
        self.assertNotIn("AEROBIM_API_BEARER_TOKEN", env)
        self.assertEqual(env["AEROBIM_SIGNOFF_PROFILE"], "development")
        self.assertEqual(env["AEROBIM_HOST"], "127.0.0.1")
        self.assertIn("customer_go false", CLAIM_BOUNDARY)
        self.assertNotIn("customer pack processed", CLAIM_BOUNDARY.lower())
        self.assertNotIn("Empty storage", CLAIM_BOUNDARY)

    def test_stand_card_prints_the_demo_button(self) -> None:
        import io
        from contextlib import redirect_stdout

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            print_stand_card(
                frontend_url="http://127.0.0.1:5173",
                backend_url="http://127.0.0.1:8080",
                storage=Path("c:/tmp/mentor-stand"),
            )
        text = buffer.getvalue()
        self.assertIn("Загрузить демонстрационный комплект", text)
        self.assertIn("customer_go=False", text)
        self.assertIn("http://127.0.0.1:5173", text)
        self.assertIn("Ctrl+C stops both processes", text)


def _load_review_shell_wrapper():
    path = repo_root() / "scripts" / "run_review_shell.py"
    spec = importlib.util.spec_from_file_location("run_review_shell", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReviewShellLauncherTests(unittest.TestCase):
    def test_wrapper_finds_backend_venv_python(self) -> None:
        module = _load_review_shell_wrapper()
        repo = Path(self.enterContext(TemporaryDirectory()))
        posix = repo / "backend" / ".venv" / "bin" / "python"
        posix.parent.mkdir(parents=True)
        posix.write_text("", encoding="utf-8")
        self.assertEqual(module.backend_venv_python(repo), posix)

    def test_wrapper_prefers_windows_python_exe_when_both_exist(self) -> None:
        module = _load_review_shell_wrapper()
        repo = Path(self.enterContext(TemporaryDirectory()))
        windows = repo / "backend" / ".venv" / "Scripts" / "python.exe"
        posix = repo / "backend" / ".venv" / "bin" / "python"
        windows.parent.mkdir(parents=True)
        posix.parent.mkdir(parents=True)
        windows.write_text("", encoding="utf-8")
        posix.write_text("", encoding="utf-8")
        self.assertEqual(module.backend_venv_python(repo), windows)

    def test_wrapper_missing_venv_is_explicit(self) -> None:
        module = _load_review_shell_wrapper()
        missing = Path(self.enterContext(TemporaryDirectory()))
        with self.assertRaises(FileNotFoundError) as raised:
            module.backend_venv_python(missing)
        self.assertIn("backend/.venv not found", str(raised.exception))

    def test_ensure_skips_npm_ci_when_vite_is_present(self) -> None:
        tmp = Path(self.enterContext(TemporaryDirectory()))
        vite = tmp / "node_modules" / "vite"
        vite.mkdir(parents=True)
        (vite / "package.json").write_text("{}", encoding="utf-8")
        self.assertTrue(frontend_vite_installed(tmp))
        with (
            patch("aerobim.tools.run_live_review_smoke.frontend_dir", return_value=tmp),
            patch("aerobim.tools.run_live_review_smoke.run_foreground_command") as npm_ci,
        ):
            ensure_frontend_dependencies()
            npm_ci.assert_not_called()

    def test_ensure_runs_npm_ci_when_vite_is_missing(self) -> None:
        tmp = Path(self.enterContext(TemporaryDirectory()))
        self.assertFalse(frontend_vite_installed(tmp))
        with (
            patch("aerobim.tools.run_live_review_smoke.frontend_dir", return_value=tmp),
            patch("aerobim.tools.run_live_review_smoke.run_foreground_command") as npm_ci,
        ):
            ensure_frontend_dependencies()
            npm_ci.assert_called_once()
            command = npm_ci.call_args.args[0]
            self.assertEqual(command[1], "ci")
            self.assertEqual(npm_ci.call_args.kwargs["cwd"], tmp)
            self.assertEqual(npm_ci.call_args.kwargs["label"], "npm ci")

    def test_wrapper_stays_in_foreground_via_subprocess(self) -> None:
        module = _load_review_shell_wrapper()
        fake = Path("C:/fake-venv/python.exe")
        with (
            patch.object(module, "backend_venv_python", return_value=fake),
            patch.object(module.subprocess, "call", return_value=0) as call,
        ):
            self.assertEqual(module.main(["--help"]), 0)
        command = call.call_args.args[0]
        self.assertEqual(command[0], str(fake))
        self.assertEqual(command[1:3], ["-m", "aerobim.tools.run_it_mentor_stand"])
        self.assertEqual(command[-1], "--help")

    def test_root_start_bat_calls_the_mentor_stand(self) -> None:
        text = (repo_root() / "start.bat").read_text(encoding="utf-8")
        self.assertIn("-m aerobim.tools.run_it_mentor_stand", text)
        self.assertIn("backend\\.venv\\Scripts\\python.exe", text)
        self.assertIn(".\\start.bat", text)
        self.assertNotIn("run_kt3_jury", text)

    def test_root_start_ps1_calls_the_mentor_stand(self) -> None:
        text = (repo_root() / "start.ps1").read_text(encoding="utf-8")
        self.assertIn("aerobim.tools.run_it_mentor_stand", text)
        self.assertIn("backend\\.venv\\Scripts\\python.exe", text)
        self.assertIn(".\\start.bat", text)
        self.assertNotIn("run_kt3_jury", text)

    def test_readme_power_shell_recipe_requires_dot_slash(self) -> None:
        for name in ("README.md", "README.ru.md"):
            text = (repo_root() / name).read_text(encoding="utf-8")
            self.assertIn(".\\start.bat", text, msg=name)
            self.assertIn("Start-Process", text, msg=name)


if __name__ == "__main__":
    unittest.main()
