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
    information_level: str = "alphanumeric"
    """LOIN information level: ``geometry`` | ``alphanumeric`` | ``documentation``."""


class LoinMetadataResolver:
    """Fail-soft: LOIN metadata is export enrichment (verdict-neutral). A missing
    or corrupt manifest must degrade to 'no metadata' with a visible flag, never
    crash the server at import time (offline-smoke finding 2026-07-31: the
    production image shipped without samples/ and died on startup)."""

    def __init__(self, manifest_path: Path | None = None) -> None:
        path = manifest_path or (
            Path(__file__).resolve().parents[5]
            / "samples"
            / "benchmarks"
            / "loin-rule-metadata.json"
        )
        self.available = False
        self.degrade_reason: str | None = None
        self._rules: list[tuple[str, LoinMetadata]] = []
        try:
            with open(path, encoding="utf-8") as fh:
                payload = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            self.degrade_reason = f"LOIN metadata manifest unavailable: {exc}"
            return
        self.available = True
        for entry in payload.get("rules", []):
            prefix = str(entry.get("rule_id_prefix", "")).strip()
            if not prefix:
                continue
            level = str(entry.get("information_level", "alphanumeric")).strip().lower()
            if level not in {"geometry", "alphanumeric", "documentation"}:
                level = "alphanumeric"
            self._rules.append(
                (
                    prefix,
                    LoinMetadata(
                        purpose=str(entry.get("purpose", "")),
                        milestone=str(entry.get("milestone", "")),
                        actor=str(entry.get("actor", "")),
                        information_level=level,
                    ),
                )
            )

    def resolve(self, rule_id: str) -> LoinMetadata | None:
        for prefix, metadata in self._rules:
            if rule_id.startswith(prefix):
                return metadata
        return None
