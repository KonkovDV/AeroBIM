"""Map Samolet typical-error catalog entries to AeroBIM rule_id coverage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def default_catalog_path() -> Path:
    return repo_root() / "samples" / "benchmarks" / "samolet-typical-errors-catalog.json"


def default_rules_dir() -> Path:
    return repo_root() / "samples" / "requirements"


def _collect_rule_ids(rules_dir: Path) -> set[str]:
    rule_ids: set[str] = set()
    for path in sorted(rules_dir.glob("*.txt")):
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "|" in stripped and not stripped.startswith("rule_id"):
                rule_ids.add(stripped.split("|", 1)[0].strip())
    return rule_ids


def map_typical_errors(
    catalog_path: Path,
    rules_dir: Path,
) -> dict[str, object]:
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    patterns = catalog.get("patterns", [])
    rule_ids = _collect_rule_ids(rules_dir)

    rows: list[dict[str, object]] = []
    covered = 0
    for entry in patterns:
        error_id = str(entry.get("error_id", ""))
        prefix = entry.get("maps_to_rule_prefix")
        category = entry.get("maps_to_category")
        matched: list[str] = []
        if prefix:
            matched = sorted(rid for rid in rule_ids if rid.upper().startswith(str(prefix).upper()))
        status = "covered" if matched else ("category-only" if category else "unmapped")
        if matched:
            covered += 1
        rows.append(
            {
                "error_id": error_id,
                "title_ru": entry.get("title_ru"),
                "status": status,
                "matched_rule_ids": matched,
                "maps_to_rule_prefix": prefix,
                "maps_to_category": category,
            }
        )

    total = len(patterns)
    return {
        "artifact_type": "samolet_typical_errors_mapping",
        "schema_version": "1.0.0",
        "catalog_id": catalog.get("catalog_id"),
        "patterns_total": total,
        "patterns_with_rule_match": covered,
        "coverage_ratio": round(covered / total, 3) if total else 0.0,
        "known_rule_ids_count": len(rule_ids),
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Map Samolet typical-error catalog to rule_ids")
    parser.add_argument("--catalog", type=Path, default=default_catalog_path())
    parser.add_argument("--rules-dir", type=Path, default=default_rules_dir())
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    payload = map_typical_errors(args.catalog, args.rules_dir)
    serialized = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        tmp = args.output.with_suffix(".tmp")
        tmp.write_text(serialized, encoding="utf-8")
        tmp.replace(args.output)
    else:
        print(serialized)


if __name__ == "__main__":
    main()
