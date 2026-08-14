"""Classify in-repo deterministic rules by Solihin & Eastman (2015) classes 1–4.

Class 4 is listed so it is explicitly **not claimed**. This is an engineering
inventory, not product accuracy and not a statutory completeness claim.

Reference: Solihin, W. & Eastman, C. (2015). Classification of rules for
automated BIM rule checking development. Automation in Construction, 53, 69–82.
https://doi.org/10.1016/j.autcon.2015.03.003
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aerobim.tools.benchmark_project_package import repo_root
from aerobim.tools.map_typical_errors import _collect_rule_ids


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


CLAIM_BOUNDARY = (
    "Engineering classification of in-repo rule identifiers. "
    "Solihin class 4 (performance / proof-of-solution) is not claimed. "
    "Not customer accuracy. Not statutory PP-87 completeness."
)
SOURCE = "https://doi.org/10.1016/j.autcon.2015.03.003"

# Prefix → class. First match wins. Class 4 entries are honesty (not claimed).
_PREFIX_CLASS: tuple[tuple[str, int, str], ...] = (
    ("AEROBIM-CALCULATION-CORRECTNESS", 4, "independent calc correctness not claimed"),
    ("AEROBIM-AGENT-", 4, "advisory agent path; never sets Shared-gate"),
    ("AEROBIM-INTERPRET-IDS-DRAFT", 4, "LLM/IDS draft; advisory"),
    ("DRAWING-ADVISORY", 4, "advisory drawing read; not verdict"),
    ("DEGRADED-SCAN", 4, "synthetic degrade fixture; not product CV"),
    ("AEROBIM-CLASH", 3, "spatial / interference (geometry_verified=False unless extra)"),
    ("AEROBIM-MEP-", 3, "federated MEP / RT-003; not verified"),
    ("AEROBIM-LOGIC", 3, "extended conditional / cross-doc logic"),
    ("AEROBIM-QTY", 2, "derived quantity compare"),
    ("AEROBIM-LOAD-", 2, "spreadsheet vs model derived check"),
    ("OPENREBAR-", 2, "rebar derived quantities / waste; fixture"),
    ("AEROBIM-CAD", 1, "CAD ingest honesty; native DWG stays FAILED"),
    ("AEROBIM-PACKAGE-", 1, "declared inventory / naming / pairing"),
    ("AEROBIM-IFC-", 1, "schema / GUID explicit data"),
    ("AEROBIM-GUID-", 1, "explicit identifier"),
    ("AEROBIM-IDS-", 1, "IDS attribute/existence"),
    ("AEROBIM-SIGNATURE-", 1, "envelope presence; not УКЭП legal validity"),
    ("AEROBIM-BSI-", 1, "schema certificate presence"),
    ("AEROBIM-CUSTOMER-INTAKE", 1, "intake completeness"),
    ("AEROBIM-DRAWING-", 1, "text-layer / annotation explicit value"),
    ("AEROBIM-NORM-PACK", 1, "pack status / eligibility"),
    ("AEROBIM-REVISION", 1, "revision / edition label"),
    ("AEROBIM-SHEET", 1, "sheet identity / naming"),
    ("AEROBIM-UNIT", 1, "declared unit / scale"),
    ("SAM-AR-", 1, "synthetic AR property exists"),
    ("SAM-R-", 1, "synthetic residential template"),
    ("V2-AR-", 1, "schema 2 AR draft template"),
    ("REQ-", 1, "fixture requirement text rules"),
    ("EN-SPACE", 1, "English space property fixture"),
    ("EN-WALL", 1, "English wall property fixture"),
    ("IDS-WALLHEIGHT", 1, "IDS height existence fixture"),
    ("AEROBIM-DETERMINISM-", 1, "advisory vs engine divergence honesty"),
)


def classify_rule(rule_id: str) -> tuple[int, str]:
    """Return (solihin_class, reason). Unknown rules stay class 1-unclassified as 0."""

    upper = rule_id.upper()
    for prefix, klass, reason in _PREFIX_CLASS:
        if upper.startswith(prefix.upper()):
            return klass, reason
    return 0, "unclassified prefix — listed, not claimed as class 1–4 coverage"


def build_solihin_inventory(*, root: Path | None = None) -> dict[str, Any]:
    repo = root or repo_root()
    rule_ids = sorted(
        _collect_rule_ids(
            repo / "samples" / "requirements",
            repo / "samples" / "rule-packs",
            repo / "backend" / "src",
        )
    )
    rows: list[dict[str, Any]] = []
    counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    for rule_id in rule_ids:
        klass, reason = classify_rule(rule_id)
        counts[klass] += 1
        rows.append(
            {
                "rule_id": rule_id,
                "solihin_class": klass,
                "claimed": klass in {1, 2, 3},
                "reason": reason,
            }
        )
    payload: dict[str, Any] = {
        "artifact_type": "solihin_rule_classes",
        "schema_version": "1.0.0",
        "claim_level": "engineering_inventory",
        "claim_boundary": CLAIM_BOUNDARY,
        "source": SOURCE,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "class_4_not_claimed": True,
        "summary": {
            "rule_count": len(rule_ids),
            "class_1_explicit": counts[1],
            "class_2_derived": counts[2],
            "class_3_extended": counts[3],
            "class_4_not_claimed": counts[4],
            "unclassified": counts[0],
        },
        "rules": rows,
    }
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    payload["content_sha256"] = hashlib.sha256(encoded).hexdigest()
    return payload


def render_solihin_markdown(payload: dict[str, Any]) -> str:
    summary = _mapping(payload.get("summary"))
    return "\n".join(
        [
            '<!-- claims-lint: allow-file reason="Solihin class inventory; class 4 listed as not claimed" -->',
            "# Solihin & Eastman rule-class inventory",
            "",
            str(payload.get("claim_boundary") or ""),
            "",
            f"Source: {payload.get('source')}",
            "",
            "| Class | Meaning | Count | Claimed? |",
            "| --- | --- | ---: | --- |",
            f"| 1 | Explicit data (attribute / existence / naming) | {summary.get('class_1_explicit')} | yes, fixture |",
            f"| 2 | Derived / simple calculated | {summary.get('class_2_derived')} | yes, fixture |",
            f"| 3 | Extended conditions (spatial / system) | {summary.get('class_3_extended')} | fixture / not verified |",
            f"| 4 | Performance / proof-of-solution | {summary.get('class_4_not_claimed')} | **not claimed** |",
            f"| 0 | Unclassified prefix | {summary.get('unclassified')} | listed only |",
            "",
            f"content_sha256: `{payload.get('content_sha256')}`",
            "",
        ]
    )


def write_solihin_inventory(
    payload: dict[str, Any], *, evidence_json: Path, evidence_md: Path
) -> None:
    evidence_json.parent.mkdir(parents=True, exist_ok=True)
    evidence_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    evidence_md.write_text(render_solihin_markdown(payload), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    root = repo_root()
    payload = build_solihin_inventory(root=root)
    write_solihin_inventory(
        payload,
        evidence_json=root / "docs" / "evidence" / "solihin-rule-classes-2026-08.json",
        evidence_md=root / "docs" / "evidence" / "solihin-rule-classes-2026-08.md",
    )
    print(json.dumps(payload.get("summary"), ensure_ascii=False, indent=2))
    print("content_sha256", payload.get("content_sha256"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
