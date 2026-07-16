"""Map Samolet typical-error entries to rule ids and finding classes.

Mapping is traceability, not a precision or implementation claim.  The output keeps
rule-level coverage, class-only mapping, and explicit gaps separate.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

_STATIC_RULE_ID_RE = re.compile(r"rule_id\s*=\s*[\"']([A-Za-z0-9._:-]+)[\"']")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def default_catalog_path() -> Path:
    return repo_root() / "samples" / "benchmarks" / "samolet-typical-errors-catalog.json"


def default_rules_dir() -> Path:
    return repo_root() / "samples" / "requirements"


def default_rule_packs_dir() -> Path:
    return repo_root() / "samples" / "rule-packs"


def default_source_dir() -> Path:
    return repo_root() / "backend" / "src"


def _collect_rule_ids(
    rules_dir: Path,
    rule_packs_dir: Path | None = None,
    source_dir: Path | None = None,
) -> set[str]:
    rule_ids: set[str] = set()
    for path in sorted(rules_dir.glob("*.txt")):
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "|" in stripped and not stripped.startswith("rule_id"):
                rule_ids.add(stripped.split("|", 1)[0].strip())

    effective_pack_dir = rule_packs_dir or rules_dir.parent / "rule-packs"
    if effective_pack_dir.exists():
        for path in sorted(effective_pack_dir.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if not isinstance(payload, dict) or not isinstance(payload.get("rules"), list):
                continue
            for rule in payload["rules"]:
                if isinstance(rule, dict) and isinstance(rule.get("rule_id"), str):
                    rule_ids.add(rule["rule_id"].strip())

    effective_source_dir = source_dir
    if effective_source_dir is None:
        candidate = rules_dir.parents[1] / "backend" / "src"
        effective_source_dir = candidate if candidate.exists() else None
    if effective_source_dir is not None and effective_source_dir.exists():
        for path in sorted(effective_source_dir.rglob("*.py")):
            text = path.read_text(encoding="utf-8")
            rule_ids.update(_STATIC_RULE_ID_RE.findall(text))
    return {rule_id for rule_id in rule_ids if rule_id}


def map_typical_errors(
    catalog_path: Path,
    rules_dir: Path,
    *,
    rule_packs_dir: Path | None = None,
    source_dir: Path | None = None,
) -> dict[str, object]:
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    patterns = catalog.get("patterns", [])
    if not isinstance(patterns, list):
        raise ValueError("Typical-error catalog patterns must be an array")
    rule_ids = _collect_rule_ids(rules_dir, rule_packs_dir, source_dir)

    rows: list[dict[str, object]] = []
    rule_covered = 0
    class_mapped = 0
    explicit_gaps = 0
    implementation_ready = 0
    for entry in patterns:
        if not isinstance(entry, dict):
            raise ValueError("Each typical-error catalog pattern must be an object")
        error_id = str(entry.get("error_id", ""))
        prefix = entry.get("maps_to_rule_prefix")
        category = entry.get("maps_to_category")
        implementation_status = str(entry.get("implementation_status", "intake"))
        raw_explicit_ids = entry.get("maps_to_rule_ids", [])
        if not isinstance(raw_explicit_ids, list):
            raise ValueError(f"{error_id}: maps_to_rule_ids must be an array")
        explicit_ids = {str(value) for value in raw_explicit_ids if str(value).strip()}

        matched = sorted(explicit_ids & rule_ids)
        if prefix:
            matched = sorted(
                set(matched)
                | {
                    rule_id
                    for rule_id in rule_ids
                    if rule_id.upper().startswith(str(prefix).upper())
                }
            )

        if implementation_status == "gap":
            status = "gap"
            explicit_gaps += 1
        elif matched:
            status = "covered"
            rule_covered += 1
        elif category:
            status = "category-only"
            class_mapped += 1
        else:
            status = "unmapped"

        if implementation_status == "implemented" and status in {"covered", "category-only"}:
            implementation_ready += 1
        rows.append(
            {
                "error_id": error_id,
                "title_ru": entry.get("title_ru"),
                "status": status,
                "implementation_status": implementation_status,
                "matched_rule_ids": matched,
                "declared_rule_ids": sorted(explicit_ids),
                "maps_to_rule_prefix": prefix,
                "maps_to_category": category,
                "roadmap_ref": entry.get("roadmap_ref"),
            }
        )

    total = len(patterns)
    mapped = rule_covered + class_mapped + explicit_gaps
    return {
        "artifact_type": "samolet_typical_errors_mapping",
        "schema_version": "1.1.0",
        "catalog_id": catalog.get("catalog_id"),
        "catalog_status": catalog.get("catalog_status"),
        "patterns_total": total,
        "customer_confirmed_patterns": catalog.get("customer_confirmed_patterns", 0),
        "patterns_with_rule_match": rule_covered,
        "patterns_with_class_only_mapping": class_mapped,
        "patterns_with_explicit_gap": explicit_gaps,
        "patterns_implementation_ready": implementation_ready,
        "coverage_ratio": round(rule_covered / total, 3) if total else 0.0,
        "mapping_ratio": round(mapped / total, 3) if total else 0.0,
        "known_rule_ids_count": len(rule_ids),
        "claim_boundary": (
            "Traceability mapping only; customer-confirmed detection precision requires "
            "an adjudicated corpus."
        ),
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Map Samolet typical-error catalog to rule ids and finding classes"
    )
    parser.add_argument("--catalog", type=Path, default=default_catalog_path())
    parser.add_argument("--rules-dir", type=Path, default=default_rules_dir())
    parser.add_argument("--rule-packs-dir", type=Path, default=default_rule_packs_dir())
    parser.add_argument("--source-dir", type=Path, default=default_source_dir())
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    payload = map_typical_errors(
        args.catalog,
        args.rules_dir,
        rule_packs_dir=args.rule_packs_dir,
        source_dir=args.source_dir,
    )
    serialized = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_suffix(args.output.suffix + ".tmp")
        temporary.write_text(serialized + "\n", encoding="utf-8")
        temporary.replace(args.output)
    else:
        print(serialized)


if __name__ == "__main__":
    main()
