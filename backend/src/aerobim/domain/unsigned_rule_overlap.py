
"""Overlap between unsigned educational packs (not a customer defect list).

``samples/requirements/samolet-*.txt`` (eq/gte/lte on ALL) and
``samples/rule-packs/residential-ar-reference-template.json`` (mostly exists)
share (entity, pset, property) keys. Running both inflates SIG-01 volume.
That is a pack-composition artifact, not two independent defects.
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Final

from aerobim.domain.checkpoint import CHECKPOINT

CLAIM_LEVEL: Final = "pack_volume_not_accuracy"
CLAIM_BOUNDARY: Final = (
    "Unsigned educational packs overlap on the same IFC property. "
    "Summing both rule ids is not two defects. Not SP. Not accuracy. "
    "Checkpoint GO (regulatory_measurement_mvp; customer_go false)."
)

_UNSIGNED_PACKS: Final[tuple[str, ...]] = (
    "samples/requirements/samolet-fire-safety-rules.txt",
    "samples/requirements/samolet-structure-rules.txt",
    "samples/rule-packs/residential-ar-reference-template.json",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def normalize_ifc_entity(token: str | None) -> str:
    """IfcWall / IFCWALL / ifcwall → IFCWALL."""

    raw = (token or "").strip()
    if not raw:
        return ""
    if raw.lower().startswith("ifc"):
        return "IFC" + raw[3:].upper()
    return raw.upper()


def property_key(
    ifc_entity: str | None, property_set: str | None, property_name: str | None
) -> tuple[str, str, str] | None:
    entity = normalize_ifc_entity(ifc_entity)
    pset = (property_set or "").strip()
    name = (property_name or "").strip()
    if not entity or not pset or not name:
        return None
    return (entity, pset, name)


def _parse_pipe_pack(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split("|")
        if len(parts) < 7:
            continue
        rows.append(
            {
                "rule_id": parts[0].strip(),
                "ifc_entity": parts[2].strip(),
                "property_set": parts[4].strip(),
                "property_name": parts[5].strip(),
                "operator": parts[6].strip(),
                "pack": path.name,
            }
        )
    return rows


def _parse_json_pack(path: Path) -> list[dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows: list[dict[str, str]] = []
    for item in payload.get("rules") or []:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "rule_id": str(item.get("rule_id") or "").strip(),
                "ifc_entity": str(item.get("ifc_entity") or "").strip(),
                "property_set": str(item.get("property_set") or "").strip(),
                "property_name": str(item.get("property_name") or "").strip(),
                "operator": str(item.get("operator") or "").strip(),
                "pack": path.name,
            }
        )
    return rows


def load_unsigned_rule_rows(root: Path | None = None) -> list[dict[str, str]]:
    base = root or _repo_root()
    rows: list[dict[str, str]] = []
    for rel in _UNSIGNED_PACKS:
        path = base / rel
        if not path.is_file():
            continue
        if path.suffix.lower() == ".json":
            rows.extend(_parse_json_pack(path))
        else:
            rows.extend(_parse_pipe_pack(path))
    return rows


def overlap_groups(root: Path | None = None) -> list[dict[str, Any]]:
    """Groups of unsigned rules that share entity+pset+property."""

    buckets: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in load_unsigned_rule_rows(root):
        key = property_key(row.get("ifc_entity"), row.get("property_set"), row.get("property_name"))
        if key is None or not row.get("rule_id"):
            continue
        buckets[key].append(row)
    groups: list[dict[str, Any]] = []
    for (entity, pset, name), members in sorted(buckets.items()):
        rule_ids = tuple(sorted({item["rule_id"] for item in members}))
        if len(rule_ids) < 2:
            continue
        groups.append(
            {
                "ifc_entity": entity,
                "property_set": pset,
                "property_name": name,
                "rule_ids": list(rule_ids),
                "operators": sorted({item["operator"] for item in members if item.get("operator")}),
                "packs": sorted({item["pack"] for item in members}),
            }
        )
    return groups


def active_overlap_groups(
    rule_ids: Iterable[str], root: Path | None = None
) -> list[dict[str, Any]]:
    """Overlap groups that have two or more member rules present in *rule_ids*."""

    present = {item for item in rule_ids if item}
    active: list[dict[str, Any]] = []
    for group in overlap_groups(root):
        hit = [rule_id for rule_id in group["rule_ids"] if rule_id in present]
        if len(hit) < 2:
            continue
        row = dict(group)
        row["present_rule_ids"] = hit
        active.append(row)
    return active


def overlap_snapshot(root: Path | None = None) -> dict[str, Any]:
    groups = overlap_groups(root)
    return {
        "artifact_type": "unsigned_rule_overlap",
        "claim_level": CLAIM_LEVEL,
        "checkpoint": CHECKPOINT,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "group_count": len(groups),
        "groups": groups,
        "is_customer_defect_list": False,
        "is_accuracy": False,
    }


__all__ = [
    "CLAIM_BOUNDARY",
    "active_overlap_groups",
    "load_unsigned_rule_rows",
    "normalize_ifc_entity",
    "overlap_groups",
    "overlap_snapshot",
    "property_key",
]
