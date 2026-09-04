"""Rehearse moscow_agr_2026 on city-published AGR example IFCs.

Class-1 AGR exchange + official city IDS (IfcTester) + honest-scope clash/MEP
SKIPPED. Not a PD pack. Does not close RT-001 / RT-002b / RT-003. Does not
run inject_defects until a clean PD pack exists.

Binaries live under gitignored ``.local/moscow-agr-examples/``.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aerobim.application.services.capability_policy import (
    apply_demo_scope_honesty,
    build_signoff_policy,
)
from aerobim.domain.agr_exchange_checks import (
    collect_agr_exchange_issues,
    collect_agr_tep_xml_issues,
    collect_agr_vedomost_xsd_issues,
)
from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.models import ReportCapabilities
from aerobim.domain.npa_legal_force import agr_exchange_legal_payload
from aerobim.infrastructure.adapters.ifc_file_open import open_ifc_model
from aerobim.infrastructure.adapters.xml_ids_document_auditor import XmlIdsDocumentAuditor
from aerobim.tools.benchmark_project_package import repo_root
from aerobim.tools.export_moexp_ids_coverage import (
    build_ids_engine_coverage,
    discover_ids,
    evaluate_ids_file,
)
from aerobim.tools.moscow_agr_city_examples import (
    CLAIM_BOUNDARY,
    CLAIM_LEVEL,
    ids_paths_for_entry,
    ifc_dir,
    load_manifest,
    missing_ifc_files,
    sha256_bytes,
    sha256_file,
)

EVIDENCE_JSON = Path("docs") / "evidence" / "moscow-agr-city-examples-2026-08.json"
EVIDENCE_MD = Path("docs") / "evidence" / "moscow-agr-city-examples-2026-08.md"
ARTIFACTS_JSON = Path("artifacts") / "moscow-agr-city-examples" / "run.json"


def skipped_payload(*, reason: str) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "artifact_type": "moscow_agr_city_examples",
        "claim_level": CLAIM_LEVEL,
        "claim_boundary": CLAIM_BOUNDARY,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "status": "SKIPPED",
        "reason": reason,
        "closes_rt001": False,
        "closes_rt002b": False,
        "closes_rt003": False,
        "checkpoint": CHECKPOINT,
        "pd_pack": False,
        "injector_ran": False,
        "legal_qualification": agr_exchange_legal_payload(),
    }
    encoded = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    body["content_sha256"] = sha256_bytes(encoded)
    return body


skipped_payload = skipped_payload


def _read_ifc(path: Path) -> tuple[str, str, int]:
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    return text[: 64 * 1024], text, len(raw)


def _issue_ids(issues: tuple[Any, ...]) -> list[str]:
    return [str(issue.rule_id) for issue in issues]


def evaluate_exchange(
    ifc_path: Path,
    *,
    declared_name: str,
    tep: Path,
    tep_root: str,
) -> dict[str, Any]:
    header, body, size = _read_ifc(ifc_path)
    ifc_issues = collect_agr_exchange_issues(
        filename=declared_name,
        header_text=header,
        body_text=body,
        size_bytes=size,
    )
    tep_issues = collect_agr_tep_xml_issues(xml_path=tep, expected_root=tep_root)
    issues = ifc_issues + tep_issues
    return {
        "declared_filename": declared_name,
        "bytes": size,
        "sha256": sha256_file(ifc_path),
        "ifc_rule_ids": _issue_ids(ifc_issues),
        "ifc_shape_clean": not ifc_issues,
        "tep_reused_official_example": True,
        "tep_rule_ids": _issue_ids(tep_issues),
        "rule_ids": _issue_ids(issues),
        "exchange_clean": not issues,
    }


def evaluate_ids(
    *,
    pack_dir: Path,
    ifc_path: Path,
    ids_paths: list[Path] | None = None,
) -> dict[str, Any]:
    auditor = XmlIdsDocumentAuditor()
    model = open_ifc_model(ifc_path)
    selected = [path for path in (ids_paths or discover_ids(pack_dir)) if path.is_file()]
    files = [
        evaluate_ids_file(path, ifc_path=ifc_path, auditor=auditor, ifc_model=model)
        for path in selected
    ]
    return build_ids_engine_coverage(
        pack_dir=pack_dir,
        ifc_path=ifc_path,
        artifact_type="moscow_agr_city_example_ids",
        claim_boundary=CLAIM_BOUNDARY,
        source_page="https://stroimprosto.mos.ru/knowledge/article/cim-agr/",
        extra_fields={
            "closes_rt001": False,
            "closes_rt002b": False,
            "closes_rt003": False,
            "fixture_ifc": {
                "path": ifc_path.as_posix(),
                "sha256": sha256_file(ifc_path),
                "bytes": ifc_path.stat().st_size,
                "note": "City AGR example IFC. Fail ≠ product accuracy. Not a PD pack.",
            },
        },
        files=files,
    )


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    return "\n".join(
        [
            '<!-- claims-lint: allow-file reason="City AGR example rehearsal; not PD pack; RT stay OPEN" -->',
            "---",
            'title: "Moscow AGR city examples — local rehearsal"',
            f"date: {str(payload.get('generated_at') or '')[:10]}",
            f"claim_level: {payload.get('claim_level')}",
            "claim_boundary: >-",
            f"  {payload.get('claim_boundary')}",
            "closes_rt001: false",
            "closes_rt002b: false",
            "closes_rt003: false",
            f"checkpoint: {CHECKPOINT}",
            "---",
            "",
            "# Moscow AGR city examples",
            "",
            "Official IFCs from the city article, plus already-vendored IDS/TEP/Vedomost. ",
            "**Not** a PD pack. **Not** Samolet. Clash/MEP stay SKIPPED under ",
            "`moscow_agr_2026`. Injector is not run. TEP sidecar is the official ",
            "published example reused for every IFC (not a per-model TEP). IDS ",
            "files are role-matched (ПС→ПС, БиО→БиО, АР→Общие+МССК).",
            "",
            f"- status: **{payload.get('status')}**",
            f"- reason: {payload.get('reason') or 'n/a'}",
            f"- IFC evaluated: **{summary.get('ifc_count', 0)}**",
            f"- exchange-clean IFC: **{summary.get('exchange_clean_count', 0)}**",
            f"- injector_ran: `{payload.get('injector_ran')}`",
            f"- content_sha256: `{payload.get('content_sha256')}`",
            "",
            "```bash",
            "cd backend",
            "python -m aerobim.tools.fetch_moscow_agr_city_examples",
            "python -m aerobim.tools.run_moscow_agr_city_examples",
            "```",
            "",
        ]
    )


def _write_outputs(root: Path, payload: dict[str, Any]) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    artifacts = root / ARTIFACTS_JSON
    artifacts.parent.mkdir(parents=True, exist_ok=True)
    artifacts.write_text(text, encoding="utf-8")
    (root / EVIDENCE_JSON).write_text(text, encoding="utf-8")
    (root / EVIDENCE_MD).write_text(render_markdown(payload), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-ids", action="store_true")
    parser.add_argument("--ids-all", action="store_true")
    args = parser.parse_args(argv)
    root = repo_root()
    missing = missing_ifc_files(root)
    if missing:
        payload = skipped_payload(
            reason=(
                "City IFCs not on disk: "
                + ", ".join(missing)
                + ". Fetch with python -m aerobim.tools.fetch_moscow_agr_city_examples"
            )
        )
        _write_outputs(root, payload)
        print(json.dumps({"status": "SKIPPED", "reason": payload["reason"]}))
        return 0

    manifest = load_manifest(root)
    tep = root / str(manifest["tep_sidecar"])
    tep_root_name = str(manifest["tep_expected_root"])
    ved_xml = root / str(manifest["vedomost_xml"])
    ved_xsd = root / str(manifest["vedomost_xsd"])
    ids_pack = root / str(manifest["ids_pack"])
    dest = ifc_dir(root)
    policy = build_signoff_policy(profile=str(manifest.get("signoff_profile") or "moscow_agr_2026"))
    honesty = apply_demo_scope_honesty(ReportCapabilities(), profile=policy.profile)
    ifc_rows: list[dict[str, Any]] = []
    ids_runs: list[dict[str, Any]] = []
    for entry in manifest.get("files") or []:
        if not isinstance(entry, dict):
            continue
        name = str(entry["local_name"])
        path = dest / name
        row = evaluate_exchange(
            path,
            declared_name=name,
            tep=tep,
            tep_root=tep_root_name,
        )
        row["id"] = entry.get("id")
        row["role"] = entry.get("role")
        row["filename_fields"] = entry.get("filename_fields")
        ifc_rows.append(row)
        run_ids = bool(args.ids_all) or (bool(entry.get("ids_default")) and not args.skip_ids)
        if run_ids:
            matched = ids_paths_for_entry(ids_pack, entry)
            ids_runs.append(
                {
                    "id": entry.get("id"),
                    "ifc": name,
                    "ids_names": [path.name for path in matched],
                    "coverage": evaluate_ids(
                        pack_dir=ids_pack,
                        ifc_path=path,
                        ids_paths=matched,
                    ),
                }
            )

    ved_issues = collect_agr_vedomost_xsd_issues(xml_path=ved_xml, xsd_path=ved_xsd)
    exchange_clean = [row for row in ifc_rows if row.get("exchange_clean")]
    payload = {
        "schema_version": "1.0.0",
        "artifact_type": "moscow_agr_city_examples",
        "claim_level": CLAIM_LEVEL,
        "claim_boundary": CLAIM_BOUNDARY,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "status": "RUN",
        "closes_rt001": False,
        "closes_rt002b": False,
        "closes_rt003": False,
        "checkpoint": CHECKPOINT,
        "pd_pack": False,
        "missing_pd_parts": [
            "sheets",
            "two_revisions",
            "tz",
            "calculations",
            "expertise_remarks",
            "dual_raters",
        ],
        "signoff_profile": policy.profile,
        "signoff_policy": {
            "require_clash": policy.require_clash,
            "clash_affects_pass": policy.clash_affects_pass,
            "require_mep_system_clash": policy.require_mep_system_clash,
        },
        "clash_mep": "SKIPPED",
        "honesty": {
            "clash": {
                "state": honesty.clash.status.value,
                "reason": honesty.clash.reason,
            },
            "mep_system_clash": {
                "state": honesty.mep_system_clash.status.value,
                "reason": honesty.mep_system_clash.reason,
            },
        },
        "tep_reused_official_example": True,
        "injector_ran": False,
        "injector_blocked_reason": (
            "City examples are CIM+TEP rehearsal, not a clean PD pack. "
            "inject_defects stays blocked."
        ),
        "legal_qualification": agr_exchange_legal_payload(),
        "vedomost_xsd_rule_ids": _issue_ids(ved_issues),
        "ifc": ifc_rows,
        "ids": [
            {
                "id": item.get("id"),
                "ifc": item.get("ifc"),
                "ids_names": item.get("ids_names"),
                "summary": (item.get("coverage") or {}).get("summary"),
            }
            for item in ids_runs
        ],
        "summary": {
            "ifc_count": len(ifc_rows),
            "exchange_clean_count": len(exchange_clean),
            "ids_runs": len(ids_runs),
        },
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    payload["content_sha256"] = sha256_bytes(encoded)
    _write_outputs(root, payload)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "summary": payload["summary"],
                "closes_rt001": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
