"""Validate the SPb GAU CGE official IDS profile (fail-closed) + fixture probe.

Gates, in order; any failure aborts the run (silence is never success):
1. manifest parses under the domain honesty locks (``official_ids_profile``);
2. every declared ``.ids`` file exists, byte-size and SHA-256 match the manifest,
   and no undeclared ``.ids`` sits in the pack root;
3. every file validates against the vendored buildingSMART IDS 1.0 XSD
   (``samples/ids-xsd/ids.xsd``, CC BY-ND 4.0) — a non-1.0 document fails here;
4. every file parses through IfcTester (``ids.open``) and exposes specifications;
5. fixture determinism probe: two full IfcTester runs of the whole profile
   against ``samples/ifc/wall-pset-qto-pass.ifc`` must produce byte-identical
   issue signatures.

Result is written to ``docs/evidence/spb-cge-profile-validation-2026-08.json``
with per-file hashes. The profile is an OFFICIAL_PUBLISHED ruleset bundle, not
a customer-signed acceptance profile: it does not close RT-001/RT-002/RT-003.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aerobim.domain.official_ids_profile import (
    OfficialIdsProfile,
    OfficialIdsProfileError,
    canonical_profile_hash,
    find_file_mismatches,
    parse_official_ids_profile,
)
from aerobim.infrastructure.adapters.ifc_tester_ids_validator import IfcTesterIdsValidator

EVIDENCE_SCHEMA_VERSION = "1.0.0"
EVIDENCE_ARTIFACT_TYPE = "spb_cge_profile_validation"
DEFAULT_MANIFEST = Path("samples/profiles/spb-cge/manifest.json")
DEFAULT_XSD = Path("samples/ids-xsd/ids.xsd")
DEFAULT_FIXTURE_IFC = Path("samples/ifc/wall-pset-qto-pass.ifc")
DEFAULT_EVIDENCE_OUT = Path("docs/evidence/spb-cge-profile-validation-2026-08.json")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _sha256_file(path: Path) -> str:
    """SHA-256 of on-disk bytes. Used for ``.ids`` (git ``binary``; publisher XML)."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_text_ci(path: Path) -> str:
    """Hash UTF-8 text as Linux CI would (LF), matching DATASET_MANIFEST.

    JSON is ``*.json text eol=lf`` in ``.gitattributes``. Windows worktrees can
    still show CRLF; stripping CR makes evidence ``manifest_sha256`` match the
    file Git ships, not the local checkout. Do not use this for ``.ids``.
    """
    data = path.read_bytes()
    if b"\r\n" in data and b"\x00" not in data[:8192]:
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            pass
        else:
            data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def _resolve_under(root: Path, value: Path) -> Path:
    return value if value.is_absolute() else root / value


def _must_stay_under(root: Path, path: Path, *, what: str) -> Path:
    """Fail-closed path jail after resolve (symlinks included)."""
    resolved = path.resolve()
    root_res = root.resolve()
    try:
        resolved.relative_to(root_res)
    except ValueError:
        raise OfficialIdsProfileError(
            f"{what} resolves outside the allowed root ({resolved} vs {root_res})"
        ) from None
    return resolved


def load_manifest(manifest_path: Path) -> OfficialIdsProfile:
    if not manifest_path.is_file():
        raise OfficialIdsProfileError(f"manifest missing: {manifest_path}")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OfficialIdsProfileError(f"manifest is not valid UTF-8 JSON: {exc}") from exc
    return parse_official_ids_profile(payload)


def collect_actual_files(
    profile: OfficialIdsProfile, pack_root: Path
) -> dict[str, tuple[str, int] | None]:
    """Observed (sha256, size) per declared path, plus undeclared on-disk .ids."""
    actual: dict[str, tuple[str, int] | None] = {}
    for entry in profile.files:
        path = pack_root / entry.path
        if not path.is_file():
            actual[entry.path] = None
            continue
        actual[entry.path] = (_sha256_file(path), path.stat().st_size)
    declared = {entry.path for entry in profile.files}
    if pack_root.is_dir():
        for path in sorted(pack_root.rglob("*.ids")):
            rel = path.relative_to(pack_root).as_posix()
            if rel not in declared:
                actual[rel] = (_sha256_file(path), path.stat().st_size)
    return actual


def xsd_validate_files(
    profile: OfficialIdsProfile,
    pack_root: Path,
    xsd_path: Path,
) -> dict[str, str]:
    """Validate each file against the vendored IDS 1.0 XSD; return path -> error."""
    if not xsd_path.is_file():
        raise OfficialIdsProfileError(f"IDS 1.0 XSD missing: {xsd_path}")
    try:
        import xmlschema
    except ModuleNotFoundError as exc:
        raise OfficialIdsProfileError(
            "xmlschema is required for IDS 1.0 XSD validation (ships with ifctester)"
        ) from exc
    try:
        schema = xmlschema.XMLSchema(str(xsd_path))
    except Exception as exc:  # noqa: BLE001 — fail-closed, record the reason
        raise OfficialIdsProfileError(f"IDS 1.0 XSD failed to load: {exc}") from exc
    errors: dict[str, str] = {}
    for entry in profile.files:
        path = pack_root / entry.path
        if not path.is_file():
            continue
        try:
            schema.validate(str(path))
        except Exception as exc:  # noqa: BLE001 — record, fail-closed below
            errors[entry.path] = str(exc).splitlines()[0][:300] if str(exc) else repr(exc)
    return errors


def parse_gate_files(profile: OfficialIdsProfile, pack_root: Path) -> dict[str, int]:
    """IfcTester ``ids.open`` per file; return path -> specification count."""
    try:
        from ifctester import ids
    except ModuleNotFoundError as exc:
        raise OfficialIdsProfileError("ifctester is required for the IDS parse gate") from exc
    counts: dict[str, int] = {}
    problems: list[str] = []
    for entry in profile.files:
        path = pack_root / entry.path
        if not path.is_file():
            continue
        try:
            document = ids.open(str(path))
        except Exception as exc:  # noqa: BLE001 — fail-closed, record the reason
            problems.append(f"{entry.path}: IfcTester failed to parse: {exc}")
            continue
        spec_count = len(getattr(document, "specifications", []) or [])
        if spec_count == 0:
            problems.append(f"{entry.path}: zero specifications — empty IDS is never a pass")
            continue
        counts[entry.path] = spec_count
    if problems:
        raise OfficialIdsProfileError("IDS parse gate failed: " + "; ".join(problems))
    return counts


def fixture_probe_signature(
    profile: OfficialIdsProfile,
    pack_root: Path,
    ifc_path: Path,
) -> tuple[tuple[str, str, str, str], ...]:
    """One full profile run against the fixture IFC; deterministic issue signature."""
    validator = IfcTesterIdsValidator()
    signature: list[tuple[str, str, str, str]] = []
    for entry in profile.files:
        issues = validator.validate(pack_root / entry.path, ifc_path)
        for issue in issues:
            signature.append((entry.path, issue.rule_id, issue.severity.value, issue.message))
    return tuple(signature)


def validate_profile(
    root: Path,
    *,
    manifest_path: Path | None = None,
    xsd_path: Path | None = None,
    probe_ifc: Path | None = None,
    probe_runs: int = 2,
) -> dict[str, Any]:
    manifest_path = _resolve_under(root, manifest_path or DEFAULT_MANIFEST)
    xsd_path = _resolve_under(root, xsd_path or DEFAULT_XSD)
    probe_ifc = _resolve_under(root, probe_ifc or DEFAULT_FIXTURE_IFC)

    profile = load_manifest(manifest_path)
    pack_root = _must_stay_under(
        root, _resolve_under(root, Path(profile.pack_root)), what="pack_root"
    )
    if not pack_root.is_dir():
        raise OfficialIdsProfileError(f"pack root missing: {pack_root}")

    mismatches = find_file_mismatches(profile, collect_actual_files(profile, pack_root))
    if mismatches:
        raise OfficialIdsProfileError("profile file integrity failed: " + "; ".join(mismatches))

    xsd_errors = xsd_validate_files(profile, pack_root, xsd_path)
    if xsd_errors:
        detail = "; ".join(f"{path}: {error}" for path, error in sorted(xsd_errors.items()))
        raise OfficialIdsProfileError(f"XSD validation failed (IDS 1.0, {xsd_path}): {detail}")

    spec_counts = parse_gate_files(profile, pack_root)

    if not probe_ifc.is_file():
        raise OfficialIdsProfileError(f"fixture IFC missing: {probe_ifc}")
    runs: list[tuple[tuple[str, str, str, str], ...]] = []
    for _ in range(max(2, probe_runs)):
        runs.append(fixture_probe_signature(profile, pack_root, probe_ifc))
    identical = all(run == runs[0] for run in runs[1:])
    if not identical:
        raise OfficialIdsProfileError(
            "fixture probe is not deterministic across runs — refusing to publish profile evidence"
        )
    signature_blob = json.dumps(runs[0], ensure_ascii=False, sort_keys=True)

    def _rel(path: Path) -> str:
        try:
            return path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            canonical = {
                "ids.xsd": "samples/ids-xsd/ids.xsd",
                "wall-pset-qto-pass.ifc": "samples/ifc/wall-pset-qto-pass.ifc",
            }.get(path.name)
            if canonical is not None:
                return canonical
            raise OfficialIdsProfileError(
                f"refusing to record a path outside the repo: {path}"
            ) from None

    return {
        "artifact_type": EVIDENCE_ARTIFACT_TYPE,
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "profile_id": profile.profile_id,
        "human_name": profile.human_name,
        "provenance_status": profile.provenance_status,
        "signed_by_customer": False,
        "samolet_alias": False,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "source_page": profile.source_page,
        "retrieval_date": profile.retrieval_date,
        "manifest_path": _rel(manifest_path),
        "manifest_sha256": _sha256_text_ci(manifest_path),
        "canonical_profile_hash": canonical_profile_hash(profile),
        "ids_xsd": {
            "path": _rel(xsd_path),
            "ids_schema_version": "1.0",
            "xsd_sha256": _sha256_file(xsd_path),
        },
        "files": [
            {
                "path": entry.path,
                "subject": entry.subject,
                "sha256": entry.sha256,
                "size_bytes": entry.size_bytes,
                "doc_edition": entry.doc_edition,
                "specifications": spec_counts[entry.path],
            }
            for entry in profile.files
        ],
        "totals": {
            "files": len(profile.files),
            "specifications": sum(spec_counts.values()),
            "subjects": sorted(profile.subjects),
        },
        "fixture_probe": {
            "ifc": _rel(probe_ifc),
            "runs": len(runs),
            "identical": identical,
            "issues_per_run": [len(run) for run in runs],
            "signature_sha256": hashlib.sha256(signature_blob.encode("utf-8")).hexdigest(),
            "note": (
                "Fail on the wall fixture means the specs executed; it is not a CIM "
                "compliance verdict and not an expertise conclusion."
            ),
        },
        "claim_boundary": (
            "Проверка по опубликованному набору правил СПб ГАУ «ЦГЭ», без статуса "
            "экспертизы. Не закрывает RT-001/RT-002/RT-003; не подписанный заказчиком "
            "профиль приёмки."
        ),
        "engine": "IfcTester",
        "not_buildingsmart_ids_audit_tool_binary": True,
        "fixture_probe_is_not_expertise_verdict": True,
    }


_HOST_LEAK_MARKERS = (
    "C:/plans/",
    "C:\\plans\\",
    "Windows-11-",
    "/Users/",
    "/home/",
)


def _walk_strings(payload: Any) -> list[str]:
    found: list[str] = []
    if isinstance(payload, dict):
        for value in payload.values():
            found.extend(_walk_strings(value))
    elif isinstance(payload, list):
        for value in payload:
            found.extend(_walk_strings(value))
    elif isinstance(payload, str):
        found.append(payload)
    return found


def _assert_repo_relative_evidence(payload: dict[str, Any]) -> None:
    """Published evidence must not carry a host checkout path."""
    for text in _walk_strings(payload):
        lowered = text.replace("\\", "/")
        for marker in _HOST_LEAK_MARKERS:
            if marker.lower() in text or marker.lower() in lowered:
                raise OfficialIdsProfileError(
                    f"published evidence contains a host path marker ({marker!r})"
                )
        if len(text) >= 3 and text[0].isalpha() and text[1:3] in (":/", ":\\"):
            raise OfficialIdsProfileError(f"published evidence contains an absolute path: {text}")


def _require_repo_file(root: Path, rel: object, *, what: str) -> Path:
    """Resolve a published relative path; reject abs, ``..``, and jail escapes."""
    if not isinstance(rel, str) or not rel or rel.startswith("/"):
        raise OfficialIdsProfileError(f"{what} must be a repo-relative POSIX path")
    if ".." in Path(rel).parts:
        raise OfficialIdsProfileError(f"{what} must not contain ..")
    path = _must_stay_under(root, root / rel, what=what)
    if not path.is_file():
        raise OfficialIdsProfileError(f"{what} missing on disk: {rel}")
    return path


def verify_committed_evidence(
    root: Path,
    *,
    evidence_path: Path | None = None,
    live: dict[str, Any] | None = None,
) -> None:
    """Recompute hashes of the files next to the evidence; do not trust the JSON.

    ``generated_at`` is ignored: a five-minute gap between the run and the
    commit is not a bind. The bind is SHA-256 of the sitting manifest and
    of every ``.ids`` listed in the artifact.
    """
    evidence_path = evidence_path or (root / DEFAULT_EVIDENCE_OUT)
    if not evidence_path.is_file():
        raise OfficialIdsProfileError(f"committed evidence missing: {evidence_path}")
    try:
        committed = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OfficialIdsProfileError(f"committed evidence is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(committed, dict):
        raise OfficialIdsProfileError("committed evidence is not an object")

    _assert_repo_relative_evidence(committed)

    manifest_path = _require_repo_file(
        root, committed.get("manifest_path"), what="committed evidence manifest_path"
    )
    recomputed_manifest = _sha256_text_ci(manifest_path)
    recorded_manifest = committed.get("manifest_sha256")
    if recorded_manifest != recomputed_manifest:
        raise OfficialIdsProfileError(
            "committed evidence manifest_sha256 does not match the sitting manifest "
            f"({committed.get('manifest_path')})"
        )

    raw_xsd = committed.get("ids_xsd")
    xsd_meta: dict[str, Any] = raw_xsd if isinstance(raw_xsd, dict) else {}
    xsd_path = _require_repo_file(
        root, xsd_meta.get("path"), what="committed evidence ids_xsd.path"
    )
    if xsd_meta.get("xsd_sha256") != _sha256_file(xsd_path):
        raise OfficialIdsProfileError(
            "committed evidence ids_xsd.xsd_sha256 does not match the sitting XSD"
        )

    raw_probe = committed.get("fixture_probe")
    probe_meta: dict[str, Any] = raw_probe if isinstance(raw_probe, dict) else {}
    _require_repo_file(root, probe_meta.get("ifc"), what="committed evidence fixture_probe.ifc")

    profile = load_manifest(manifest_path)
    pack_root = _must_stay_under(
        root, _resolve_under(root, Path(profile.pack_root)), what="pack_root"
    )
    rows = committed.get("files")
    if not isinstance(rows, list):
        raise OfficialIdsProfileError("committed evidence files[] is missing")
    by_path = {row.get("path"): row for row in rows if isinstance(row, dict)}
    declared = {entry.path for entry in profile.files}
    if set(by_path) != declared:
        raise OfficialIdsProfileError(
            "committed evidence files[] does not match the sitting manifest inventory"
        )
    for entry in profile.files:
        row = by_path[entry.path]
        on_disk = pack_root / entry.path
        if not on_disk.is_file():
            raise OfficialIdsProfileError(f"evidence file missing on disk: {entry.path}")
        disk_sha = _sha256_file(on_disk)
        if row.get("sha256") != disk_sha:
            raise OfficialIdsProfileError(
                f"committed evidence sha256 does not match sitting file: {entry.path}"
            )
        if row.get("sha256") != entry.sha256:
            raise OfficialIdsProfileError(
                f"committed evidence sha256 does not match the sitting manifest: {entry.path}"
            )

    if committed.get("canonical_profile_hash") != canonical_profile_hash(profile):
        raise OfficialIdsProfileError(
            "committed evidence canonical_profile_hash does not match the sitting manifest"
        )
    for flag in (
        "signed_by_customer",
        "closes_rt001",
        "closes_rt002",
        "closes_rt003",
        "samolet_alias",
    ):
        if committed.get(flag) is not False:
            raise OfficialIdsProfileError(f"committed evidence {flag} must be JSON false")
    if committed.get("engine") != "IfcTester":
        raise OfficialIdsProfileError("committed evidence engine must be IfcTester")
    if committed.get("not_buildingsmart_ids_audit_tool_binary") is not True:
        raise OfficialIdsProfileError(
            "committed evidence must state it is not the buildingSMART IDS-Audit-tool binary"
        )
    if committed.get("fixture_probe_is_not_expertise_verdict") is not True:
        raise OfficialIdsProfileError(
            "committed evidence must state the fixture probe is not an expertise verdict"
        )

    if live is not None:
        for key in (
            "manifest_sha256",
            "canonical_profile_hash",
            "signed_by_customer",
            "closes_rt001",
            "closes_rt002",
            "closes_rt003",
            "samolet_alias",
        ):
            if committed.get(key) != live.get(key):
                raise OfficialIdsProfileError(
                    f"committed evidence {key} does not match the live validation payload"
                )
        raw_live_xsd = live.get("ids_xsd")
        live_xsd: dict[str, Any] = raw_live_xsd if isinstance(raw_live_xsd, dict) else {}
        if xsd_meta.get("xsd_sha256") != live_xsd.get("xsd_sha256"):
            raise OfficialIdsProfileError(
                "committed evidence ids_xsd.xsd_sha256 does not match the live validation payload"
            )
        raw_live_probe = live.get("fixture_probe")
        live_probe: dict[str, Any] = raw_live_probe if isinstance(raw_live_probe, dict) else {}
        committed_probe = probe_meta
        for key in ("signature_sha256", "issues_per_run", "identical"):
            if committed_probe.get(key) != live_probe.get(key):
                raise OfficialIdsProfileError(
                    f"committed evidence fixture_probe.{key} does not match the live run"
                )


def write_evidence(payload: dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=repo_root())
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--xsd", type=Path, default=None)
    parser.add_argument("--probe-ifc", type=Path, default=None)
    parser.add_argument("--evidence-out", type=Path, default=None)
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Validate only; do not write the evidence artifact",
    )
    parser.add_argument(
        "--verify-committed-evidence",
        action="store_true",
        help=(
            "After a live run, recompute hashes of the sitting manifest and "
            ".ids files and compare them to the committed evidence JSON"
        ),
    )
    args = parser.parse_args(argv)

    root = args.root.resolve()
    try:
        payload = validate_profile(
            root,
            manifest_path=args.manifest,
            xsd_path=args.xsd,
            probe_ifc=args.probe_ifc,
        )
        if args.verify_committed_evidence:
            verify_committed_evidence(
                root,
                evidence_path=args.evidence_out or (root / DEFAULT_EVIDENCE_OUT),
                live=payload,
            )
            print("committed evidence re-hash OK")
    except OfficialIdsProfileError as exc:
        print(f"SPB-CGE PROFILE FAILED: {exc}", file=sys.stderr)
        return 1

    out_path = args.evidence_out or (root / DEFAULT_EVIDENCE_OUT)
    if not args.no_write:
        write_evidence(payload, out_path)
    totals = payload["totals"]
    probe = payload["fixture_probe"]
    print(
        f"SPB-CGE PROFILE OK: {totals['files']} files, "
        f"{totals['specifications']} specifications, subjects={totals['subjects']}"
    )
    print(
        f"fixture probe: {probe['runs']} identical runs, "
        f"{probe['issues_per_run'][0]} issues, signature {probe['signature_sha256'][:16]}…"
    )
    if not args.no_write:
        print(f"evidence written: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
