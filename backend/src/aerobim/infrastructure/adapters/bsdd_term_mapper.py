"""Offline bSDD term mapper for pilot property names (C.3)."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from aerobim.domain.models import ParsedRequirement

_DEFAULT_TERMS_PATH = (
    Path(__file__).resolve().parents[5] / "samples" / "benchmarks" / "bsdd-pilot-terms.json"
)


class BsddTermMapper:
    """Map IFC property names to curated bSDD URIs (RU/EN aliases)."""

    def __init__(self, terms_path: Path | None = None) -> None:
        path = terms_path or _DEFAULT_TERMS_PATH
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
        self._by_property: dict[str, str] = {}
        for entry in payload.get("terms", []):
            uri = str(entry.get("bsdd_uri", "")).strip()
            if not uri:
                continue
            for key in entry.get("property_names", []):
                self._by_property[str(key).strip().lower()] = uri
            for alias in entry.get("aliases", []):
                self._by_property[str(alias).strip().lower()] = uri

    def resolve_uri(self, property_name: str | None) -> str | None:
        if property_name is None:
            return None
        return self._by_property.get(property_name.strip().lower())

    def enrich(self, requirement: ParsedRequirement) -> ParsedRequirement:
        uri = self.resolve_uri(requirement.property_name)
        if uri is None:
            return requirement
        return replace(requirement, bsdd_uri=uri)

    def enrich_all(self, requirements: list[ParsedRequirement]) -> list[ParsedRequirement]:
        return [self.enrich(req) for req in requirements]
