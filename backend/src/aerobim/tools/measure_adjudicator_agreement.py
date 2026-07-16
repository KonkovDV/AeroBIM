"""Cohen's κ / Krippendorff's α helpers for dual-human adjudication CSVs."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path


def cohen_kappa(labels_a: list[str], labels_b: list[str]) -> float:
    """Chance-corrected agreement for two raters, same item order."""

    if len(labels_a) != len(labels_b):
        raise ValueError("label vectors must have equal length")
    n = len(labels_a)
    if n == 0:
        raise ValueError("empty label vectors")

    categories = sorted(set(labels_a) | set(labels_b))
    agree = sum(1 for a, b in zip(labels_a, labels_b, strict=True) if a == b)
    p_o = agree / n

    count_a = Counter(labels_a)
    count_b = Counter(labels_b)
    p_e = sum((count_a[c] / n) * (count_b[c] / n) for c in categories)
    if abs(1.0 - p_e) < 1e-12:
        return 1.0 if p_o == 1.0 else 0.0
    return (p_o - p_e) / (1.0 - p_e)


def _item_key(row: dict[str, str]) -> str:
    finding_id = (row.get("finding_id") or "").strip()
    if finding_id:
        return finding_id
    parts = [
        (row.get("case_id") or "").strip(),
        (row.get("finding_class") or "").strip(),
        (row.get("rule_id") or "").strip(),
        (row.get("target_ref") or "").strip(),
        (row.get("element_guid") or "").strip(),
        (row.get("match_key") or "").strip(),
    ]
    return "|".join(parts)


def measure_adjudication_csv(path: Path) -> dict[str, object]:
    """Load adjudication template CSV and compute dual-rater Cohen's κ."""

    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    by_item: dict[str, dict[str, str]] = defaultdict(dict)
    for row in rows:
        adjudicator = (row.get("adjudicator_id") or "").strip()
        verdict = (row.get("verdict") or "").strip().upper()
        if not adjudicator or not verdict:
            continue
        by_item[_item_key(row)][adjudicator] = verdict

    adjudicators = sorted({aid for mapping in by_item.values() for aid in mapping})
    if len(adjudicators) < 2:
        raise ValueError("need at least two distinct adjudicator_id values")

    a_id, b_id = adjudicators[0], adjudicators[1]
    paired_a: list[str] = []
    paired_b: list[str] = []
    confusion: Counter[tuple[str, str]] = Counter()
    for mapping in by_item.values():
        if a_id not in mapping or b_id not in mapping:
            continue
        va, vb = mapping[a_id], mapping[b_id]
        paired_a.append(va)
        paired_b.append(vb)
        confusion[(va, vb)] += 1

    if not paired_a:
        raise ValueError("no overlapping items between the first two adjudicators")

    kappa = cohen_kappa(paired_a, paired_b)
    matrix = {
        f"{a}/{b}": count for (a, b), count in sorted(confusion.items())
    }
    return {
        "artifact_type": "adjudicator_agreement",
        "schema_version": "1.0.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "source_csv": str(path.as_posix()),
        "adjudicator_a": a_id,
        "adjudicator_b": b_id,
        "paired_items": len(paired_a),
        "cohens_kappa": round(kappa, 4),
        "confusion_matrix": matrix,
        "pass_threshold_0_60": kappa >= 0.60,
        "target_threshold_0_80": kappa >= 0.80,
        "notes": [
            "LLM assist does not count as an adjudicator",
            "Report confusion matrix with F1 for publishable PrecisionClaim",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Measure Cohen's κ from dual-human adjudication CSV"
    )
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    payload = measure_adjudication_csv(args.csv)
    serialized = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        tmp = args.output.with_suffix(".tmp")
        tmp.write_text(serialized, encoding="utf-8")
        tmp.replace(args.output)
    else:
        print(serialized)

    if not payload["pass_threshold_0_60"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
