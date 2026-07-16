from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.core.di.tokens import Tokens
from aerobim.domain.architecture import CONTOUR_PORTS, Contour
from aerobim.domain.mep import UnconfiguredMepSystemGraphProvider


class MepSystemGraphContractTests(unittest.TestCase):
    def test_unconfigured_provider_fails_closed(self) -> None:
        provider = UnconfiguredMepSystemGraphProvider()
        with tempfile.TemporaryDirectory() as temporary_directory:
            fake = Path(temporary_directory) / "mep.ifc"
            fake.write_text("ISO-10303-21;", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "MEP-CLASH-001"):
                provider.build(fake)

    def test_mep_port_in_deterministic_contour_and_token_exists(self) -> None:
        self.assertIn("MepSystemGraphProvider", CONTOUR_PORTS[Contour.DETERMINISTIC_VALIDATION])
        self.assertEqual(Tokens.MEP_SYSTEM_GRAPH_PROVIDER, "mep_system_graph_provider")


if __name__ == "__main__":
    unittest.main()
