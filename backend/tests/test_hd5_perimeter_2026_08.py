"""HD5 perimeter remediations: PDF literal CR/LF, documented DDL bootstrap."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.core.simple_pdf import escape_pdf_literal, write_simple_pdf
from aerobim.infrastructure.adapters.postgres_audit_store import PostgresAuditStore


class SimplePdfEscapeTests(unittest.TestCase):
    def test_cr_lf_do_not_remain_in_literal(self) -> None:
        escaped = escape_pdf_literal("a\rb\nc")
        self.assertNotIn("\r", escaped)
        self.assertNotIn("\n", escaped)
        self.assertEqual(escaped, "a b c")

    def test_parens_and_backslash_escaped(self) -> None:
        self.assertEqual(escape_pdf_literal("x\\y (z)"), "x\\\\y \\(z\\)")

    def test_write_pdf_with_cr_is_still_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cr.pdf"
            write_simple_pdf(path, ["line\rwith CR"], lines_per_page=50)
            data = path.read_bytes()
        self.assertTrue(data.startswith(b"%PDF"))
        self.assertNotIn(b"(line\rwith CR)", data)


class PostgresDdlBoundaryTests(unittest.TestCase):
    def test_hd5_ddl_privilege_boundary_is_documented(self) -> None:
        doc = PostgresAuditStore.__doc__ or ""
        self.assertIn("HD5-PGSQL-02", doc)
        self.assertIn("DML-only", doc)


if __name__ == "__main__":
    unittest.main()
