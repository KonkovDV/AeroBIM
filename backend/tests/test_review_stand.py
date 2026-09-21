from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.tools.run_live_review_smoke import (
    build_backend_env,
    ensure_frontend_dependencies,
    frontend_vite_installed,
    repo_root,
)
from aerobim.tools.run_review_stand import (
    CLAIM_BOUNDARY,
    default_storage_dir,
    print_stand_card,
)
from aerobim.tools.seed_smoke_report import SMOKE_TENANT_ID


class ReviewStandTests(unittest.TestCase):
    def test_default_storage_is_isolated_under_local(self) -> None:
        storage = default_storage_dir()
        self.assertEqual(storage, repo_root() / ".local" / "review-stand")
        self.assertNotEqual(storage, repo_root() / "backend" / "var" / "reports")

    def test_stand_reuses_anonymous_dev_env_and_does_not_claim_customer_go(self) -> None:
        env = build_backend_env(
            base_env={"PATH": "example", "AEROBIM_API_BEARER_TOKEN": "secret"},
            storage_dir=Path("c:/tmp/review-stand"),
            port=8080,
            frontend_origin="http://127.0.0.1:5173",
        )
        self.assertEqual(env["AEROBIM_ENV"], "development")
        self.assertEqual(env["AEROBIM_ALLOW_ANONYMOUS_DEV"], "true")
        self.assertEqual(env["AEROBIM_API_TENANT_ID"], SMOKE_TENANT_ID)
        self.assertNotIn("AEROBIM_API_BEARER_TOKEN", env)
        self.assertTrue((env.get("AEROBIM_DEV_REVIEWER_TOKEN") or "").strip())
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
                storage=Path("c:/tmp/review-stand"),
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
            patch("aerobim.tools.run_live_review_smoke.shutil.which", return_value="npm"),
            patch("aerobim.tools.run_live_review_smoke.run_foreground_command") as npm_ci,
        ):
            ensure_frontend_dependencies()
            npm_ci.assert_called_once()
            command = npm_ci.call_args.args[0]
            self.assertEqual(command[1], "ci")
            self.assertEqual(npm_ci.call_args.kwargs["cwd"], tmp)
            self.assertEqual(npm_ci.call_args.kwargs["label"], "npm ci")

    def test_ensure_explains_missing_npm(self) -> None:
        tmp = Path(self.enterContext(TemporaryDirectory()))
        with (
            patch("aerobim.tools.run_live_review_smoke.frontend_dir", return_value=tmp),
            patch("aerobim.tools.run_live_review_smoke.shutil.which", return_value=None),
        ):
            with self.assertRaises(RuntimeError) as raised:
                ensure_frontend_dependencies()
        self.assertIn("Node.js / npm not found", str(raised.exception))
        self.assertIn("run_kt3_jury", str(raised.exception))

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
        self.assertEqual(command[1:3], ["-m", "aerobim.tools.run_review_stand"])
        self.assertEqual(command[-1], "--help")

    def test_root_run_jury_bat_is_the_windows_first_clone(self) -> None:
        text = (repo_root() / "run-jury.bat").read_text(encoding="utf-8")
        self.assertIn("py -3.12 -m venv .venv", text)
        self.assertIn('pip install -e ".[dev,raster]"', text)
        self.assertIn("-m aerobim.tools.check_local_launch", text)
        self.assertIn("-m aerobim.tools.run_kt3_jury", text)
        self.assertNotIn("run_review_stand", text)
        self.assertIn("customer_go false", text)
        self.assertIn("is not CPython 3.12", text)
        self.assertIn("Trying python if it is CPython 3.12", text)
        check = (repo_root() / "check-launch.bat").read_text(encoding="utf-8")
        self.assertIn("backend\\.venv\\Scripts\\python.exe", check)
        self.assertIn("check_local_launch", check)
        self.assertIn("run-jury.bat", check)
        self.assertIn("pause", check)
        self.assertNotIn("run_review_stand", check)
        sh = (repo_root() / "run-jury.sh").read_text(encoding="utf-8")
        self.assertIn("python3.12 -m venv .venv", sh)
        self.assertIn("is not CPython 3.12", sh)
        self.assertIn('pip install -e ".[dev,raster]"', sh)
        attrs = (repo_root() / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn("*.bat text eol=crlf", attrs)
        self.assertIn("*.sh text eol=lf", attrs)

    def test_readme_points_diagnostics_at_check_launch_bat(self) -> None:
        for name in ("README.md", "README.en.md"):
            text = (repo_root() / name).read_text(encoding="utf-8")
            self.assertIn("run-jury.bat", text, msg=name)
            self.assertIn(".\\check-launch.bat", text, msg=name)
            self.assertIn("./run-jury.sh", text, msg=name)
            self.assertIn("VC++ 2015-2022", text, msg=name)
            self.assertNotIn("один путь в коде", text, msg=name)
            self.assertNotIn("same code path", text, msg=name)
        ru = (repo_root() / "README.md").read_text(encoding="utf-8")
        en = (repo_root() / "README.en.md").read_text(encoding="utf-8")
        self.assertIn("один порт и два адаптера", ru)
        self.assertIn("one port and two adapters", en)
        self.assertIn("не импорт в СОД", ru)
        self.assertIn("not CDE import proof", en)

    def test_root_start_bat_calls_the_review_stand(self) -> None:
        text = (repo_root() / "start.bat").read_text(encoding="utf-8")
        self.assertIn("-m aerobim.tools.run_review_stand", text)
        self.assertIn("backend\\.venv\\Scripts\\python.exe", text)
        self.assertIn(".\\start.bat", text)
        self.assertIn("python.exe -m pip install", text)
        self.assertIn("Node 20+", text)
        self.assertIn("run-jury.bat", text)
        self.assertNotIn("run_kt3_jury", text)

    def test_root_start_ps1_calls_the_review_stand(self) -> None:
        text = (repo_root() / "start.ps1").read_text(encoding="utf-8")
        self.assertIn("aerobim.tools.run_review_stand", text)
        self.assertIn("backend\\.venv\\Scripts\\python.exe", text)
        self.assertIn(".\\start.bat", text)
        self.assertIn("python.exe -m pip install", text)
        self.assertIn("Node 20+", text)
        self.assertIn("run-jury.bat", text)
        self.assertNotIn("run_kt3_jury", text)

    def test_root_start_sh_and_vite_identity(self) -> None:
        sh = (repo_root() / "start.sh").read_text(encoding="utf-8")
        self.assertIn("aerobim.tools.run_review_stand", sh)
        self.assertIn("backend/.venv/bin/python", sh)
        self.assertIn("run-jury.sh", sh)
        self.assertNotIn("next.config", sh)
        from aerobim.tools.run_review_stand import run_review_stand

        with self.assertRaises(ValueError):
            run_review_stand(frontend_port=3000)
        wrapper = (repo_root() / "frontend" / "scripts" / "start-review-shell.mjs").read_text(
            encoding="utf-8"
        )
        self.assertIn("AEROBIM_BACKEND_DIR", wrapper)
        self.assertNotIn("next dev", wrapper)
        for rel in ("next.config.mjs", "frontend/app/page.tsx"):
            self.assertFalse((repo_root() / rel).exists(), msg=rel)

    def test_readme_power_shell_recipe_requires_dot_slash(self) -> None:
        for name in ("README.md", "README.en.md"):
            text = (repo_root() / name).read_text(encoding="utf-8")
            self.assertIn(".\\start.bat", text, msg=name)
            self.assertIn("Start-Process", text, msg=name)

    def test_readme_windows_clone_calls_venv_python_exe(self) -> None:
        for name in ("README.md", "README.en.md"):
            text = (repo_root() / name).read_text(encoding="utf-8")
            self.assertIn(
                r".\.venv\Scripts\python.exe -m pip install -e",
                text,
                msg=name,
            )
            self.assertIn(
                r".\.venv\Scripts\python.exe -m aerobim.tools.run_kt3_jury",
                text,
                msg=name,
            )
            self.assertIn("Node 20+", text, msg=name)
            self.assertIn("requirements-lock.txt", text, msg=name)
            self.assertIn("requirements-win-lock.txt", text, msg=name)
            self.assertIn("uv pip install -e", text, msg=name)
            self.assertIn(".devcontainer/", text, msg=name)
            self.assertIn("customer_pilot", text, msg=name)

    def test_prototype_hop_uses_venv_python_exe_from_clone_root(self) -> None:
        text = (repo_root() / "submission" / "04-prototype" / "README.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(r".\.venv\Scripts\python.exe -m pip", text)
        self.assertIn("run-jury.bat", text)
        self.assertIn(r".\start.bat", text)
        self.assertIn("не из `frontend/`", text)
        self.assertNotIn("cd frontend", text)
        repository = (repo_root() / "submission" / "01-repository" / "README.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(r".\.venv\Scripts\python.exe -m pip", repository)
        self.assertIn("run-jury.bat", repository)


if __name__ == "__main__":
    unittest.main()
