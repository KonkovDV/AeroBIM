"""Thin IFC GUID/attribute model-diff adapter + DI wiring."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.core.di.tokens import Tokens
from aerobim.infrastructure.adapters.ifc_guid_attribute_diff import (
    IfcGuidAttributeDiffAdapter,
)
from aerobim.infrastructure.di.bootstrap import bootstrap_container


def _fixture_pair() -> tuple[Path, Path]:
    root = Path(__file__).resolve().parents[2] / "samples" / "ifc" / "model-diff"
    return root / "revision-a.ifc", root / "revision-b.ifc"


class IfcModelDiffTests(unittest.TestCase):
    def test_guid_add_remove_rename(self) -> None:
        old_p, new_p = _fixture_pair()
        result = IfcGuidAttributeDiffAdapter().compare(old_p, new_p)
        self.assertFalse(result.closes_rt001)
        self.assertEqual(result.claim_level, "engineering_signal_only")
        summary = result.summary()
        self.assertEqual(summary["removed"], 1)
        self.assertEqual(summary["added"], 1)
        self.assertGreaterEqual(summary["attribute_changed"], 1)
        kinds = {e.kind for e in result.entries}
        self.assertIn("removed", kinds)
        self.assertIn("added", kinds)
        self.assertIn("attribute_changed", kinds)
        renamed = [
            e
            for e in result.entries
            if e.kind == "attribute_changed" and e.attribute == "Name"
        ]
        self.assertTrue(any(e.old_value == "Wall Rename Source" for e in renamed))
        self.assertTrue(any(e.new_value == "Wall Renamed" for e in renamed))

    def test_di_token_resolves(self) -> None:
        container = bootstrap_container()
        adapter = container.resolve(Tokens.IFC_MODEL_DIFF)
        old_p, new_p = _fixture_pair()
        result = adapter.compare(old_p, new_p)
        self.assertEqual(result.summary()["removed"], 1)


if __name__ == "__main__":
    unittest.main()
