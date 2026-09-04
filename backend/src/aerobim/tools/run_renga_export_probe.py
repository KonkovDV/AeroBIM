"""Probe a Renga IFC export: originating system + MOEXP IFC4 fail-closed.

Does not replace the vertical-slice demo IFC (IfcOpenShell fixture).
Does not vendor publisher binaries. Samolet Renga export remains intake.

Needed for demo 20.08: show a real Renga FILE_SCHEMA / FILE_NAME when a local
publisher sample exists, and SKIPPED when it does not.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.ids_schema_gate import (
    RULE_IFC_VERSION,
    collect_schema_mismatches,
    parse_ids_specification_versions,
    parse_ifc_file_name,
    parse_ifc_file_schema,
    parse_ifc_view_definition,
)
from aerobim.tools.benchmark_project_package import repo_root

CLAIM_LEVEL = "renga_export_probe"
CLAIM_BOUNDARY = (
    "Header-level probe of one IFC: FILE_SCHEMA, FILE_NAME originating_system, "
    "and official MOEXP ifcVersion=IFC4 fail-closed. Publisher PNST 909 sample "
    "is not a Samolet export, not product accuracy, not Exp A 18/22 rerun. "
    "Vertical-slice demo IFC stays IfcOpenShell. This Renga 8.7 pack sample is "
    "FILE_SCHEMA IFC4 (not IFC4X3). IFC4X3 fail-closed remains on the "
    "IfcOpenShell fixture. Checkpoint GO (regulatory_measurement_mvp; customer_go false)."
)
PACK_HEADER_SAMPLE = {
    "date": "2026-08-14",
    "source_zip": "Yandex public /Модель/IFC.zip (rengabim.com/shablons PNST 909)",
    "members_sampled": 18,
    "selection": "15 smallest + 3 files ~5MB",
    "file_schema_counts": {"IFC4": 18},
    "originating_system": "Renga Professional 8.7.20879.0",
    "preprocessor_version": "IfcPlusPlus",
    "not_a_full_census": True,
    "not_proof_renga_never_emits_ifc4x3": True,
}
HEADER_BYTES = 256 * 1024
DEFAULT_PACK_REL = Path(".local") / "renga-pnst909"
DEFAULT_IDS_REL = (
    Path("samples")
    / "ids"
    / "moexp"
    / "pack"
    / "oks"
    / ("IDS_v1.0_Требования_МОГЭ_к_ЦИМ_АР_v3.2.ids")
)
ENV_IFC = "AEROBIM_RENGA_IFC"
_IFCAPPLICATION_RE = re.compile(
    r"IFCAPPLICATION\s*\(\s*[^,]+,\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'",
    re.IGNORECASE,
)


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def default_ids_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / DEFAULT_IDS_REL


def default_pack_root(root: Path | None = None) -> Path:
    return (root or repo_root()) / DEFAULT_PACK_REL


def discover_local_renga_ifc(pack_root: Path) -> Path | None:
    if not pack_root.is_dir():
        return None
    files = [path for path in pack_root.rglob("*.ifc") if path.is_file()]
    if not files:
        return None
    return min(files, key=lambda path: (path.stat().st_size, str(path).lower()))


def resolve_ifc_path(
    explicit: Path | None,
    *,
    repo: Path,
    env: Mapping[str, str] | None = None,
) -> Path | None:
    if explicit is not None:
        return explicit
    env_raw = (env if env is not None else os.environ).get(ENV_IFC)
    if env_raw:
        return Path(env_raw)
    return discover_local_renga_ifc(default_pack_root(repo))


def parse_ifc_applications(header_text: str) -> tuple[dict[str, str], ...]:
    rows: list[dict[str, str]] = []
    for match in _IFCAPPLICATION_RE.finditer(header_text):
        rows.append(
            {
                "version": match.group(1),
                "application_full_name": match.group(2),
                "application_identifier": match.group(3),
            }
        )
    return tuple(rows)


def classify_originating_system(
    *,
    preprocessor_version: str,
    originating_system: str,
    applications: tuple[dict[str, str], ...],
) -> str:
    parts = [preprocessor_version, originating_system]
    for row in applications:
        parts.extend(row.values())
    blob = " ".join(parts).lower()
    if "renga" in blob:
        return "renga"
    if "ifcopenshell" in blob:
        return "ifcopenshell"
    if "revit" in blob:
        return "revit"
    if blob.strip():
        return "other"
    return "unknown"


def _rel_or_name(path: Path, repo: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(repo.resolve()).as_posix()
    except ValueError:
        return path.name


def is_publisher_pnst_path(path: Path, repo: Path) -> bool:
    pack = default_pack_root(repo).resolve()
    try:
        path.resolve().relative_to(pack)
        return True
    except ValueError:
        return False


def skipped_payload(*, reason: str) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "artifact_type": "renga_export_probe",
        "claim_level": CLAIM_LEVEL,
        "claim_boundary": CLAIM_BOUNDARY,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "status": "SKIPPED",
        "reason": reason,
        "is_renga_export": False,
        "publisher_pnst909_sample": False,
        "samolet_export": False,
        "closes_c4_samolet_intake": False,
        "vertical_slice_ifc_replaced": False,
        "checkpoint": CHECKPOINT,
    }
    encoded = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    body["content_sha256"] = _sha256_bytes(encoded)
    return body


def probe_ifc(ifc_path: Path, ids_path: Path, *, repo: Path) -> dict[str, Any]:
    started = perf_counter()
    size = ifc_path.stat().st_size
    with ifc_path.open("rb") as handle:
        header = handle.read(HEADER_BYTES).decode("utf-8", errors="replace")
    schema = parse_ifc_file_schema(header)
    view = parse_ifc_view_definition(header)
    file_name = parse_ifc_file_name(header)
    applications = parse_ifc_applications(header)
    preprocessor = file_name.preprocessor_version if file_name else ""
    originating = file_name.originating_system if file_name else ""
    family = classify_originating_system(
        preprocessor_version=preprocessor,
        originating_system=originating,
        applications=applications,
    )
    ids_xml = ids_path.read_text(encoding="utf-8", errors="replace")
    specs = parse_ids_specification_versions(ids_xml)
    mismatches = collect_schema_mismatches(model_schema=schema, specs=specs)
    elapsed_ms = round((perf_counter() - started) * 1000.0, 3)
    publisher = is_publisher_pnst_path(ifc_path, repo)
    is_renga = family == "renga"
    result: dict[str, Any] = {
        "status": "MEASURED",
        "ifc_path": _rel_or_name(ifc_path, repo),
        "ifc_name": ifc_path.name,
        "ifc_bytes": size,
        "ifc_sha256": _sha256_file(ifc_path),
        "ids_path": _rel_or_name(ids_path, repo),
        "ids_sha256": _sha256_file(ids_path),
        "model_schema": schema,
        "view_definition": view,
        "preprocessor_version": preprocessor or None,
        "originating_system": originating or None,
        "authorization": (file_name.authorization if file_name else None) or None,
        "applications": list(applications),
        "originating_family": family,
        "is_renga_export": is_renga,
        "publisher_pnst909_sample": publisher,
        "samolet_export": False,
        "closes_c4_samolet_intake": False,
        "vertical_slice_ifc_replaced": False,
        "spec_count": len(specs),
        "schema_mismatch_count": len(mismatches),
        "schema_fail_closed": len(mismatches) > 0,
        "fail_closed_rule_id": RULE_IFC_VERSION if mismatches else None,
        "mismatch_spec_names": [item.spec_name for item in mismatches[:5]],
        "elapsed_ms": elapsed_ms,
        "checkpoint": CHECKPOINT,
    }
    if publisher:
        result["pack_header_sample"] = dict(PACK_HEADER_SAMPLE)
    return result


def build_payload(
    *,
    ifc_path: Path | None,
    ids_path: Path,
    repo: Path,
    missing_reason: str | None = None,
) -> dict[str, Any]:
    if ifc_path is None or not ifc_path.is_file():
        reason = missing_reason or (
            f"Renga IFC missing. Set {ENV_IFC} or place a publisher sample under "
            f"{DEFAULT_PACK_REL.as_posix()}/ (gitignored). "
            "Do not relabel samples/ifc/walls-multi-entity.ifc as Renga."
        )
        return skipped_payload(reason=reason)
    if not ids_path.is_file():
        return skipped_payload(reason=f"MOEXP IDS missing: {ids_path}")
    probe = probe_ifc(ifc_path, ids_path, repo=repo)
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "artifact_type": "renga_export_probe",
        "claim_level": CLAIM_LEVEL,
        "claim_boundary": CLAIM_BOUNDARY,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        **probe,
    }
    encoded = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    body["content_sha256"] = _sha256_bytes(encoded)
    return body


def render_markdown(payload: dict[str, Any]) -> str:
    status = str(payload.get("status") or "")
    lines = [
        '<!-- claims-lint: allow-file reason="Renga publisher IFC probe; not Samolet; NO_GO" -->',
        "---",
        'title: "Renga IFC export probe"',
        f"date: {str(payload.get('generated_at') or '')[:10]}",
        f"claim_level: {payload.get('claim_level')}",
        "claim_boundary: >-",
        f"  {payload.get('claim_boundary')}",
        "---",
        "",
        "# Renga IFC export probe",
        "",
        "Vertical-slice demo IFC is **not** replaced. Publisher PNST 909 sample "
        "is **not** a Samolet export. Checkpoint **GO**; customer_go false.",
        "",
        f"- status: **{status}**",
    ]
    if status == "SKIPPED":
        lines.extend(
            [
                f"- reason: {payload.get('reason')}",
                f"- content_sha256: `{payload.get('content_sha256')}`",
                "",
                "```bash",
                "cd backend",
                "python -m aerobim.tools.run_renga_export_probe --write-evidence",
                "```",
                "",
            ]
        )
        return "\n".join(lines)
    lines.extend(
        [
            f"- ifc: `{payload.get('ifc_path')}` ({payload.get('ifc_bytes')} bytes)",
            f"- ifc_sha256: `{payload.get('ifc_sha256')}`",
            f"- originating_system: `{payload.get('originating_system')}`",
            f"- preprocessor_version: `{payload.get('preprocessor_version')}`",
            f"- view_definition: `{payload.get('view_definition')}`",
            f"- originating_family: **{payload.get('originating_family')}**",
            f"- is_renga_export: **{payload.get('is_renga_export')}**",
            f"- publisher_pnst909_sample: **{payload.get('publisher_pnst909_sample')}**",
            f"- samolet_export: **{payload.get('samolet_export')}**",
            f"- FILE_SCHEMA: `{payload.get('model_schema')}`",
            f"- MOEXP IDS: `{payload.get('ids_path')}`",
            f"- schema_mismatch_count: **{payload.get('schema_mismatch_count')}** / "
            f"{payload.get('spec_count')} specs",
            f"- schema_fail_closed: **{payload.get('schema_fail_closed')}** "
            f"(`{payload.get('fail_closed_rule_id')}`)",
            f"- elapsed_ms: {payload.get('elapsed_ms')}",
            f"- content_sha256: `{payload.get('content_sha256')}`",
            "",
        ]
    )
    sample = payload.get("pack_header_sample") or {}
    if sample:
        counts = sample.get("file_schema_counts") or {}
        lines.extend(
            [
                "## Pack header sample (this machine)",
                "",
                f"- members_sampled: {sample.get('members_sampled')} ({sample.get('selection')})",
                f"- FILE_SCHEMA counts: `{counts}`",
                f"- originating_system: `{sample.get('originating_system')}`",
                "",
                "Not a 198-file census. Not proof that Renga never emits IFC4X3.",
                "",
            ]
        )
    lines.extend(
        [
            "Not product accuracy. Not Exp A 18/22. Not customer precision.",
            "",
            "```bash",
            "cd backend",
            "python -m aerobim.tools.run_renga_export_probe --write-evidence",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(
    payload: dict[str, Any],
    *,
    artifacts_json: Path,
    evidence_json: Path | None,
    evidence_md: Path | None,
) -> None:
    artifacts_json.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    artifacts_json.write_text(text, encoding="utf-8")
    if evidence_json is not None:
        evidence_json.parent.mkdir(parents=True, exist_ok=True)
        evidence_json.write_text(text, encoding="utf-8")
    if evidence_md is not None:
        evidence_md.parent.mkdir(parents=True, exist_ok=True)
        evidence_md.write_text(render_markdown(payload), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ifc", type=Path, default=None)
    parser.add_argument("--ids", type=Path, default=None)
    parser.add_argument("--write-evidence", action="store_true")
    parser.add_argument(
        "--require-renga",
        action="store_true",
        help="Exit 2 if the IFC originating system is not Renga.",
    )
    args = parser.parse_args(argv)
    root = repo_root()
    ids_path = args.ids or default_ids_path(root)
    ifc_path = resolve_ifc_path(args.ifc, repo=root)
    payload = build_payload(ifc_path=ifc_path, ids_path=ids_path, repo=root)
    artifacts = root / "artifacts" / "renga-export-probe" / "probe.json"
    evidence_json = root / "docs" / "evidence" / "renga-export-probe-2026-08.json"
    evidence_md = root / "docs" / "evidence" / "renga-export-probe-2026-08.md"
    write_outputs(
        payload,
        artifacts_json=artifacts,
        evidence_json=evidence_json if args.write_evidence else None,
        evidence_md=evidence_md if args.write_evidence else None,
    )
    summary = {
        "status": payload.get("status"),
        "ifc_path": payload.get("ifc_path") or payload.get("reason"),
        "originating_family": payload.get("originating_family"),
        "is_renga_export": payload.get("is_renga_export"),
        "model_schema": payload.get("model_schema"),
        "schema_fail_closed": payload.get("schema_fail_closed"),
        "schema_mismatch_count": payload.get("schema_mismatch_count"),
        "samolet_export": payload.get("samolet_export"),
        "checkpoint": payload.get("checkpoint"),
        "content_sha256": payload.get("content_sha256"),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if payload.get("status") == "SKIPPED":
        return 2 if args.require_renga else 0
    if args.require_renga and not payload.get("is_renga_export"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
