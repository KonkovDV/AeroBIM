from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.domain.mep import UnconfiguredMepSystemGraphProvider


class MepSystemGraphContractTests(unittest.TestCase):
    def test_unconfigured_provider_fails_closed(self) -> None:
        provider = UnconfiguredMepSystemGraphProvider()
        with tempfile.TemporaryDirectory() as temporary_directory:
            fake = Path(temporary_directory) / "mep.ifc"
            fake.write_text("ISO-10303-21;", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "MEP-CLASH-001"):
                provider.build(fake)


if __name__ == "__main__":
    unittest.main()
