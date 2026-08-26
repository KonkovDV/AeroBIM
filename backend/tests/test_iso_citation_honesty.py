"""Fail-closed: ISO 12006-3 is not a tolerance standard; IFC2x3 is not ISO 16739:2005."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]

_FALSE_12006_TOLERANCE = re.compile(
    r"12006-3.{0,60}(?:toleran|допуск|ε-band|epsilon)"
    r"|(?:toleran|допуск|ε-band|epsilon).{0,60}12006-3",
    re.IGNORECASE | re.DOTALL,
)
_NEGATION = re.compile(r"(?i)\bnot\b|\bне\b")

_IFC2X3_AS_ISO_2005 = re.compile(
    r"IFC\s*2x3\s*\(\s*ISO\s*16739:2005\s*\)",
    re.IGNORECASE,
)

_FALSE_MIB_ALIGNMENT = re.compile(
    r"aligned with bSI Validation Service|согласовано с лимитом сервиса валидации",
    re.IGNORECASE,
)

_SURFACES = (
    "README.md",
    "README.ru.md",
    "docs/ifc-compatibility-matrix.md",
    "docs/samolet-techlab-alignment-2026.md",
    "backend/src/aerobim/domain/quantity.py",
    "backend/src/aerobim/domain/models.py",
    "backend/src/aerobim/application/services/cross_document_contradictions.py",
    "backend/src/aerobim/application/services/drawing_annotation_validation.py",
    "backend/src/aerobim/core/config/settings.py",
    "backend/src/aerobim/infrastructure/adapters/ifc_file_open.py",
    "backend/tests/test_supplemental_edge_cases.py",
)


class IsoCitationHonestyTests(unittest.TestCase):
    def test_iso_12006_3_is_not_cited_as_tolerance(self) -> None:
        hits: list[str] = []
        for rel in _SURFACES:
            path = _REPO / rel
            text = path.read_text(encoding="utf-8")
            for i, line in enumerate(text.splitlines(), start=1):
                if not _FALSE_12006_TOLERANCE.search(line):
                    continue
                if _NEGATION.search(line):
                    continue
                hits.append(f"{rel}:{i}:{line.strip()[:160]}")
        self.assertEqual(
            hits,
            [],
            msg="ISO 12006-3 is a dictionary framework, not a tolerance:\n" + "\n".join(hits),
        )

    def test_ifc2x3_is_not_iso_16739_2005(self) -> None:
        hits: list[str] = []
        for rel in _SURFACES:
            path = _REPO / rel
            text = path.read_text(encoding="utf-8")
            for i, line in enumerate(text.splitlines(), start=1):
                if _IFC2X3_AS_ISO_2005.search(line):
                    hits.append(f"{rel}:{i}:{line.strip()[:160]}")
        self.assertEqual(
            hits,
            [],
            msg="IFC2x3 has no ISO number; ISO/PAS 16739:2005 is IFC2x Platform:\n"
            + "\n".join(hits),
        )

    def test_256_mib_is_comparable_not_identical_to_bsi_256_mb(self) -> None:
        hits: list[str] = []
        for rel in _SURFACES:
            path = _REPO / rel
            text = path.read_text(encoding="utf-8")
            for i, line in enumerate(text.splitlines(), start=1):
                if _FALSE_MIB_ALIGNMENT.search(line):
                    hits.append(f"{rel}:{i}:{line.strip()[:160]}")
        self.assertEqual(
            hits,
            [],
            msg="256 MiB is comparable to bSI 256 MB, not identical:\n" + "\n".join(hits),
        )
        readme = (_REPO / "README.md").read_text(encoding="utf-8")
        self.assertIn("Comparable to the buildingSMART Validation Service cap of 256 MB", readme)
        self.assertNotIn("согласовано с лимитом сервиса валидации", readme)


if __name__ == "__main__":
    unittest.main()
