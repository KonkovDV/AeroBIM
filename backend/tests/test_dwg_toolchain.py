"""Native DWG toolchain probe — honesty, never DWG-ready."""

from __future__ import annotations

import unittest

from aerobim.core.config.settings import Settings
from aerobim.tools.validate_dwg_toolchain import probe_dwg_toolchain


class DwgToolchainProbeTests(unittest.TestCase):
    def test_probe_never_claims_native_dwg(self) -> None:
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(
                application_name="test",
                environment="test",
                host="127.0.0.1",
                port=8080,
                storage_dir=Path(tmp),
                debug=True,
                api_bearer_token="test-token",
            )
            payload = probe_dwg_toolchain(settings=settings)
        self.assertEqual(payload["native_dwg"], "missing")
        self.assertEqual(payload["dwg_native"], "NOT_IMPLEMENTED")
        self.assertFalse(payload["claim_allowed"])
        self.assertFalse(payload["oda_sdk_present"])
        self.assertFalse(payload["oda_ingest_supported"])
        self.assertIn("STUB-ODA-CAD-001", payload["stub_id"])
        self.assertIn("Never dwg_supported", payload["claim_boundary"])


if __name__ == "__main__":
    unittest.main()
