"""LOIN metadata resolver for report exports (ISO 7817-1 via 19650 draft alignment)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LoinMetadata:
    purpose: str
    milestone: str
    actor: str


class LoinMetadataResolver:
    def __init__(self, manifest_path: Path | None = None) -> None:
        path = manifest_path or (
            Path(__file__).resolve().parents[5]
            / "samples"
            / "benchmarks"
            / "loin-rule-metadata.json"
        )
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
        self._rules: list[tuple[str, LoinMetadata]] = []
        for entry in payload.get("rules", []):
            prefix = str(entry.get("rule_id_prefix", "")).strip()
            if not prefix:
                continue
            self._rules.append(
                (
                    prefix,
                    LoinMetadata(
                        purpose=str(entry.get("purpose", "")),
                        milestone=str(entry.get("milestone", "")),
                        actor=str(entry.get("actor", "")),
                    ),
                )
            )

    def resolve(self, rule_id: str) -> LoinMetadata | None:
        for prefix, metadata in self._rules:
            if rule_id.startswith(prefix):
                return metadata
        return None
