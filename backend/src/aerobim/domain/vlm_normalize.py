"""Deterministic normalizer for VLM raw reads (domain-pure).

Paraphrase-divergence defense (Enginuity 2026): a VLM often finds the right
object but rephrases its designation. We therefore IGNORE the model's own
``normalized_value`` and recompute it here with a deterministic, testable rule
per observation kind. The result is a *candidate*, never a verdict.
"""

from __future__ import annotations

import re

_WS = re.compile(r"\s+")
_ALLOWED_KINDS = frozenset({"text", "dimension", "designation", "table_row", "stamp_field"})


def is_allowed_kind(kind: str) -> bool:
    return kind.strip().lower() in _ALLOWED_KINDS


def normalize_observation_value(kind: str, raw_value: str) -> str | None:
    """Deterministic normalization; empty/whitespace → None. Model value ignored.

    - ``designation`` (marks/positions): drop internal whitespace, upper-case.
    - ``dimension``: decimal comma→dot, drop spaces (keep digits/units/signs).
    - ``text`` / ``table_row`` / ``stamp_field`` and any other: collapse
      internal whitespace to single spaces, strip.
    """
    text = (raw_value or "").strip()
    if not text:
        return None
    normalized_kind = kind.strip().lower()
    if normalized_kind == "designation":
        return _WS.sub("", text).upper()
    if normalized_kind == "dimension":
        return text.replace(",", ".").replace(" ", "")
    return _WS.sub(" ", text)


__all__ = ["is_allowed_kind", "normalize_observation_value"]
