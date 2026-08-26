"""Federated MEP inventory on public IFC. Never claims MEP delivered.

Looks at in-repo HVAC fixture plus optional IFC-Bench checkouts
(duplex/dental/digital_hub/wbdg_office; west_riverside if present).
Counts distribution elements. Does not run clash. Capability stays NOT_VERIFIED.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from aerobim.domain.copyleft_lane import (
    GPLV3_IFC_BENCH_PROJECTS,
    local_samolet_demo_copyleft_inputs_permitted,
)
from aerobim.domain.ids_schema_gate import parse_ifc_file_schema, parse_ifc_view_definition
from aerobim.tools.benchmark_project_package import repo_root

CLAIM_LEVEL = "federated_mep_inventory"
CLAIM_BOUNDARY = (
    "Public federated / MEP IFC on disk. Entity counts plus AABB broadphase on "
    "the in-repo HVAC fixture (existing graph + AABB filter) and duplex "
    "architecture-vs-MEP product AABBs. "
    "AABB overlap is not geometric clash. mep_system_clash remains NOT_VERIFIED. "
    "Not RT-003 delivered. Not customer MEP. GPLv3 IFC-Bench models are not opened."
)
MEP_TYPES = (
    "IfcDistributionElement",
    "IfcFlowTerminal",
    "IfcFlowSegment",
    "IfcFlowFitting",
    "IfcFlowController",
    "IfcDistributionPort",
    "IfcSystem",
)

CANDIDATES = (
    ("samples/mep/hvac-sprinkler-systems.ifc", "eng_fixture"),
    (".local/ifc-bench-v2/projects/duplex/mep.ifc", "ifc_bench_duplex_mep"),
    (".local/ifc-bench-v2/projects/duplex/arc.ifc", "ifc_bench_duplex_arc"),
    (".local/ifc-bench-v2/projects/dental_clinic/mep.ifc", "ifc_bench_dental_mep"),
    (".local/ifc-bench-v2/projects/dental_clinic/str.ifc", "ifc_bench_dental_str"),
    (".local/ifc-bench-v2/projects/digital_hub/arc.ifc", "ifc_bench_digital_hub"),
    (".local/ifc-bench-v2/projects/digital_hub/heating.ifc", "ifc_bench_digital_hub_heating"),
    (".local/ifc-bench-v2/projects/digital_hub/plumbing.ifc", "ifc_bench_digital_hub_plumbing"),
    (
        ".local/ifc-bench-v2/projects/digital_hub/ventilation.ifc",
        "ifc_bench_digital_hub_ventilation",
    ),
    (".local/ifc-bench-v2/projects/wbdg_office/mep.ifc", "ifc_bench_wbdg_office_mep"),
    # West Riverside ships IFC2X3 + IFC4 twins; inventory IFC4 once (not both).
    (
        ".local/ifc-bench-v2/projects/west_riverside_hospital/arc_ifc4.ifc",
        "ifc_bench_west_riverside_arc_ifc4",
    ),
    (
        ".local/ifc-bench-v2/projects/west_riverside_hospital/mech_ifc4.ifc",
        "ifc_bench_west_riverside_mech_ifc4",
    ),
    (
        ".local/ifc-bench-v2/projects/west_riverside_hospital/plumb_ifc4.ifc",
        "ifc_bench_west_riverside_plumb_ifc4",
    ),
    (
        ".local/ifc-bench-v2/projects/west_riverside_hospital/elec_ifc4.ifc",
        "ifc_bench_west_riverside_elec_ifc4",
    ),
    (
        ".local/ifc-bench-v2/projects/west_riverside_hospital/fire_ifc4.ifc",
        "ifc_bench_west_riverside_fire_ifc4",
    ),
    (
        ".local/ifc-bench-v2/projects/west_riverside_hospital/sprinkle_ifc4.ifc",
        "ifc_bench_west_riverside_sprinkle_ifc4",
    ),
    (
        ".local/ifc-bench-v2/projects/west_riverside_hospital/str_ifc4.ifc",
        "ifc_bench_west_riverside_str_ifc4",
    ),
)


def _ci_environment() -> bool:
    return os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("CI") == "true"


def gplv3_local_candidates(repo: Path) -> tuple[tuple[str, str], ...]:
    """Discover gitignored GPLv3 IFC-Bench files. Empty when dirs are absent."""
    root = repo / ".local" / "ifc-bench-v2" / "projects"
    found: list[tuple[str, str]] = []
    for name in GPLV3_IFC_BENCH_PROJECTS:
        project = root / name
        if not project.is_dir():
            continue
        for path in sorted(project.rglob("*.ifc")):
            rel = path.relative_to(repo).as_posix()
            label = f"ifc_bench_gplv3_{name}_{path.stem}"
            found.append((rel, label))
    return tuple(found)


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _inventory(path: Path, *, label: str, repo: Path) -> dict[str, Any]:
    started = perf_counter()
    try:
        rel = path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        rel = str(path)
    if not path.is_file():
        return {
            "label": label,
            "path": rel,
            "status": "SKIPPED",
            "reason": "file not present",
            "elapsed_ms": round((perf_counter() - started) * 1000.0, 3),
        }
    header = path.read_bytes()[: 64 * 1024].decode("utf-8", errors="replace")
    row: dict[str, Any] = {
        "label": label,
        "path": rel,
        "status": "RUN",
        "bytes": path.stat().st_size,
        "schema": parse_ifc_file_schema(header),
        "view": parse_ifc_view_definition(header),
        "counts": {},
        "elapsed_ms": None,
        "error": None,
    }
    try:
        import ifcopenshell

        model = ifcopenshell.open(str(path))
        row["counts"] = {name: len(model.by_type(name)) for name in MEP_TYPES}
        row["ifc_product_count"] = len(model.by_type("IfcProduct"))
    except Exception as exc:
        row["status"] = "ERROR"
        row["error"] = f"{type(exc).__name__}: {exc}"
    row["elapsed_ms"] = round((perf_counter() - started) * 1000.0, 3)
    return row


def _hvac_graph_aabb(repo: Path) -> dict[str, Any]:
    started = perf_counter()
    scope_path = repo / "samples" / "mep" / "federated-scope-verified-fixture.json"
    dummy = repo / "samples" / "mep" / "hvac-sprinkler-systems.ifc"
    try:
        from aerobim.infrastructure.adapters.federated_ifc_mep_system_graph import (
            FederatedIfcMepSystemGraphProvider,
        )
        from aerobim.infrastructure.adapters.ifc_aabb_mep_pair_filter import IfcAabbMepPairFilter

        provider = FederatedIfcMepSystemGraphProvider.from_scope_path(scope_path, repo_root=repo)
        graph = provider.build(dummy)
        aabb = IfcAabbMepPairFilter().filter_pairs(graph)
        return {
            "status": "RUN",
            "geometry_verified": False,
            "nodes": len(graph.nodes),
            "edges": len(graph.edges),
            "synthetic": graph.synthetic,
            "aabb_status": aabb.status,
            "aabb_reason": aabb.reason,
            "aabb_boxes_built": aabb.boxes_built,
            "aabb_pairs_before": aabb.pairs_before,
            "aabb_pairs_after": aabb.pairs_after,
            "elapsed_ms": round((perf_counter() - started) * 1000.0, 3),
        }
    except Exception as exc:
        return {
            "status": "ERROR",
            "geometry_verified": False,
            "error": f"{type(exc).__name__}: {exc}",
            "elapsed_ms": round((perf_counter() - started) * 1000.0, 3),
        }


def _duplex_aabb_overlaps(repo: Path) -> dict[str, Any]:
    started = perf_counter()
    arc = repo / ".local" / "ifc-bench-v2" / "projects" / "duplex" / "arc.ifc"
    mep = repo / ".local" / "ifc-bench-v2" / "projects" / "duplex" / "mep.ifc"
    v1_arc = repo / ".local" / "ifc-bench" / "projects" / "duplex" / "arc.ifc"
    v1_mep = repo / ".local" / "ifc-bench" / "projects" / "duplex" / "mep.ifc"
    if not arc.is_file():
        arc, mep = v1_arc, v1_mep
    if not arc.is_file() or not mep.is_file():
        return {
            "status": "SKIPPED",
            "reason": "duplex arc/mep not present under .local/ifc-bench*",
            "geometry_verified": False,
            "elapsed_ms": round((perf_counter() - started) * 1000.0, 3),
        }
    try:
        from aerobim.domain.mep_aabb import aabb_overlap
        from aerobim.infrastructure.adapters.ifc_aabb_mep_pair_filter import (
            _element_boxes_from_model,
        )
        from aerobim.infrastructure.adapters.ifc_file_open import open_ifc_model

        arc_boxes = _element_boxes_from_model(
            open_ifc_model(arc),
            ifc_types=("IfcWall", "IfcSlab", "IfcDoor", "IfcWindow"),
        )
        mep_boxes = _element_boxes_from_model(
            open_ifc_model(mep),
            ifc_types=("IfcFlowTerminal", "IfcEnergyConversionDevice", "IfcFlowSegment"),
        )
        overlaps = 0
        for box_a in arc_boxes.values():
            for box_b in mep_boxes.values():
                if aabb_overlap(box_a, box_b):
                    overlaps += 1
        return {
            "status": "RUN",
            "geometry_verified": False,
            "arc_boxes": len(arc_boxes),
            "mep_boxes": len(mep_boxes),
            "aabb_overlap_pairs": overlaps,
            "arc_types": ["IfcWall", "IfcSlab", "IfcDoor", "IfcWindow"],
            "mep_types": ["IfcFlowTerminal", "IfcEnergyConversionDevice", "IfcFlowSegment"],
            "elapsed_ms": round((perf_counter() - started) * 1000.0, 3),
        }
    except Exception as exc:
        return {
            "status": "ERROR",
            "geometry_verified": False,
            "error": f"{type(exc).__name__}: {exc}",
            "elapsed_ms": round((perf_counter() - started) * 1000.0, 3),
        }


def build_payload(*, repo: Path, include_gplv3: bool = False) -> dict[str, Any]:
    candidates: tuple[tuple[str, str], ...] = CANDIDATES
    if include_gplv3:
        candidates = CANDIDATES + gplv3_local_candidates(repo)
    rows = [_inventory(repo / rel, label=label, repo=repo) for rel, label in candidates]
    present = [row for row in rows if row["status"] == "RUN"]
    geometry = {
        "hvac_fixture_graph_aabb": _hvac_graph_aabb(repo),
        "duplex_arc_mep_aabb": _duplex_aabb_overlaps(repo),
    }
    boundary = CLAIM_BOUNDARY
    if include_gplv3:
        boundary = (
            "Samolet-local copyleft lane. GPLv3 IFC-Bench files may be opened from "
            "gitignored .local/. AABB overlap is not geometric clash. "
            "mep_system_clash remains NOT_VERIFIED. Not RT-003 delivered. "
            "Not customer MEP. Not a public MIT distribution."
        )
    body: dict[str, Any] = {
        "schema_version": "1.1.0",
        "artifact_type": "federated_mep_inventory",
        "claim_level": CLAIM_LEVEL,
        "claim_boundary": boundary,
        "copyleft_lane": "samolet_demo_local" if include_gplv3 else "public_mit",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "mep_system_clash": "NOT_VERIFIED",
        "closes_rt003": False,
        "present": len(present),
        "rows": rows,
        "geometry": geometry,
    }
    encoded = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    body["content_sha256"] = _sha256_bytes(encoded)
    return body


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        '<!-- claims-lint: allow-file reason="Federated MEP inventory; clash NOT_VERIFIED" -->',
        "---",
        'title: "Federated MEP inventory"',
        f"date: {str(payload.get('generated_at') or '')[:10]}",
        f"claim_level: {payload.get('claim_level')}",
        "claim_boundary: >-",
        f"  {payload.get('claim_boundary')}",
        "---",
        "",
        "# Federated MEP inventory",
        "",
        f"- present/run: **{payload.get('present')}**",
        f"- mep_system_clash: **{payload.get('mep_system_clash')}**",
        f"- closes_rt003: **{payload.get('closes_rt003')}**",
        f"- content_sha256: `{payload.get('content_sha256')}`",
        f"- HVAC graph+AABB: `{json.dumps((payload.get('geometry') or {}).get('hvac_fixture_graph_aabb'), ensure_ascii=False)}`",
        f"- duplex AABB: `{json.dumps((payload.get('geometry') or {}).get('duplex_arc_mep_aabb'), ensure_ascii=False)}`",
        "",
        "| label | status | schema | IfcFlowTerminal | IfcSystem | products | ms |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload.get("rows") or []:
        counts = row.get("counts") or {}
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("label")),
                    str(row.get("status")),
                    str(row.get("schema") or ""),
                    str(counts.get("IfcFlowTerminal", "")),
                    str(counts.get("IfcSystem", "")),
                    str(row.get("ifc_product_count") or ""),
                    str(row.get("elapsed_ms") or ""),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Public models measured here are **not** MEP delivered and **not** a 0.5 s teaching-pack claim.",
            "",
            "```bash",
            "cd backend",
            "python -m aerobim.tools.run_federated_mep_inventory",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--samolet-demo-copyleft",
        action="store_true",
        help="Open gitignored GPLv3 IFC-Bench files if present. Never writes them to docs/evidence.",
    )
    args = parser.parse_args(argv)
    include_gpl = local_samolet_demo_copyleft_inputs_permitted(
        opted_in=bool(args.samolet_demo_copyleft),
        ci=_ci_environment(),
    )
    if args.samolet_demo_copyleft and not include_gpl:
        print(
            "refusing --samolet-demo-copyleft on CI (public MIT evidence stays copyleft-free)",
            file=sys.stderr,
        )
        return 2
    repo = repo_root()
    payload = build_payload(repo=repo, include_gplv3=include_gpl)
    out = repo / "artifacts" / "federated-mep-inventory"
    out.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    (out / "federated-mep-inventory.json").write_text(text, encoding="utf-8")
    if not include_gpl:
        (repo / "docs" / "evidence" / "federated-mep-inventory-2026-08.json").write_text(
            text, encoding="utf-8"
        )
        (repo / "docs" / "evidence" / "federated-mep-inventory-2026-08.md").write_text(
            render_markdown(payload), encoding="utf-8"
        )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["present"] >= 1 else 1


if __name__ == "__main__":
    raise SystemExit(main())
