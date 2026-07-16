# pyright: reportMissingImports=false

"""OfficeDocumentIngestor — Docling when available; plain-text / fail-closed otherwise."""

from __future__ import annotations

import re
from pathlib import Path

from aerobim.domain.models import RequirementSource, SourceKind

_TEXT_SUFFIXES = {".txt", ".md", ".csv"}
_OFFICE_SUFFIXES = {".docx", ".xlsx", ".pptx", ".doc", ".xls", ".odt", ".ods"}


class DoclingOfficeDocumentIngestor:
    """Extract text from MS Office / LibreOffice documents into RequirementSource."""

    def ingest(self, path: Path) -> RequirementSource:
        if not path.exists():
            raise FileNotFoundError(path)

        suffix = path.suffix.lower()
        text = self._load_text(path, suffix)
        kind = (
            SourceKind.TECHNICAL_SPECIFICATION
            if suffix in _OFFICE_SUFFIXES
            else SourceKind.STRUCTURED_TEXT
        )
        return RequirementSource(
            text=text,
            path=path,
            source_kind=kind,
            source_id=path.stem,
            doc_type=suffix.lstrip(".") or None,
        )

    def _load_text(self, path: Path, suffix: str) -> str:
        if suffix in _TEXT_SUFFIXES:
            return path.read_text(encoding="utf-8")

        try:
            from docling.document_converter import DocumentConverter
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Docling is required for MS Office ingest "
                "(pip install aerobim-backend[docling]); "
                f"cannot read {suffix}"
            ) from exc

        converter = DocumentConverter()
        result = converter.convert(str(path))
        return self._normalize_markdown(result.document.export_to_markdown())

    def _normalize_markdown(self, markdown: str) -> str:
        normalized_lines: list[str] = []
        for line in markdown.splitlines():
            stripped = line.strip()
            if not stripped:
                normalized_lines.append("")
                continue
            stripped = re.sub(r"^#+\s*", "", stripped)
            stripped = re.sub(r"^[-*+]\s*", "", stripped)
            stripped = stripped.replace(r"\_", "_")
            normalized_lines.append(stripped)
        return "\n".join(normalized_lines)
