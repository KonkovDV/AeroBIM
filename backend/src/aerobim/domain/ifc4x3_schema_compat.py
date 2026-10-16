"""Pre-final IFC4x3 FILE_SCHEMA tokens and their mapping to IFC4X3_ADD2.

IfcOpenShell 0.9 ships only the final IFC4X3_ADD2 schema. Exporters still
write ``IFC4X3``, ``IFC4X3_ADD1`` or ``IFC4X3_TC1``; those files usually parse
against ADD2. AeroBIM opens them as ADD2 and reports a schema WARNING; a file
that does not parse under ADD2 is still rejected by the kernel error.
"""

from __future__ import annotations

import re
from typing import Final

PRE_FINAL_IFC4X3: Final[frozenset[str]] = frozenset({"IFC4X3", "IFC4X3_ADD1", "IFC4X3_TC1"})
IFC4X3_FINAL: Final[str] = "IFC4X3_ADD2"

_HEADER_SCHEMA_RE = re.compile(
    rb"(FILE_SCHEMA\s*\(\s*\(\s*')([^']+)(')",
    re.IGNORECASE,
)


def is_pre_final_ifc4x3(token: str | None) -> bool:
    if not token:
        return False
    return token.strip().upper().replace(" ", "").replace(".", "") in PRE_FINAL_IFC4X3


def rewrite_header_schema(header: bytes) -> tuple[bytes, str | None]:
    """Replace a pre-final IFC4x3 FILE_SCHEMA token with IFC4X3_ADD2.

    Returns ``(header, original_token)``; ``original_token`` is None when the
    header carries no pre-final token (header returned unchanged).
    """

    match = _HEADER_SCHEMA_RE.search(header)
    if match is None:
        return header, None
    token = match.group(2).decode("ascii", errors="replace")
    if not is_pre_final_ifc4x3(token):
        return header, None
    start, end = match.span(2)
    return header[:start] + IFC4X3_FINAL.encode("ascii") + header[end:], token
