"""PNST 909 22-scenario IDS runtime on the gitignored Renga publisher pack.

Not product accuracy. Zero findings on the publisher reference IFC are expected
(the pack is designed to satisfy its own IDS). Missing IDS → ``NO_IDS_IN_PACK``,
never a silent pass. Absent pack → ``SKIPPED`` and does **not** overwrite the
measured docs snapshot. Checkpoint NO_GO. Does not close RT-001 / RT-002.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any, Protocol

from aerobim.core.security.path_jail import PathJailError, resolve_storage_path

CLAIM_BOUNDARY = (
    "Aggregated PNST 909 IDS coverage on Renga open pack after ToS cite GO "
    "(2026-08-05). AUTHOR_CLAIM coverage map — NOT product accuracy, NOT expert "
    "adjudication. Clean pack != customer precision. Checkpoint NO_GO."
)
ENV_PACK = "AEROBIM_PNST909_PACK"
DEFAULT_PACK_REL = Path(".local") / "renga-pnst909" / "pack"
DEFAULT_PAIRING_REL = Path("docs") / "evidence" / "pnst909-22-scenario-pairing.json"
OUT_OF_PACK_SCENARIOS = frozenset({3, 18, 21, 22})


class IdsRuntimeValidator(Protocol):
    def validate(self, ids_path: Path, ifc_path: Path) -> Sequence[Any]: ...


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def default_pack_root(root: Path | None = None) -> Path:
    env = (os.getenv(ENV_PACK) or "").strip()
    if env:
        return Path(env)
    return (root or repo_root()) / DEFAULT_PACK_REL


def default_pairing_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / DEFAULT_PAIRING_REL


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _repo_relative_or_redact(path: Path, *, repo: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except (OSError, ValueError):
        return "<redacted>"


def load_pairing(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("PNST 909 pairing must be a JSON object")
    rows = payload.get("scenarios")
    if not isinstance(rows, list) or len(rows) != 22:
        raise ValueError("PNST 909 pairing must list exactly 22 scenarios")
    scenarios: list[dict[str, Any]] = []
    seen: set[int] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("PNST 909 pairing row must be an object")
        number = int(row["scenario"])
        if number < 1 or number > 22 or number in seen:
            raise ValueError(f"invalid or duplicate PNST scenario number: {number}")
        seen.add(number)
        ids_path = row.get("ids_path")
        ifc_path = row.get("ifc_path")
        scenarios.append(
            {
                "scenario": number,
                "ids_path": None if ids_path in (None, "") else str(ids_path),
                "ifc_path": None if ifc_path in (None, "") else str(ifc_path),
            }
        )
    if seen != set(range(1, 23)):
        raise ValueError("PNST 909 pairing must cover scenarios 1..22")
    return scenarios


def _posix_rel(value: str | None) -> str | None:
    if value is None:
        return None
    return value.replace("\\", "/")


def _jail_rel(rel: str, *, pack_root: Path) -> Path:
    return resolve_storage_path(_posix_rel(rel) or "", base=pack_root)


def _stat_ifc_bytes(rel: str | None, *, pack_root: Path) -> int | None:
    if not rel:
        return None
    try:
        path = _jail_rel(rel, pack_root=pack_root)
    except PathJailError:
        return None
    if path.is_file():
        return path.stat().st_size
    return None


def count_pairing_ids_on_disk(pack_root: Path, pairing: Sequence[dict[str, Any]]) -> int:
    present = 0
    for spec in pairing:
        rel = spec.get("ids_path")
        if not rel:
            continue
        try:
            path = _jail_rel(str(rel), pack_root=pack_root)
        except PathJailError:
            continue
        if path.is_file():
            present += 1
    return present


def skipped_pack_payload(
    *,
    reason: str,
    pairing_path: str,
    status: str = "SKIPPED_PACK_ABSENT",
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "artifact_type": "aerobim_pnst909_22_scenario_runtime",
        "schema_version": "1.1.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "claim_boundary": CLAIM_BOUNDARY,
        "tos_cite": "GO",
        "tos_cite_date": "2026-08-05",
        "status": status,
        "reason": reason,
        "source_pack": DEFAULT_PACK_REL.as_posix(),
        "pairing_path": pairing_path,
        "cli": "python -m aerobim.tools.run_pnst909_22_scenario_runtime",
        "validator": None,
        "closes_rt001": False,
        "closes_rt002": False,
        "checkpoint": "NO_GO",
        "summary": {
            "scenarios_total": 22,
            "executed": 0,
            "coverage_class_counts": {},
            "runtime_status_counts": {status: 1},
            "share_executed": 0.0,
            "share_ids_available": 0.0,
        },
        "scenarios": [],
        "note": (
            "Pack missing or truncated to a header sample. Do not invent a fresh "
            "18/22 from this SKIPPED payload. Keep the last measured docs/evidence snapshot."
        ),
    }
    encoded = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    body["content_sha256"] = _sha256_bytes(encoded)
    return body


def default_validator() -> IdsRuntimeValidator:
    from aerobim.infrastructure.adapters.ifc_tester_ids_validator import IfcTesterIdsValidator

    return IfcTesterIdsValidator()


def run_scenarios(
    *,
    pack_root: Path,
    pairing: Sequence[dict[str, Any]],
    validator: IdsRuntimeValidator,
    repo: Path,
    pairing_path: str,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for spec in pairing:
        scenario = int(spec["scenario"])
        ids_rel = spec.get("ids_path")
        ifc_rel = spec.get("ifc_path")
        ifc_bytes = _stat_ifc_bytes(ifc_rel, pack_root=pack_root) if ifc_rel else None
        if not ids_rel:
            rows.append(
                {
                    "scenario": scenario,
                    "ids_path": None,
                    "ifc_path": _posix_rel(ifc_rel),
                    "ifc_bytes": ifc_bytes,
                    "coverage_class": "out_of_pack",
                    "runtime_status": "NO_IDS_IN_PACK",
                    "issue_count": None,
                    "wall_clock_s": None,
                    "error": None,
                    "notes": "No IDS in downloaded publisher pack (frozen pairing)",
                }
            )
            continue
        try:
            ids_path = _jail_rel(str(ids_rel), pack_root=pack_root)
            ifc_path = _jail_rel(str(ifc_rel), pack_root=pack_root) if ifc_rel else None
        except PathJailError as exc:
            rows.append(
                {
                    "scenario": scenario,
                    "ids_path": _posix_rel(str(ids_rel)),
                    "ifc_path": _posix_rel(ifc_rel),
                    "ifc_bytes": None,
                    "coverage_class": "path_rejected",
                    "runtime_status": "PATH_REJECTED",
                    "issue_count": None,
                    "wall_clock_s": None,
                    "error": str(exc),
                    "notes": "Relative IDS/IFC path escaped pack root",
                }
            )
            continue
        if not ids_path.is_file():
            rows.append(
                {
                    "scenario": scenario,
                    "ids_path": _posix_rel(str(ids_rel)),
                    "ifc_path": _posix_rel(ifc_rel),
                    "ifc_bytes": ifc_bytes,
                    "coverage_class": "out_of_pack",
                    "runtime_status": "NO_IDS_IN_PACK",
                    "issue_count": None,
                    "wall_clock_s": None,
                    "error": None,
                    "notes": "Paired IDS path is not a file on disk",
                }
            )
            continue
        if ifc_path is None or not ifc_path.is_file():
            rows.append(
                {
                    "scenario": scenario,
                    "ids_path": _posix_rel(str(ids_rel)),
                    "ifc_path": _posix_rel(ifc_rel),
                    "ifc_bytes": ifc_bytes,
                    "coverage_class": "missing_ifc",
                    "runtime_status": "MISSING_IFC",
                    "issue_count": None,
                    "wall_clock_s": None,
                    "error": None,
                    "notes": "Paired IFC path is not a file on disk",
                }
            )
            continue
        started = perf_counter()
        try:
            issues = list(validator.validate(ids_path, ifc_path))
            elapsed = round(perf_counter() - started, 3)
            issue_count = len(issues)
            clean = issue_count == 0
            rows.append(
                {
                    "scenario": scenario,
                    "ids_path": _posix_rel(str(ids_rel)),
                    "ifc_path": _posix_rel(ifc_rel),
                    "ifc_bytes": ifc_path.stat().st_size,
                    "coverage_class": "runtime_clean" if clean else "runtime_findings",
                    "runtime_status": "EXECUTED",
                    "issue_count": issue_count,
                    "wall_clock_s": elapsed,
                    "error": None,
                    "notes": (
                        "IDS validator executed; 0 findings on Renga reference IFC "
                        "(pack designed to satisfy IDS)"
                        if clean
                        else "IDS validator executed; findings are pack coverage, not precision"
                    ),
                }
            )
        except Exception as exc:
            rows.append(
                {
                    "scenario": scenario,
                    "ids_path": _posix_rel(str(ids_rel)),
                    "ifc_path": _posix_rel(ifc_rel),
                    "ifc_bytes": ifc_path.stat().st_size,
                    "coverage_class": "error",
                    "runtime_status": "ERROR",
                    "issue_count": None,
                    "wall_clock_s": round(perf_counter() - started, 3),
                    "error": f"{type(exc).__name__}: {exc}",
                    "notes": "Validator raised; not a silent pass",
                }
            )

    status_counts: dict[str, int] = {}
    class_counts: dict[str, int] = {}
    for row in rows:
        status = str(row["runtime_status"])
        status_counts[status] = status_counts.get(status, 0) + 1
        klass = str(row["coverage_class"])
        class_counts[klass] = class_counts.get(klass, 0) + 1
    executed = status_counts.get("EXECUTED", 0)
    ids_available = sum(1 for row in rows if row.get("ids_path"))
    total = len(rows)
    body: dict[str, Any] = {
        "artifact_type": "aerobim_pnst909_22_scenario_runtime",
        "schema_version": "1.1.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "claim_boundary": CLAIM_BOUNDARY,
        "tos_cite": "GO",
        "tos_cite_date": "2026-08-05",
        "status": "PARTIAL_RUN" if executed < total else "EXECUTED",
        "source_pack": _repo_relative_or_redact(pack_root, repo=repo),
        "pairing_path": pairing_path,
        "cli": "python -m aerobim.tools.run_pnst909_22_scenario_runtime",
        "validator": type(validator).__name__,
        "closes_rt001": False,
        "closes_rt002": False,
        "checkpoint": "NO_GO",
        "summary": {
            "scenarios_total": total,
            "executed": executed,
            "coverage_class_counts": class_counts,
            "runtime_status_counts": status_counts,
            "share_executed": round(executed / total, 3) if total else 0.0,
            "share_ids_available": round(ids_available / total, 3) if total else 0.0,
        },
        "scenarios": rows,
        "out_of_pack_scenarios": sorted(OUT_OF_PACK_SCENARIOS),
        "note": (
            "0 findings on the publisher reference IFC is expected. "
            "This is not customer precision and does not close RT-001/RT-002."
        ),
    }
    encoded = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    body["content_sha256"] = _sha256_bytes(encoded)
    return body


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    status_counts = summary.get("runtime_status_counts") or {}
    class_counts = summary.get("coverage_class_counts") or {}
    generated = str(payload.get("generated_at") or "")[:10]
    executed = summary.get("executed")
    total = summary.get("scenarios_total")
    no_ids = status_counts.get("NO_IDS_IN_PACK", 0)
    lines = [
        '<!-- claims-lint: allow-file reason="PNST 909 22-scenario IDS axis; not product accuracy; NO_GO" -->',
        "---",
        'title: "PNST 909 — 22-scenario second coverage axis"',
        f"date: {generated}",
        f"status: {payload.get('status')}",
        "claim_boundary: >-",
        f"  {CLAIM_BOUNDARY}",
        "---",
        "",
        "# Вторая ось покрытия: 22 сценария ПНСТ 909-2024",
        "",
        "Not product accuracy. Checkpoint **NO_GO**. ToS cite **GO** for aggregated metrics.",
        "",
        f"- status: **{payload.get('status')}**",
        f"- CLI: `{payload.get('cli')}`",
        f"- pairing: `{payload.get('pairing_path')}`",
        f"- pack: `{payload.get('source_pack')}`",
        f"- validator: `{payload.get('validator')}`",
        f"- executed: **{executed}/{total}** (n=22; NO_IDS_IN_PACK={no_ids})",
        f"- coverage_class_counts: `{class_counts}`",
        f"- runtime_status_counts: `{status_counts}`",
        f"- content_sha256: `{payload.get('content_sha256')}`",
        "",
        "Scenarios 3 / 18 / 21 / 22 stay `out_of_pack` until the publisher ships IDS.",
        "Zero findings on the reference IFC means the pack was built to satisfy IDS, "
        "not that AeroBIM has customer precision.",
        "",
        "```bash",
        "cd backend",
        "python -m aerobim.tools.run_pnst909_22_scenario_runtime --write-docs-evidence",
        "```",
        "",
    ]
    if str(payload.get("status") or "").startswith("SKIPPED"):
        lines.insert(-5, f"- reason: {payload.get('reason')}")
        lines.insert(-5, "")
        lines.insert(
            -5,
            "Do not invent a fresh 18/22 from SKIPPED. Keep the last measured snapshot.",
        )
        lines.insert(-5, "")
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
    parser.add_argument("--pack-root", type=Path, default=None)
    parser.add_argument("--pairing", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--write-docs-evidence", action="store_true")
    parser.add_argument(
        "--require-pack",
        action="store_true",
        help="Exit 2 when the gitignored publisher pack is absent.",
    )
    args = parser.parse_args(argv)

    root = repo_root()
    pairing_file = args.pairing or default_pairing_path(root)
    pairing_rel = _repo_relative_or_redact(pairing_file, repo=root)
    pack_root = (args.pack_root or default_pack_root(root)).resolve()
    artifacts = args.output or (root / "artifacts" / "pnst909" / "pnst909-22-scenario-runtime.json")
    evidence_json = root / "docs" / "evidence" / "pnst909-22-scenario-runtime-latest.json"
    evidence_md = root / "docs" / "evidence" / "PNST909_22_SCENARIO_COVERAGE_AXIS_2026_08.md"

    if not pairing_file.is_file():
        print(json.dumps({"error": f"pairing missing: {pairing_rel}"}))
        return 3

    pairing = load_pairing(pairing_file)
    ids_on_disk = count_pairing_ids_on_disk(pack_root, pairing) if pack_root.is_dir() else 0
    if not pack_root.is_dir() or ids_on_disk == 0:
        if pack_root.is_dir():
            status = "SKIPPED_PACK_INCOMPLETE"
            reason = (
                f"PNST 909 pack at {pack_root} has 0/{sum(1 for row in pairing if row.get('ids_path'))} "
                "paired IDS files (header-sample / truncated extract). "
                "Do not overwrite the 2026-08-05 18/22 snapshot with a fake 0/22."
            )
        else:
            status = "SKIPPED_PACK_ABSENT"
            reason = (
                f"PNST 909 pack missing at {pack_root}. "
                f"Set {ENV_PACK} or place the publisher extract under "
                f"{DEFAULT_PACK_REL.as_posix()}/ (gitignored)."
            )
        payload = skipped_pack_payload(
            reason=reason,
            pairing_path=pairing_rel,
            status=status,
        )
        write_outputs(
            payload,
            artifacts_json=artifacts,
            evidence_json=None,
            evidence_md=None,
        )
        print(
            json.dumps(
                {
                    "status": payload["status"],
                    "reason": payload["reason"],
                    "output": str(artifacts),
                    "docs_evidence_written": False,
                    "paired_ids_on_disk": ids_on_disk,
                },
                ensure_ascii=False,
            )
        )
        return 2 if args.require_pack else 0

    payload = run_scenarios(
        pack_root=pack_root,
        pairing=pairing,
        validator=default_validator(),
        repo=root,
        pairing_path=pairing_rel,
    )
    write_docs = bool(args.write_docs_evidence)
    write_outputs(
        payload,
        artifacts_json=artifacts,
        evidence_json=evidence_json if write_docs else None,
        evidence_md=evidence_md if write_docs else None,
    )
    summary = payload["summary"]
    print(
        json.dumps(
            {
                "status": payload["status"],
                "summary": summary,
                "output": str(artifacts),
                "docs_evidence_written": write_docs,
                "content_sha256": payload.get("content_sha256"),
                "claim_boundary": "not product accuracy",
                "checkpoint": "NO_GO",
            },
            ensure_ascii=False,
        )
    )
    statuses = summary.get("runtime_status_counts") or {}
    if statuses.get("ERROR") or statuses.get("PATH_REJECTED") or statuses.get("MISSING_IFC"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
