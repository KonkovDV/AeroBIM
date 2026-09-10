from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.tools.run_it_mentor_stand import (
    CLAIM_BOUNDARY,
    default_storage_dir,
    print_stand_card,
)
from aerobim.tools.run_live_review_smoke import build_backend_env, repo_root
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
        self.assertIn("customer_go false", CLAIM_BOUNDARY)
        self.assertNotIn("customer pack processed", CLAIM_BOUNDARY.lower())

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
