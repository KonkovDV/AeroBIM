"""XML parse limits — billion-laughs / entity / element-count protection."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from xml.etree.ElementTree import Element, ElementTree, ParseError

DEFAULT_MAX_XML_BYTES = 16 * 1024 * 1024  # 16 MiB
DEFAULT_MAX_ELEMENTS = 200_000
DEFAULT_MAX_DEPTH = 64
DEFAULT_MAX_TEXT_CHARS = 1_000_000


class XmlBombError(ValueError):
    """Raised when XML input exceeds safe size or element-count limits."""


def _require_defusedxml() -> tuple[Any, type[Exception]]:
    try:
        from defusedxml import ElementTree as DefusedET
        from defusedxml.common import DefusedXmlException
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "defusedxml is required to parse untrusted XML. "
            "Install AeroBIM dependencies (defusedxml>=0.7.1)."
        ) from exc
    return DefusedET, DefusedXmlException


def _count_elements(root: Element) -> int:
    return sum(1 for _ in root.iter())


def _enforce_element_cap(root: Element, *, max_elements: int) -> None:
    count = _count_elements(root)
    if count > max_elements:
        raise XmlBombError(f"XML has too many elements ({count} > {max_elements})")


def _element_depth(root: Element) -> int:
    max_depth = 1
    stack: list[tuple[Element, int]] = [(root, 1)]
    while stack:
        node, depth = stack.pop()
        max_depth = max(max_depth, depth)
        next_depth = depth + 1
        stack.extend((child, next_depth) for child in list(node))
    return max_depth


def _enforce_depth_and_text_caps(
    root: Element,
    *,
    max_depth: int,
    max_text_chars: int,
) -> None:
    if _element_depth(root) > max_depth:
        raise XmlBombError(f"XML nesting exceeds maximum depth ({max_depth})")
    for node in root.iter():
        for chunk in (node.text, node.tail):
            if chunk is not None and len(chunk) > max_text_chars:
                raise XmlBombError(
                    f"XML text node exceeds maximum length ({len(chunk)} > {max_text_chars})"
                )


def safe_fromstring(
    data: bytes | str,
    *,
    max_bytes: int = DEFAULT_MAX_XML_BYTES,
    max_elements: int = DEFAULT_MAX_ELEMENTS,
    max_depth: int = DEFAULT_MAX_DEPTH,
    max_text_chars: int = DEFAULT_MAX_TEXT_CHARS,
) -> Element:
    """Parse XML from bytes/str with size + element caps (defusedxml)."""

    DefusedET, DefusedXmlException = _require_defusedxml()
    if isinstance(data, str):
        payload_size = len(data.encode("utf-8"))
    else:
        payload_size = len(data)
    if payload_size > max_bytes:
        raise XmlBombError(f"XML payload too large ({payload_size} > {max_bytes})")
    try:
        root = DefusedET.fromstring(data, forbid_entities=True, forbid_external=True)
    except DefusedXmlException as exc:
        raise XmlBombError(f"XML rejected by defusedxml: {exc}") from exc
    except ParseError:
        raise
    _enforce_element_cap(root, max_elements=max_elements)
    _enforce_depth_and_text_caps(root, max_depth=max_depth, max_text_chars=max_text_chars)
    return cast(Element, root)


def safe_parse(
    path: Path,
    *,
    max_bytes: int = DEFAULT_MAX_XML_BYTES,
    max_elements: int = DEFAULT_MAX_ELEMENTS,
    max_depth: int = DEFAULT_MAX_DEPTH,
    max_text_chars: int = DEFAULT_MAX_TEXT_CHARS,
) -> ElementTree:
    """Parse XML from a filesystem path with size + element caps (defusedxml)."""

    DefusedET, DefusedXmlException = _require_defusedxml()
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise XmlBombError(f"XML file is not readable: {exc}") from exc
    if size > max_bytes:
        raise XmlBombError(f"XML file too large ({size} > {max_bytes})")
    try:
        tree = DefusedET.parse(path, forbid_entities=True, forbid_external=True)
    except DefusedXmlException as exc:
        raise XmlBombError(f"XML rejected by defusedxml: {exc}") from exc
    except ParseError:
        raise
    root = tree.getroot()
    _enforce_element_cap(root, max_elements=max_elements)
    _enforce_depth_and_text_caps(root, max_depth=max_depth, max_text_chars=max_text_chars)
    return cast(ElementTree, tree)


__all__ = [
    "DEFAULT_MAX_DEPTH",
    "DEFAULT_MAX_ELEMENTS",
    "DEFAULT_MAX_TEXT_CHARS",
    "DEFAULT_MAX_XML_BYTES",
    "XmlBombError",
    "safe_fromstring",
    "safe_parse",
]
