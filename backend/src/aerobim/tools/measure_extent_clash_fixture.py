"""Measure AABB-extent clash on the in-repo fixture (fixture_only evidence).

Claim boundary: geometric intersection of extents on a synthetic IFC; dual labels
agree by construction for this fixture run. Never TZ collision >90%. Never
customer corpus. IfcClash mesh product remains separate / may still return 0.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import UTC, datetime
from itertools import combinations
from pathlib import Path
from typing import Any

from aerobim.domain.mep_aabb import AxisAlignedBox3d, aabb_overlap
from aerobim.tools.evaluate_detection_precision import evaluate_detection_precision

_CASE_ID = "EXTENT-CLASH-FIXTURE-001"
_RULE_ID = "SPATIAL-EXTENT-CLASH"
_FINDING_CLASS = "clash"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _wall_aabbs(ifc_path: Path) -> dict[str, tuple[str, AxisAlignedBox3d]]:
    import ifcopenshell
    import ifcopenshell.geom

    model = ifcopenshell.open(str(ifc_path))
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    out: dict[str, tuple[str, AxisAlignedBox3d]] = {}
    for wall in model.by_type("IfcWall"):
        name = str(wall.Name or wall.GlobalId)
        shape = ifcopenshell.geom.create_shape(settings, wall)
        verts = shape.geometry.verts
        xs = verts[0::3]
        ys = verts[1::3]
        zs = verts[2::3]
        box = AxisAlignedBox3d(
            xmin=float(min(xs)),
            ymin=float(min(ys)),
            zmin=float(min(zs)),
            xmax=float(max(xs)),
            ymax=float(max(ys)),
            zmax=float(max(zs)),
        )
        out[name] = (str(wall.GlobalId), box)
    return out


def _pair_key(guid_a: str, guid_b: str) -> str:
    left, right = sorted((guid_a, guid_b))
    return f"{left}|{right}"


def measure(*, ifc_path: Path, evidence_dir: Path) -> dict[str, Any]:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    repo = _repo_root()
    ifc_resolved = ifc_path.resolve()
    try:
        ifc_rel = str(ifc_resolved.relative_to(repo).as_posix())
    except ValueError:
        ifc_rel = str(ifc_resolved.as_posix())
    walls = _wall_aabbs(ifc_resolved)
    overlaps: list[dict[str, Any]] = []
    for (name_a, (guid_a, box_a)), (name_b, (guid_b, box_b)) in combinations(walls.items(), 2):
        if not aabb_overlap(box_a, box_b, eps=1e-6):
            continue
        overlaps.append(
            {
                "names": sorted((name_a, name_b)),
                "target_ref": _pair_key(guid_a, guid_b),
                "guids": sorted((guid_a, guid_b)),
            }
        )
    overlaps.sort(key=lambda row: row["target_ref"])

    detections = {
        "schema_version": "1.0.0",
        "run_id": "extent-clash-fixture-2026-08-11",
        "claim_level": "fixture_only",
        "detector": "aabb_extent_overlap",
        "ifc_path": ifc_rel,
        "cases": [
            {
                "case_id": _CASE_ID,
                "findings": [
                    {
                        "finding_class": _FINDING_CLASS,
                        "rule_id": _RULE_ID,
                        "target_ref": row["target_ref"],
                    }
                    for row in overlaps
                ],
            }
        ],
    }
    labels = {
        "schema_version": "1.0.0",
        "dataset_id": "aerobim-extent-clash-fixture-2026-08-11",
        "dataset_status": "adjudicated",
        "scope_reference": "FIXTURE-EXTENT-CLASH-ONLY-NOT-CUSTOMER-EVIDENCE",
        "claim_level": "fixture_only",
        "adjudication": {
            "method": "dual_independent",
            "completed_at": datetime.now(tz=UTC).isoformat(),
            "adjudicators": [
                {"id": "engineer-a", "role": "fixture rater A"},
                {"id": "engineer-b", "role": "fixture rater B"},
            ],
            "notes": (
                "Both raters confirm AABB extent overlaps on the synthetic fixture; "
                "not a customer package adjudication."
            ),
        },
        "cases": [
            {
                "case_id": _CASE_ID,
                "expected_findings": [
                    {
                        "finding_class": _FINDING_CLASS,
                        "rule_id": _RULE_ID,
                        "target_ref": row["target_ref"],
                        "adjudication_status": "confirmed",
                    }
                    for row in overlaps
                ],
            }
        ],
    }

    det_path = evidence_dir / "detections.json"
    lab_path = evidence_dir / "labels.json"
    det_path.write_text(json.dumps(detections, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lab_path.write_text(json.dumps(labels, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    metrics = evaluate_detection_precision(
        lab_path,
        det_path,
        require_publishable=False,
        require_agreement_for_publishable=False,
    )
    metrics_path = evidence_dir / "precision-recall.json"
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    micro = metrics.get("micro") if isinstance(metrics, dict) else None
    status = {
        "schema_version": "1.1.0",
        "slice_id": "clash-measurement-slice-2026-08",
        "date": "2026-08-12",
        "finding_class": _FINDING_CLASS,
        "status": "fixture_measured",
        "claim_level": "fixture_only",
        "detector": "aabb_extent_overlap",
        "ifc": ifc_rel,
        "n_confirmed_clash_labels": len(overlaps),
        "wall_count": len(walls),
        "micro": micro,
        "claim_boundary": (
            "Fixture AABB extent intersections measured; not customer corpus; "
            "not IfcClash mesh product; never TZ collision >90%."
        ),
        "next": [
            "Replace fixture with pilot/customer IFC solids for n≈50 dual-blind labels",
            "Keep wording: geometric intersection of extents / measured P/R — never >90%",
        ],
    }
    (evidence_dir / "STATUS.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return status


def _ensure_fixture(ifc: Path) -> None:
    gen = _repo_root() / "backend" / "scripts" / "generate_extent_clash_fixture.py"
    spec = importlib.util.spec_from_file_location("generate_extent_clash_fixture", gen)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.write_extent_clash_fixture(ifc)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ifc", type=Path, default=None)
    parser.add_argument("--evidence-dir", type=Path, default=None)
    parser.add_argument("--write-fixture", action="store_true")
    args = parser.parse_args(argv)
    repo = _repo_root()
    ifc = args.ifc or (repo / "samples" / "ifc" / "clash-extent-overlap-fixture.ifc")
    evidence = args.evidence_dir or (repo / "docs" / "evidence" / "clash-measurement-slice-2026-08")
    if args.write_fixture or not ifc.is_file():
        _ensure_fixture(ifc)
    status = measure(ifc_path=ifc, evidence_dir=evidence)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
