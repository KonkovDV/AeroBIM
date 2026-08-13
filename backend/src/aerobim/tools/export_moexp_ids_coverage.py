"""Coverage of official MosoblGosExpertiza IDS against IfcTester.

Numbers come from the measured run only. Engine coverage ≠ CIM compliance
and ≠ customer accuracy. Needed for tracker 14.08.2026 (brief part 2.1).

Source: https://www.moexp.ru/services/tekhnologii-informatsionnogo-modelirovaniya/
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from aerobim.domain.models import ValidationIssue
from aerobim.infrastructure.adapters.ifc_file_open import open_ifc_model
from aerobim.infrastructure.adapters.xml_ids_document_auditor import XmlIdsDocumentAuditor
from aerobim.tools.benchmark_project_package import _machine_fingerprint, repo_root

CLAIM_LEVEL = "official_ids_engine_coverage"
SOURCE_PAGE = "https://www.moexp.ru/services/tekhnologii-informatsionnogo-modelirovaniya/"
CLAIM_BOUNDARY = (
    "Official GAU MO MosoblGosExpertiza IDS executed by IfcTester. "
    "Fixture IFC is not a MOEXP-compliant CIM. Pass/fail on the fixture is "
    "not product accuracy, not Samolet acceptance, and does not replace a "
    "Samolet-signed acceptance profile. ICMM 3.3 has no published IDS."
)

STATUS_PASS = "executable_pass_on_fixture"
STATUS_FAIL = "executable_fail_on_fixture"
STATUS_UNSUPPORTED = "unsupported"
STATUS_LOAD_ERROR = "load_error"
KIND_ATTRIBUTES = "attributes"
KIND_CLASSIFICATION = "classification"
KIND_OTHER = "other"


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def default_pack_dir(root: Path | None = None) -> Path:
    return (root or repo_root()) / "samples" / "ids" / "moexp" / "pack"


def default_fixture_ifc(root: Path | None = None) -> Path:
    return (root or repo_root()) / "samples" / "ifc" / "wall-pset-qto-pass.ifc"


def discover_ids(pack_dir: Path) -> list[Path]:
    return sorted(path for path in pack_dir.rglob("*.ids") if path.is_file())


def classify_specification(
    *,
    unsupported: bool,
    load_error: str | None,
    spec_passed: bool | None,
) -> str:
    if unsupported:
        return STATUS_UNSUPPORTED
    if load_error:
        return STATUS_LOAD_ERROR
    if spec_passed is True:
        return STATUS_PASS
    return STATUS_FAIL


def classify_ids_kind(file_name: str) -> str:
    """Split official MOEXP IDS into attributes vs classification packs.

    Filenames on moexp.ru: ``Требования_…`` (attribute requirements) vs
    ``Проверка_КСИ_…`` (classification / KSI). Grouping is from the published
    name, not a new measurement.
    """

    name = file_name
    if "Проверка_КСИ" in name:
        return KIND_CLASSIFICATION
    if "Требования" in name:
        return KIND_ATTRIBUTES
    return KIND_OTHER


def _issue_digest(issues: list[ValidationIssue]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for issue in issues:
        rows.append(
            {
                "rule_id": issue.rule_id,
                "severity": issue.severity.value,
                "message": issue.message[:300],
            }
        )
    return rows


def evaluate_ids_file(
    ids_path: Path,
    *,
    ifc_path: Path,
    auditor: XmlIdsDocumentAuditor,
    ifc_model: Any | None = None,
) -> dict[str, Any]:
    domain = ids_path.parent.name
    started = perf_counter()
    audit_issues = auditor.audit(ids_path)
    unsupported_facets = [
        issue
        for issue in audit_issues
        if issue.rule_id == "AEROBIM-IDS-UNSUPPORTED-FACET"
    ]
    load_error: str | None = None
    spec_rows: list[dict[str, Any]] = []
    try:
        from ifctester import ids, reporter
    except ModuleNotFoundError as exc:
        load_error = f"ifctester missing: {exc}"
        return {
            "domain": domain,
            "path": str(ids_path.as_posix()),
            "file_name": ids_path.name,
            "kind": classify_ids_kind(ids_path.name),
            "sha256": _sha256_file(ids_path),
            "bytes": ids_path.stat().st_size,
            "load_error": load_error,
            "audit_issue_count": len(audit_issues),
            "unsupported_facet_count": len(unsupported_facets),
            "audit_issues": _issue_digest(audit_issues + unsupported_facets),
            "specifications": [],
            "elapsed_ms": round((perf_counter() - started) * 1000, 1),
        }

    if unsupported_facets:
        load_error = None
        for facet in unsupported_facets:
            spec_rows.append(
                {
                    "name": facet.observed_value or facet.message,
                    "status": STATUS_UNSUPPORTED,
                    "reason": facet.message,
                    "passed_on_fixture": None,
                }
            )
    else:
        try:
            specset = ids.open(str(ids_path))
            model = ifc_model if ifc_model is not None else open_ifc_model(ifc_path)
            specset.validate(model)
            reported = reporter.Json(specset).report()
            for spec in reported.get("specifications") or []:
                passed = bool(spec.get("status", True))
                spec_rows.append(
                    {
                        "name": spec.get("name") or "Unknown Specification",
                        "ifc_version": spec.get("ifcVersion") or spec.get("ifc_version"),
                        "cardinality": spec.get("cardinality"),
                        "total_applicable": spec.get("total_applicable"),
                        "passed_on_fixture": passed,
                        "status": classify_specification(
                            unsupported=False,
                            load_error=None,
                            spec_passed=passed,
                        ),
                    }
                )
        except Exception as exc:  # noqa: BLE001 — coverage must not swallow
            load_error = f"{type(exc).__name__}: {exc}"
            spec_rows.append(
                {
                    "name": ids_path.name,
                    "status": STATUS_LOAD_ERROR,
                    "reason": load_error,
                    "passed_on_fixture": None,
                }
            )

    return {
        "domain": domain,
        "path": str(ids_path.as_posix()),
        "file_name": ids_path.name,
        "kind": classify_ids_kind(ids_path.name),
        "sha256": _sha256_file(ids_path),
        "bytes": ids_path.stat().st_size,
        "load_error": load_error,
        "audit_issue_count": len(audit_issues),
        "unsupported_facet_count": len(unsupported_facets),
        "audit_issues": _issue_digest(audit_issues[:20]),
        "specifications": spec_rows,
        "elapsed_ms": round((perf_counter() - started) * 1000, 1),
    }


def _inventory_mappings(pack_dir: Path) -> list[dict[str, Any]]:
    mapping_dir = pack_dir / "mappings"
    if not mapping_dir.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(mapping_dir.iterdir()):
        if not path.is_file():
            continue
        rows.append(
            {
                "file_name": path.name,
                "bytes": path.stat().st_size,
                "sha256": _sha256_file(path),
                "executed": False,
                "note": "Vendor mapping inventory only; not executed (architecture freeze).",
            }
        )
    return rows


def _summarize(files: list[dict[str, Any]]) -> dict[str, Any]:
    specs = [spec for row in files for spec in row.get("specifications") or []]
    counts = {
        STATUS_PASS: 0,
        STATUS_FAIL: 0,
        STATUS_UNSUPPORTED: 0,
        STATUS_LOAD_ERROR: 0,
    }
    for spec in specs:
        status = str(spec.get("status") or STATUS_LOAD_ERROR)
        counts[status] = counts.get(status, 0) + 1
    executable = counts[STATUS_PASS] + counts[STATUS_FAIL]
    return {
        "ids_file_count": len(files),
        "specification_count": len(specs),
        "executable": executable,
        "executable_pass_on_fixture": counts[STATUS_PASS],
        "executable_fail_on_fixture": counts[STATUS_FAIL],
        "unsupported": counts[STATUS_UNSUPPORTED],
        "load_error": counts[STATUS_LOAD_ERROR],
        "by_domain": _by_domain(files),
        "by_kind": _by_kind(files),
    }


def _empty_bucket() -> dict[str, int]:
    return {
        "files": 0,
        "specifications": 0,
        "executable_pass_on_fixture": 0,
        "executable_fail_on_fixture": 0,
        "unsupported": 0,
        "load_error": 0,
    }


def _accumulate_file(bucket: dict[str, int], row: dict[str, Any]) -> None:
    bucket["files"] += 1
    specs = row.get("specifications") or []
    if specs:
        bucket["specifications"] += len(specs)
        for spec in specs:
            status = str(spec.get("status") or STATUS_LOAD_ERROR)
            if status == STATUS_PASS:
                bucket["executable_pass_on_fixture"] += 1
            elif status == STATUS_FAIL:
                bucket["executable_fail_on_fixture"] += 1
            elif status == STATUS_UNSUPPORTED:
                bucket["unsupported"] += 1
            else:
                bucket["load_error"] += 1
        return
    counts = row.get("counts") if isinstance(row.get("counts"), dict) else {}
    bucket["specifications"] += int(row.get("specification_count") or 0)
    bucket["executable_pass_on_fixture"] += int(counts.get(STATUS_PASS) or 0)
    bucket["executable_fail_on_fixture"] += int(counts.get(STATUS_FAIL) or 0)
    bucket["unsupported"] += int(counts.get(STATUS_UNSUPPORTED) or 0)
    bucket["load_error"] += int(counts.get(STATUS_LOAD_ERROR) or 0)


def _by_domain(files: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, dict[str, int]] = {}
    for row in files:
        domain = str(row.get("domain") or "unknown")
        bucket = grouped.setdefault(domain, _empty_bucket())
        _accumulate_file(bucket, row)
    return grouped


def _by_kind(files: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, dict[str, int]] = {
        KIND_ATTRIBUTES: _empty_bucket(),
        KIND_CLASSIFICATION: _empty_bucket(),
        KIND_OTHER: _empty_bucket(),
    }
    for row in files:
        kind = str(row.get("kind") or classify_ids_kind(str(row.get("file_name") or "")))
        bucket = grouped.setdefault(kind, _empty_bucket())
        _accumulate_file(bucket, row)
    return grouped


def build_moexp_ids_coverage(
    *,
    pack_dir: Path,
    ifc_path: Path,
    files: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    auditor = XmlIdsDocumentAuditor()
    ifc_model = open_ifc_model(ifc_path) if files is None else None
    evaluated = files if files is not None else [
        evaluate_ids_file(path, ifc_path=ifc_path, auditor=auditor, ifc_model=ifc_model)
        for path in discover_ids(pack_dir)
    ]
    summary = _summarize(evaluated)
    payload: dict[str, Any] = {
        "artifact_type": "moexp_ids_coverage",
        "schema_version": "1.1.0",
        "claim_level": CLAIM_LEVEL,
        "customer_accuracy_not_established": True,
        "closes_rt002_customer_profile": False,
        "public_moexp_ids_present": True,
        "claim_boundary": CLAIM_BOUNDARY,
        "source_page": SOURCE_PAGE,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "machine": _machine_fingerprint(),
        "pack_dir": str(pack_dir.as_posix()),
        "fixture_ifc": {
            "path": str(ifc_path.as_posix()),
            "sha256": _sha256_file(ifc_path) if ifc_path.is_file() else None,
            "bytes": ifc_path.stat().st_size if ifc_path.is_file() else None,
            "note": "Open wall Pset fixture. Not a MOEXP CIM. Fail on fixture ≠ unsupported spec.",
        },
        "icmm_ids_published": False,
        "icmm_note": (
            "ICMM 3.3 is PDF-only on the TIM page as of 2026-08-13; no IDS listed."
        ),
        "mappings": _inventory_mappings(pack_dir),
        "summary": summary,
        "files": [
            {
                **{key: value for key, value in row.items() if key != "specifications"},
                "kind": row.get("kind") or classify_ids_kind(str(row.get("file_name") or "")),
                "specification_count": len(row.get("specifications") or []),
                "counts": {
                    STATUS_PASS: sum(
                        1
                        for spec in row.get("specifications") or []
                        if spec.get("status") == STATUS_PASS
                    ),
                    STATUS_FAIL: sum(
                        1
                        for spec in row.get("specifications") or []
                        if spec.get("status") == STATUS_FAIL
                    ),
                    STATUS_UNSUPPORTED: sum(
                        1
                        for spec in row.get("specifications") or []
                        if spec.get("status") == STATUS_UNSUPPORTED
                    ),
                    STATUS_LOAD_ERROR: sum(
                        1
                        for spec in row.get("specifications") or []
                        if spec.get("status") == STATUS_LOAD_ERROR
                    ),
                },
                "failed_specification_names": [
                    spec.get("name")
                    for spec in row.get("specifications") or []
                    if spec.get("status") == STATUS_FAIL
                ],
                "unsupported_or_load_error": [
                    spec
                    for spec in row.get("specifications") or []
                    if spec.get("status") in {STATUS_UNSUPPORTED, STATUS_LOAD_ERROR}
                ],
            }
            for row in evaluated
        ],
    }
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    payload["content_sha256"] = _sha256_bytes(encoded)
    return payload


def render_moexp_ids_coverage_markdown(coverage: dict[str, Any]) -> str:
    summary = coverage.get("summary") if isinstance(coverage.get("summary"), dict) else {}
    lines = [
        "<!-- claims-lint: allow-file reason=\"Official MOEXP IDS engine coverage; fixture fail is not product accuracy\" -->",
        "# Official MOEXP IDS coverage (IfcTester)",
        "",
        f"**claim_level:** `{coverage.get('claim_level')}`",
        f"**customer_accuracy_not_established:** `{coverage.get('customer_accuracy_not_established')}`",
        f"**closes_rt002_customer_profile:** `{coverage.get('closes_rt002_customer_profile')}`",
        "",
        str(coverage.get("claim_boundary") or ""),
        "",
        f"Source: {coverage.get('source_page')}",
        "",
        "## Engine coverage (headline)",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| IDS files | {summary.get('ids_file_count')} |",
        f"| Specifications | {summary.get('specification_count')} |",
        f"| Executable (IfcTester ran) | {summary.get('executable')} |",
        f"| Unsupported facets | {summary.get('unsupported')} |",
        f"| Load errors | {summary.get('load_error')} |",
        "",
        "## Fixture probe (not CIM compliance)",
        "",
        "Open fixture `samples/ifc/wall-pset-qto-pass.ifc`. Fail here means the spec ran and the wall fixture did not satisfy it.",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| Pass on fixture | {summary.get('executable_pass_on_fixture')} |",
        f"| Fail on fixture | {summary.get('executable_fail_on_fixture')} |",
        "",
        "## By domain",
        "",
        "| Domain | files | specs | exec pass | exec fail | unsupported | load error |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    by_domain = summary.get("by_domain") if isinstance(summary.get("by_domain"), dict) else {}
    for domain, bucket in sorted(by_domain.items()):
        if not isinstance(bucket, dict):
            continue
        lines.append(
            f"| {domain} | {bucket.get('files')} | {bucket.get('specifications')} | "
            f"{bucket.get('executable_pass_on_fixture')} | {bucket.get('executable_fail_on_fixture')} | "
            f"{bucket.get('unsupported')} | {bucket.get('load_error')} |"
        )
    lines.extend(
        [
            "",
            "## By pack kind (filename, not a new run)",
            "",
            "`attributes` = published `Требования_…` IDS. `classification` = published `Проверка_КСИ_…` IDS.",
            "This split does not mean CIM compliance. Engine coverage only.",
            "",
            "| Kind | files | specs | exec pass | exec fail | unsupported | load error |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    by_kind = summary.get("by_kind") if isinstance(summary.get("by_kind"), dict) else {}
    for kind, bucket in sorted(by_kind.items()):
        if not isinstance(bucket, dict):
            continue
        lines.append(
            f"| {kind} | {bucket.get('files')} | {bucket.get('specifications')} | "
            f"{bucket.get('executable_pass_on_fixture')} | {bucket.get('executable_fail_on_fixture')} | "
            f"{bucket.get('unsupported')} | {bucket.get('load_error')} |"
        )
    lines.extend(
        [
            "",
            str(coverage.get("icmm_note") or ""),
            "",
            f"Generated at: `{coverage.get('generated_at')}`",
            f"content_sha256: `{coverage.get('content_sha256')}`",
            f"machine: `{json.dumps(coverage.get('machine'), ensure_ascii=False)}`",
            "",
        ]
    )
    return "\n".join(lines)


def attach_by_kind(coverage: dict[str, Any]) -> dict[str, Any]:
    """Add filename-derived pack kind without re-running IfcTester."""

    files = coverage.get("files")
    if not isinstance(files, list):
        raise ValueError("coverage.files must be a list")
    for row in files:
        if isinstance(row, dict):
            row["kind"] = classify_ids_kind(str(row.get("file_name") or ""))
    summary = coverage.get("summary")
    if not isinstance(summary, dict):
        summary = {}
        coverage["summary"] = summary
    summary["by_kind"] = _by_kind(files)
    coverage["schema_version"] = "1.1.0"
    coverage.pop("content_sha256", None)
    encoded = json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    coverage["content_sha256"] = _sha256_bytes(encoded)
    return coverage


def write_moexp_ids_coverage(
    coverage: dict[str, Any],
    *,
    artifacts_json: Path,
    evidence_json: Path,
    evidence_md: Path,
) -> None:
    text = json.dumps(coverage, ensure_ascii=False, indent=2) + "\n"
    for path in (artifacts_json, evidence_json):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    evidence_md.parent.mkdir(parents=True, exist_ok=True)
    evidence_md.write_text(render_moexp_ids_coverage_markdown(coverage), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack-dir", type=Path, default=None)
    parser.add_argument("--ifc", type=Path, default=None)
    parser.add_argument(
        "--from-json",
        type=Path,
        default=None,
        help="Re-group an existing coverage JSON (by_kind) without re-running IfcTester.",
    )
    args = parser.parse_args(argv)
    root = repo_root()
    if args.from_json is not None:
        coverage = attach_by_kind(json.loads(args.from_json.read_text(encoding="utf-8")))
    else:
        pack_dir = args.pack_dir or default_pack_dir(root)
        ifc_path = args.ifc or default_fixture_ifc(root)
        coverage = build_moexp_ids_coverage(pack_dir=pack_dir, ifc_path=ifc_path)
    write_moexp_ids_coverage(
        coverage,
        artifacts_json=root / "artifacts" / "norm-pack-moexp" / "coverage.json",
        evidence_json=root / "docs" / "evidence" / "norm-pack-moexp-coverage-2026-08.json",
        evidence_md=root / "docs" / "evidence" / "norm-pack-moexp-coverage-2026-08.md",
    )
    print(json.dumps(coverage.get("summary"), ensure_ascii=False, indent=2))
    print("content_sha256", coverage.get("content_sha256"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
