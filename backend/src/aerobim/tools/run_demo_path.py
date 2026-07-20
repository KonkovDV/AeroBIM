"""Track A5 — fixture demo path: upload → analyze → review exports → BCF 2.1.

World-practice posture (buildingSMART openBIM, 2025–2026):
- Week-1 coordination handoff is **BCF-XML file exchange** (default 2.1).
- BCF-API / OpenCDE push is an escalation path, not the demo gate.
- Demo proves the deterministic review loop on a **fixture pack**, not customer
  accuracy, full SP/GOST, or Solibri replacement.

Claim boundary: this tool must never emit publishable customer precision or
imply ``customer_confirmed`` typical-errors coverage. BCF checks are a
**structural smoke** (version file + topic markup), not a full bSI conformance
suite and not a CDE import proof.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import shutil
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any
from xml.etree import ElementTree

from aerobim.core.config.settings import Settings
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.tools.benchmark_project_package import default_pack_path, repo_root

_SCHEMA_VERSION = "1.1.0"
_FORBIDDEN_CLAIMS = (
    "customer accuracy >90%",
    "full SP/GOST automation",
    "Solibri replacement",
    "autonomous engineer sign-off",
    "customer_confirmed typical-errors",
    "CDE roundtrip proven (requires customer import evidence)",
    "full buildingSMART BCF conformance certification",
)
_ALLOWED_BCF_VERSIONS = {"2.1", "3", "3.0"}
_GUID_FOLDER_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}/markup\.bcf$"
)


def pilot_moscow_pack_path() -> Path:
    return repo_root() / "samples" / "benchmarks" / "project-package-pilot-moscow-v1.json"


def normalize_bcf_version(raw: str) -> str:
    version = (raw or "").strip()
    if version not in _ALLOWED_BCF_VERSIONS:
        allowed = ", ".join(sorted(_ALLOWED_BCF_VERSIONS))
        raise ValueError(f"Unsupported BCF version {raw!r}; allowed: {allowed}")
    return "3.0" if version in {"3", "3.0"} else "2.1"


def _load_pack(pack_path: Path) -> dict[str, Any]:
    if not pack_path.is_file():
        raise FileNotFoundError(f"Demo pack not found: {pack_path}")
    payload = json.loads(pack_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or "request" not in payload:
        raise ValueError(f"Invalid demo pack manifest: {pack_path}")
    return payload


def _resolve_repo_file(raw: str) -> Path:
    root = repo_root().resolve()
    resolved = (root / raw).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"Pack path escapes repo root: {raw}")
    if not resolved.is_file():
        raise FileNotFoundError(resolved)
    return resolved


def _stage_into_storage(storage_dir: Path, source: Path, relative: str) -> str:
    """Copy a repo fixture into the storage jail; return storage-relative POSIX path."""
    raw = relative.replace("\\", "/")
    if raw.startswith("/") or raw.startswith("~") or (len(raw) >= 2 and raw[1] == ":"):
        raise ValueError(f"Unsafe staging relative path: {relative}")
    rel = raw.lstrip("/")
    candidate = Path(rel)
    if candidate.is_absolute() or candidate.drive or ".." in candidate.parts:
        raise ValueError(f"Unsafe staging relative path: {relative}")
    jail = storage_dir.resolve()
    target = (jail / rel).resolve()
    if not target.is_relative_to(jail):
        raise ValueError(f"Staging path escapes storage jail: {relative}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return rel


def _parse_bcf_version_id(version_xml: str) -> str:
    try:
        root = ElementTree.fromstring(version_xml)
    except ElementTree.ParseError as exc:
        raise ValueError("bcf.version is not well-formed XML") from exc
    # buildingSMART uses VersionId as an attribute on <Version>.
    observed = (root.attrib.get("VersionId") or "").strip()
    if not observed:
        # Tolerate rare element form if an exporter emits it.
        for child in root:
            if child.tag.split("}")[-1].lower() == "versionid" and (child.text or "").strip():
                observed = (child.text or "").strip()
                break
    if not observed:
        raise ValueError("bcf.version missing VersionId")
    return observed


def _validate_bcf_zip(payload: bytes, *, requested_version: str) -> dict[str, Any]:
    """Structural BCF smoke check — not full bSI schema conformance."""
    if not payload:
        raise ValueError("Empty BCF export")
    expected = normalize_bcf_version(requested_version)
    try:
        archive = zipfile.ZipFile(io.BytesIO(payload), "r")
    except zipfile.BadZipFile as exc:
        raise ValueError("BCF export is not a valid ZIP") from exc

    with archive:
        names = archive.namelist()
        if "bcf.version" not in names:
            raise ValueError("BCF ZIP missing bcf.version")
        try:
            version_xml = archive.read("bcf.version").decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("bcf.version is not valid UTF-8") from exc
        observed = _parse_bcf_version_id(version_xml)
        # Exporters may write "3.0" or "3"; normalize both sides.
        observed_norm = "3.0" if observed in {"3", "3.0"} else observed
        if observed_norm != expected:
            raise ValueError(f"BCF VersionId mismatch: requested {expected}, observed {observed}")

        markup = [name for name in names if _GUID_FOLDER_RE.match(name)]
        if not markup:
            raise ValueError(
                "BCF ZIP missing GUID-folder markup.bcf topics (expected {uuid}/markup.bcf)"
            )

        topic_count = 0
        for name in markup:
            raw = archive.read(name)
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ValueError(f"{name} is not valid UTF-8") from exc
            try:
                root = ElementTree.fromstring(text)
            except ElementTree.ParseError as exc:
                raise ValueError(f"{name} is not well-formed XML") from exc
            # BCF 2.1 uses Topic under Markup; tolerate namespaced tags.
            tags = {elem.tag.split("}")[-1].lower() for elem in root.iter()}
            if "topic" not in tags:
                raise ValueError(f"{name} missing Topic element")
            topic_count += 1

        return {
            "entry_count": len(names),
            "markup_topics": len(markup),
            "topics_with_topic_element": topic_count,
            "has_bcf_version": True,
            "version_requested": expected,
            "version_observed": observed,
            "check_level": "structural_smoke",
            "version_xml_snippet": version_xml.strip()[:240],
        }


def _repo_relative(path: Path) -> str:
    root = repo_root().resolve()
    resolved = path.resolve()
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError:
        return resolved.name


def run_demo_path(
    *,
    pack_path: Path | None = None,
    storage_dir: Path | None = None,
    bcf_version: str = "2.1",
    keep_storage: bool = False,
) -> dict[str, Any]:
    """Execute the API demo loop against a fixture pack inside an isolated storage jail."""
    try:
        from fastapi.testclient import TestClient
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError("FastAPI/httpx required for demo path") from exc

    from aerobim.presentation.http.api import create_http_app

    requested_bcf = normalize_bcf_version(bcf_version)
    selected_pack = pack_path or (
        pilot_moscow_pack_path() if pilot_moscow_pack_path().is_file() else default_pack_path()
    )
    pack = _load_pack(selected_pack)
    request = pack["request"]
    if not isinstance(request, dict):
        raise ValueError("Pack request must be an object")

    owns_temp_storage = False
    storage_dir_resolved: Path | None = None
    result: dict[str, Any] | None = None
    try:
        if storage_dir is None:
            storage_dir_resolved = Path(tempfile.mkdtemp(prefix="aerobim-demo-path-"))
            owns_temp_storage = True
        else:
            storage_dir_resolved = storage_dir.resolve()
            storage_dir_resolved.mkdir(parents=True, exist_ok=True)

        settings = Settings(
            application_name="aerobim-demo-path",
            environment="development",
            host="127.0.0.1",
            port=8080,
            storage_dir=storage_dir_resolved,
            debug=True,
            allow_anonymous_dev=True,
        )
        container = bootstrap_container(settings)

        started = perf_counter()
        steps: list[dict[str, Any]] = []

        with TestClient(create_http_app(container)) as client:
            health = client.get("/health")
            if health.status_code != 200:
                raise RuntimeError(f"Health check failed: {health.status_code} {health.text}")
            steps.append({"step": "health", "status_code": health.status_code, "ok": True})

            ifc_source = _resolve_repo_file(str(request["ifc_path"]))
            upload = client.post(
                "/v1/uploads",
                files={
                    "file": (
                        ifc_source.name,
                        ifc_source.read_bytes(),
                        "application/octet-stream",
                    )
                },
            )
            if upload.status_code != 200:
                raise RuntimeError(f"Upload failed: {upload.status_code} {upload.text}")
            upload_body = upload.json()
            uploaded_ifc_path = str(upload_body["path"])
            steps.append(
                {
                    "step": "upload_ifc",
                    "status_code": upload.status_code,
                    "path": uploaded_ifc_path,
                    "size_bytes": upload_body.get("size_bytes"),
                    "ok": True,
                }
            )

            analyze_payload: dict[str, Any] = {
                "ifc_path": uploaded_ifc_path,
                "project_name": pack.get("project_name"),
                "discipline": pack.get("discipline"),
                "stage": pack.get("stage"),
                "revision": pack.get("revision"),
                "doc_status": pack.get("doc_status"),
                "information_container_id": pack.get("information_container_id"),
            }

            for key in (
                "ids_path",
                "requirement_path",
                "technical_spec_path",
                "calculation_path",
                "pd_section_path",
                "rd_section_path",
            ):
                raw = request.get(key)
                if not raw:
                    continue
                staged = _stage_into_storage(
                    storage_dir_resolved,
                    _resolve_repo_file(str(raw)),
                    f"demo-pack/{Path(str(raw)).name}",
                )
                analyze_payload[key] = staged

            drawings_out: list[dict[str, Any]] = []
            for index, drawing in enumerate(request.get("drawings") or []):
                if not isinstance(drawing, dict) or not drawing.get("path"):
                    continue
                staged = _stage_into_storage(
                    storage_dir_resolved,
                    _resolve_repo_file(str(drawing["path"])),
                    f"demo-pack/drawings/{index}-{Path(str(drawing['path'])).name}",
                )
                drawings_out.append(
                    {
                        "path": staged,
                        "sheet_id": drawing.get("sheet_id"),
                        "format": drawing.get("format"),
                    }
                )
            if drawings_out:
                analyze_payload["drawings"] = drawings_out

            analyze_payload = {
                key: value for key, value in analyze_payload.items() if value is not None
            }

            analyze = client.post("/v1/analyze/project-package", json=analyze_payload)
            if analyze.status_code != 200:
                raise RuntimeError(f"Analyze failed: {analyze.status_code} {analyze.text}")
            report = analyze.json()
            report_id = str(report["report_id"])
            summary = report.get("summary") or {}
            analyze_passed = bool(summary.get("passed"))
            steps.append(
                {
                    "step": "analyze",
                    "status_code": analyze.status_code,
                    "report_id": report_id,
                    "issue_count": summary.get("issue_count"),
                    "passed": analyze_passed,
                    "ok": True,
                }
            )

            detail = client.get(f"/v1/reports/{report_id}")
            if detail.status_code != 200:
                raise RuntimeError(f"Report fetch failed: {detail.status_code} {detail.text}")
            steps.append({"step": "review_report", "status_code": detail.status_code, "ok": True})

            html = client.get(f"/v1/reports/{report_id}/export/html")
            if html.status_code != 200 or not html.text:
                raise RuntimeError(f"HTML export failed: {html.status_code}")
            steps.append(
                {
                    "step": "export_html",
                    "status_code": html.status_code,
                    "bytes": len(html.text.encode("utf-8")),
                    "ok": True,
                }
            )

            bcf = client.get(
                f"/v1/reports/{report_id}/export/bcf",
                params={"version": requested_bcf},
            )
            if bcf.status_code != 200:
                raise RuntimeError(f"BCF export failed: {bcf.status_code} {bcf.text}")
            bcf_meta = _validate_bcf_zip(bcf.content, requested_version=requested_bcf)
            steps.append(
                {
                    "step": "export_bcf",
                    "status_code": bcf.status_code,
                    "bytes": len(bcf.content),
                    "bcf": bcf_meta,
                    "ok": True,
                }
            )

            elapsed_ms = round((perf_counter() - started) * 1000.0, 2)
            sla_target_minutes = 30.0
            ids_staged = bool(request.get("ids_path"))
            result = {
                "artifact_type": "aerobim_demo_path",
                "schema_version": _SCHEMA_VERSION,
                "generated_at": datetime.now(tz=UTC).isoformat(),
                "track": "A5",
                "pack_id": pack.get("pack_id"),
                "pack_path": _repo_relative(selected_pack),
                "storage_dir": (
                    "<ephemeral>"
                    if owns_temp_storage and not keep_storage
                    else ("<ephemeral-retained>" if owns_temp_storage else "<user-provided>")
                ),
                "report_id": report_id,
                "elapsed_ms": elapsed_ms,
                "sla_target_minutes": sla_target_minutes,
                "sla_pass_fixture": (elapsed_ms / 60_000.0) <= sla_target_minutes,
                "bcf_version_requested": requested_bcf,
                "bcf_version_observed": bcf_meta["version_observed"],
                "analyze_passed": analyze_passed,
                "loop_ok": all(step.get("ok") for step in steps),
                "steps": steps,
                "openbim_practice": {
                    "ids_in_pack": ids_staged,
                    "bcf_file_exchange_default": "2.1",
                    "bcf_api_opencde": "escalation_only_not_demo_gate",
                    "bcf_check_level": "structural_smoke",
                    "references": [
                        "https://technical.buildingsmart.org/standards/bcf/",
                        "https://github.com/buildingSMART/BCF-XML",
                        "https://github.com/buildingSMART/BCF-API",
                    ],
                },
                "claim_boundary": {
                    "proven": [
                        "multipart upload into storage jail",
                        "deterministic project-package analyze on fixture",
                        "report retrieval",
                        "HTML export",
                        (
                            f"BCF {bcf_meta['version_observed']} ZIP structural smoke "
                            "(GUID-folder markup + Topic)"
                        ),
                    ],
                    "not_proven": list(_FORBIDDEN_CLAIMS),
                    "note": (
                        "loop_ok means the demo API chain succeeded; "
                        "analyze_passed is package compliance on the fixture and may be false"
                    ),
                },
                "ok": all(step.get("ok") for step in steps),
            }
            if owns_temp_storage and keep_storage:
                result["storage_retained"] = True
    finally:
        if owns_temp_storage and not keep_storage and storage_dir_resolved is not None:
            shutil.rmtree(storage_dir_resolved, ignore_errors=True)

    if result is None:
        raise RuntimeError("Demo path failed before producing a result payload")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "A5 demo path: upload → analyze → HTML/BCF structural smoke on a fixture pack "
            "(in-process ASGI; development auth)"
        )
    )
    parser.add_argument(
        "--pack",
        type=Path,
        default=None,
        help="Benchmark pack JSON (default: pilot-moscow-v1 if present)",
    )
    parser.add_argument(
        "--storage-dir",
        type=Path,
        default=None,
        help=(
            "Optional persistent storage jail (default: temp dir). "
            "Uses development/open auth via TestClient — do not point at production storage."
        ),
    )
    parser.add_argument(
        "--bcf-version",
        default="2.1",
        help="BCF export version: 2.1 (default) or 3.0",
    )
    parser.add_argument(
        "--keep-storage",
        action="store_true",
        help="Keep temp storage directory for manual UI follow-up",
    )
    parser.add_argument("--output", type=Path, default=None, help="Write evidence JSON")
    args = parser.parse_args()

    payload = run_demo_path(
        pack_path=args.pack,
        storage_dir=args.storage_dir,
        bcf_version=args.bcf_version,
        keep_storage=args.keep_storage,
    )
    serialized = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        tmp = args.output.with_suffix(".tmp")
        tmp.write_text(serialized, encoding="utf-8")
        tmp.replace(args.output)
    else:
        print(serialized)

    if not payload.get("ok"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
