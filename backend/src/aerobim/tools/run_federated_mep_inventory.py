"""Federated MEP inventory on public IFC. Never claims MEP delivered.

Looks at in-repo HVAC fixture plus optional IFC-Bench checkouts
(duplex/mep, digital_hub, west_riverside). Counts distribution elements.
Does not run clash. Capability stays NOT_VERIFIED.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from aerobim.domain.ids_schema_gate import parse_ifc_file_schema, parse_ifc_view_definition
from aerobim.tools.benchmark_project_package import repo_root

CLAIM_LEVEL = "federated_mep_inventory"
CLAIM_BOUNDARY = (
    "Inventory of public federated / MEP IFC on disk. Entity counts only. "
    "mep_system_clash remains NOT_VERIFIED. Not RT-003 delivered. "
    "Not customer MEP. GPLv3 IFC-Bench models are not opened."
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
    (".local/ifc-bench-v2/projects/digital_hub/arc.ifc", "ifc_bench_digital_hub"),
    (".local/ifc-bench-v2/projects/west_riverside_hospital/arc.ifc", "ifc_bench_west_riverside"),
)


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
    except Exception as exc:  # noqa: BLE001 — inventory must not abort
        row["status"] = "ERROR"
        row["error"] = f"{type(exc).__name__}: {exc}"
    row["elapsed_ms"] = round((perf_counter() - started) * 1000.0, 3)
    return row


def build_payload(*, repo: Path) -> dict[str, Any]:
    rows = [_inventory(repo / rel, label=label, repo=repo) for rel, label in CANDIDATES]
    present = [row for row in rows if row["status"] == "RUN"]
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "artifact_type": "federated_mep_inventory",
        "claim_level": CLAIM_LEVEL,
        "claim_boundary": CLAIM_BOUNDARY,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "mep_system_clash": "NOT_VERIFIED",
        "closes_rt003": False,
        "present": len(present),
        "rows": rows,
    }
    encoded = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    body["content_sha256"] = _sha256_bytes(encoded)
    return body


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "<!-- claims-lint: allow-file reason=\"Federated MEP inventory; clash NOT_VERIFIED\" -->",
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
    parser.parse_args(argv)
    repo = repo_root()
    payload = build_payload(repo=repo)
    out = repo / "artifacts" / "federated-mep-inventory"
    out.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    (out / "federated-mep-inventory.json").write_text(text, encoding="utf-8")
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
