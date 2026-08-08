"""WP-A6: runtime lock must ship Office ingest dependencies."""

from __future__ import annotations

import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
_LOCK = _BACKEND / "requirements-lock.txt"


@unittest.skipUnless(_LOCK.is_file(), "requirements-lock.txt missing")
class RuntimeLockOfficeTests(unittest.TestCase):
    def test_runtime_lock_lists_office_dependencies_with_hashes(self) -> None:
        text = _LOCK.read_text(encoding="utf-8")
        for package in ("python-docx", "openpyxl"):
            self.assertIn(f"{package}==", text.lower())
            self.assertIn("--hash=sha256:", text)

    def test_office_ingest_imports_resolve_under_core_dependencies(self) -> None:
        from aerobim.infrastructure.adapters.docling_office_document_ingestor import (
            DoclingOfficeDocumentIngestor,
        )

        self.assertTrue(callable(DoclingOfficeDocumentIngestor))


if __name__ == "__main__":
    unittest.main()
