"""Pin GNI anonymization scripts without rewriting them.

Upstream ``code/anonymize_bim_*.py`` are MIT research scripts with hardcoded
operator paths and pandas/tqdm. We clone, hash, and record SKIPPED execution.
We do not vendor GPLv3 IFC and we do not reimplement redaction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aerobim.tools.benchmark_project_package import repo_root

CLAIM_LEVEL = "gni_anonymization_pin"
CLAIM_BOUNDARY = (
    "MIT anonymization scripts from github.com/ZijianWang-ZW/GNI-BIM-Dataset "
    "are pinned by SHA-256. Execution is SKIPPED: scripts hardcode local paths "
    "and we only have already-anonymized Zenodo IFC. Not product accuracy."
)
EXPECTED_SCRIPTS = (
    "code/LICENSE",
    "code/anonymize_bim_fundamentals.py",
    "code/anonymize_bim_projects.py",
)
UPSTREAM = "https://github.com/ZijianWang-ZW/GNI-BIM-Dataset"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_payload(*, code_root: Path | None, repo: Path) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    status = "SKIPPED"
    reason = "AEROBIM_GNI_CODE_ROOT / .local/gni-bim-code missing; clone upstream MIT scripts"
    if code_root is not None and code_root.is_dir():
        status = "PINNED"
        reason = str(code_root)
        for rel in EXPECTED_SCRIPTS:
            path = code_root / rel
            if path.is_file():
                files.append(
                    {
                        "path": rel,
                        "bytes": path.stat().st_size,
                        "sha256": _sha256_file(path),
                        "present": True,
                    }
                )
            else:
                files.append({"path": rel, "present": False, "sha256": None, "bytes": None})
                status = "INCOMPLETE"
        if status == "PINNED" and any(not item["present"] for item in files):
            status = "INCOMPLETE"
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "artifact_type": "gni_anonymization_pin",
        "claim_level": CLAIM_LEVEL,
        "claim_boundary": CLAIM_BOUNDARY,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "upstream": UPSTREAM,
        "license": "MIT (code/); CC BY 4.0 (Zenodo models, not this pin)",
        "execution": "SKIPPED",
        "execution_reason": (
            "Scripts hardcode operator paths and depend on pandas/tqdm. "
            "Released GNI IFC are already anonymized. Do not rewrite."
        ),
        "status": status,
        "reason": reason,
        "files": files,
        "repo_relative_hint": str((repo / ".local" / "gni-bim-code").as_posix()),
    }
    encoded = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    body["content_sha256"] = hashlib.sha256(encoded).hexdigest()
    return body


def render_markdown(payload: dict[str, Any]) -> str:
    rows = []
    for item in payload.get("files") or []:
        sha = item.get("sha256") or "missing"
        rows.append(f"| `{item.get('path')}` | {item.get('present')} | `{sha}` |")
    table = "\n".join(["| path | present | sha256 |", "| --- | --- | --- |", *rows]) if rows else "_none_"
    return "\n".join(
        [
            "<!-- claims-lint: allow-file reason=\"GNI anonymization script pin; execution SKIPPED\" -->",
            "---",
            'title: "GNI anonymization script pin"',
            f"date: {str(payload.get('generated_at') or '')[:10]}",
            f"claim_level: {payload.get('claim_level')}",
            "claim_boundary: >-",
            f"  {payload.get('claim_boundary')}",
            "---",
            "",
            "# GNI anonymization script pin",
            "",
            f"- status: **{payload.get('status')}**",
            f"- execution: **{payload.get('execution')}** — {payload.get('execution_reason')}",
            f"- upstream: {payload.get('upstream')}",
            f"- content_sha256: `{payload.get('content_sha256')}`",
            "",
            table,
            "",
            "```bash",
            "git clone --depth 1 https://github.com/ZijianWang-ZW/GNI-BIM-Dataset .local/gni-bim-code",
            "cd backend",
            "python -m aerobim.tools.export_gni_anonymization_pin",
            "```",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code-root", type=Path, default=None)
    args = parser.parse_args(argv)
    root = repo_root()
    env = args.code_root or os.environ.get("AEROBIM_GNI_CODE_ROOT")
    code_root = Path(env) if env else (root / ".local" / "gni-bim-code")
    if not code_root.is_dir():
        code_root = None
    payload = build_payload(code_root=code_root, repo=root)
    out = root / "artifacts" / "gni-anonymization-pin"
    out.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    (out / "gni-anonymization-pin.json").write_text(text, encoding="utf-8")
    (root / "docs" / "evidence" / "gni-anonymization-pin-2026-08.json").write_text(
        text, encoding="utf-8"
    )
    (root / "docs" / "evidence" / "gni-anonymization-pin-2026-08.md").write_text(
        render_markdown(payload), encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] in {"PINNED", "SKIPPED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
