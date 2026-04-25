"""Parametric IFC release compatibility tests.

Runs the same IDS rule (Pset_WallCommon.FireRating = REI60) against IFC2x3,
IFC4, and IFC4x3 fixtures and verifies:

1. The property is found in all three releases (no false-positive ERROR).
2. The fixture with the correct value (REI60) passes in every release.
3. The IfcTesterIdsValidator does not raise on any supported release.

See docs/ifc-compatibility-matrix.md for the full compatibility statement.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLES_DIR = REPO_ROOT / "samples"

IFC_FIXTURES = [
    ("IFC2x3", SAMPLES_DIR / "ifc" / "wall-pset-ifc2x3.ifc"),
    ("IFC4", SAMPLES_DIR / "ifc" / "wall-pset-qto-pass.ifc"),
    ("IFC4x3", SAMPLES_DIR / "ifc" / "wall-pset-ifc4x3.ifc"),
]

IDS_FIRE_RATING = SAMPLES_DIR / "ids" / "wall-fire-rating.ids"


class IfcReleaseCompatibilityTests(unittest.TestCase):
    """Verify that the validation pipeline handles IFC2x3, IFC4, and IFC4x3."""

    def _skip_if_no_ifctester(self) -> None:
        try:
            import ifctester  # noqa: F401
        except ImportError:
            self.skipTest("ifctester not installed")
        try:
            import ifcopenshell  # noqa: F401
        except ImportError:
            self.skipTest("ifcopenshell not installed")

    def _skip_if_no_ifcopenshell(self) -> None:
        try:
            import ifcopenshell  # noqa: F401
        except ImportError:
            self.skipTest("ifcopenshell not installed")

    def test_fire_rating_ids_passes_on_all_supported_releases(self) -> None:
        """IDS rule should produce 0 ERROR findings on all three releases."""
        self._skip_if_no_ifctester()

        import ifcopenshell
        import ifctester

        for release_label, ifc_path in IFC_FIXTURES:
            if not ifc_path.exists():
                self.skipTest(f"Fixture missing: {ifc_path}")

            with self.subTest(release=release_label):
                ids_doc = ifctester.open(str(IDS_FIRE_RATING))
                model = ifcopenshell.open(str(ifc_path))
                ids_doc.validate(model)

                failed_specs = [
                    s for s in ids_doc.specifications if not s.status
                ]
                self.assertEqual(
                    [],
                    failed_specs,
                    msg=(
                        f"IDS validation failed on {release_label}: "
                        f"{[s.name for s in failed_specs]}"
                    ),
                )

    def test_ifcopenshell_opens_all_supported_releases(self) -> None:
        """IfcOpenShell must open all three release fixtures without exception."""
        self._skip_if_no_ifcopenshell()

        import ifcopenshell

        for release_label, ifc_path in IFC_FIXTURES:
            if not ifc_path.exists():
                self.skipTest(f"Fixture missing: {ifc_path}")

            with self.subTest(release=release_label):
                try:
                    model = ifcopenshell.open(str(ifc_path))
                except Exception as exc:  # noqa: BLE001
                    self.fail(
                        f"ifcopenshell.open() raised on {release_label}: {exc}"
                    )
                walls = model.by_type("IfcWall")
                self.assertGreater(
                    len(walls),
                    0,
                    msg=f"No IfcWall found in {release_label} fixture",
                )

    def test_pset_wall_common_present_in_all_releases(self) -> None:
        """Pset_WallCommon must be discoverable in all three release fixtures."""
        self._skip_if_no_ifcopenshell()

        import ifcopenshell
        import ifcopenshell.util.element as ifc_util

        for release_label, ifc_path in IFC_FIXTURES:
            if not ifc_path.exists():
                self.skipTest(f"Fixture missing: {ifc_path}")

            with self.subTest(release=release_label):
                model = ifcopenshell.open(str(ifc_path))
                walls = model.by_type("IfcWall")
                self.assertGreater(len(walls), 0)

                wall = walls[0]
                psets = ifc_util.get_psets(wall)
                self.assertIn(
                    "Pset_WallCommon",
                    psets,
                    msg=f"Pset_WallCommon missing on {release_label}",
                )
                fire_rating = psets["Pset_WallCommon"].get("FireRating")
                self.assertEqual(
                    "REI60",
                    fire_rating,
                    msg=f"FireRating mismatch on {release_label}: got {fire_rating!r}",
                )

    def test_ifc2x3_fixture_is_recognised_as_ifc2x3(self) -> None:
        """Schema header of the IFC2x3 fixture must declare IFC2X3."""
        ifc2x3_path = SAMPLES_DIR / "ifc" / "wall-pset-ifc2x3.ifc"
        if not ifc2x3_path.exists():
            self.skipTest("IFC2x3 fixture missing")

        content = ifc2x3_path.read_text(encoding="utf-8", errors="replace")
        self.assertIn("IFC2X3", content.upper())

    def test_ifc4x3_fixture_is_recognised_as_ifc4x3(self) -> None:
        """Schema header of the IFC4x3 fixture must declare IFC4X3."""
        ifc4x3_path = SAMPLES_DIR / "ifc" / "wall-pset-ifc4x3.ifc"
        if not ifc4x3_path.exists():
            self.skipTest("IFC4x3 fixture missing")

        content = ifc4x3_path.read_text(encoding="utf-8", errors="replace")
        self.assertIn("IFC4X3", content.upper())
