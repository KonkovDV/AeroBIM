"""Product-path demo: IFC Acceptance Gate. Fail-loud. fixture_only. No new ports.

Primary KT#2 sell: IFC + IDS/rule pack → evidence-backed findings → HTML/JSON/BCF.
PDF overlay is a P1 modality (`run_demo_vertical_slice`), not this command.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from aerobim.domain.ifc_acceptance_gate import (
    AcceptanceGateError,
    project_ifc_acceptance_gate,
    require_fixture_gate,
)
from aerobim.tools.run_vertical_slice import _REPO, run_vertical_slice

_DEFAULT_MANIFEST = _REPO / "samples" / "demo" / "vertical-slice-2026-08-11" / "manifest.json"
_DEFAULT_OUTPUT = _REPO / "artifacts" / "ifc-acceptance-gate-demo"


def _require_file(path: Path, what: str) -> None:
    if not path.is_file():
        raise AcceptanceGateError(f"{what} missing: {path}")


def run_demo_ifc_acceptance_gate(
    *,
    manifest: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    pack = (manifest or _DEFAULT_MANIFEST).expanduser().resolve()
    out = (output_dir or _DEFAULT_OUTPUT).expanduser().resolve()
    _require_file(pack, "manifest")
    summary = run_vertical_slice(pack, out, cv_sidecar=False)
    raw_paths = summary.get("_paths")
    paths: dict[str, Any] = raw_paths if isinstance(raw_paths, dict) else {}
    report_json = Path(str(paths.get("report_json") or out / "report.json"))
    _require_file(report_json, "report.json")
    _require_file(Path(str(paths.get("report_html") or out / "report.html")), "report.html")
    _require_file(Path(str(paths.get("bcf_zip") or out / "findings.bcfzip")), "BCF ZIP")
    _require_file(
        Path(str(paths.get("run_manifest") or out / "run-manifest.json")),
        "run-manifest.json",
    )
    payload = json.loads(report_json.read_text(encoding="utf-8"))
    run_manifest = summary.get("run_manifest") or {}
    input_hashes = summary.get("input_artifact_hash") or {}
    ids_hash = next(
        (
            str(entry.get("sha256"))
            for entry in (summary.get("inputs") or [])
            if isinstance(entry, dict) and entry.get("kind") == "ids"
        ),
        None,
    )
    gate = project_ifc_acceptance_gate(
        payload,
        engine_version=str(summary.get("git_sha") or "") or None,
        rule_pack_hash=ids_hash,
        input_hash=next(iter(input_hashes.values()), None) if input_hashes else None,
        created_at=str(summary.get("generated_at") or payload.get("created_at") or ""),
        reproducibility_hash=run_manifest.get("reproducibility_hash")
        if isinstance(run_manifest, dict)
        else None,
    )
    require_fixture_gate(gate)
    gate_path = out / "acceptance-gate.json"
    gate_path.write_text(
        json.dumps(gate, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    gate["_paths"] = {**paths, "acceptance_gate": str(gate_path)}
    return gate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        result = run_demo_ifc_acceptance_gate(manifest=args.manifest, output_dir=args.output)
    except (AcceptanceGateError, FileNotFoundError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    public = {k: v for k, v in result.items() if k != "_paths"}
    print(json.dumps(public, ensure_ascii=False, indent=2, default=str))
    print(
        "Checkpoint GO (regulatory_measurement_mvp; customer_go false). Fixture Acceptance Gate, not customer accuracy. "
        "Open artifacts/ifc-acceptance-gate-demo/report.html",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
