"""Official MOEXP IDS against one local GNI student IFC.

Does not overwrite the fixture coverage snapshot. Student models are not
CIM compliance and do not close RT-001 / RT-002.
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
from aerobim.tools.export_moexp_ids_coverage import (
    build_moexp_ids_coverage,
    default_pack_dir,
    write_moexp_ids_coverage,
)

CLAIM_LEVEL = "gni_student_vs_official_ids"
CLAIM_BOUNDARY = (
    "Official MOEXP IDS executed on one GNI student IFC. Not CIM compliance, "
    "not Samolet acceptance, not product accuracy. Does not overwrite the "
    "fixture MOEXP coverage snapshot."
)
DEFAULT_REL = "2025_BIMfundamentals/2025_BIMfundamentals/model_190.ifc"


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def skipped_payload(*, reason: str) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "artifact_type": "moexp_on_gni_sample",
        "claim_level": CLAIM_LEVEL,
        "claim_boundary": CLAIM_BOUNDARY,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "status": "SKIPPED",
        "reason": reason,
        "closes_rt001": False,
        "closes_rt002": False,
    }
    encoded = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    body["content_sha256"] = _sha256_bytes(encoded)
    return body


def render_skipped(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            '<!-- claims-lint: allow-file reason="MOEXP IDS on GNI student sample; not CIM compliance" -->',
            "---",
            'title: "MOEXP IDS on a GNI student IFC"',
            f"date: {str(payload.get('generated_at') or '')[:10]}",
            f"claim_level: {payload.get('claim_level')}",
            "claim_boundary: >-",
            f"  {payload.get('claim_boundary')}",
            "---",
            "",
            "# MOEXP IDS on a GNI student IFC",
            "",
            f"- status: **{payload.get('status')}** — {payload.get('reason')}",
            f"- content_sha256: `{payload.get('content_sha256')}`",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ifc", type=Path, default=None)
    parser.add_argument("--pack-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    root = repo_root()
    gni_env = os.environ.get("AEROBIM_GNI_BIM_ROOT")
    gni_root = Path(gni_env) if gni_env else (root / ".local" / "gni-bim")
    ifc_path = args.ifc or (gni_root / DEFAULT_REL)
    evidence_json = root / "docs" / "evidence" / "moexp-on-gni-sample-2026-08.json"
    evidence_md = root / "docs" / "evidence" / "moexp-on-gni-sample-2026-08.md"
    artifacts = root / "artifacts" / "moexp-on-gni-sample" / "coverage.json"
    if not ifc_path.is_file():
        payload = skipped_payload(
            reason=f"GNI sample missing: {ifc_path}. Dataset stays gitignored / on Zenodo."
        )
        artifacts.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        artifacts.write_text(text, encoding="utf-8")
        evidence_json.write_text(text, encoding="utf-8")
        evidence_md.write_text(render_skipped(payload), encoding="utf-8")
        print(json.dumps({"status": "SKIPPED", "reason": payload["reason"]}))
        return 0
    pack_dir = args.pack_dir or default_pack_dir(root)
    coverage = build_moexp_ids_coverage(pack_dir=pack_dir, ifc_path=ifc_path)
    coverage["claim_level"] = CLAIM_LEVEL
    coverage["claim_boundary"] = CLAIM_BOUNDARY
    coverage["closes_rt001"] = False
    coverage["closes_rt002"] = False
    try:
        coverage["gni_sample"] = ifc_path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        coverage["gni_sample"] = ifc_path.name
    coverage["status"] = "RUN"
    write_moexp_ids_coverage(
        coverage,
        artifacts_json=artifacts,
        evidence_json=evidence_json,
        evidence_md=evidence_md,
    )
    summary = coverage.get("summary") or {}
    evidence_md.write_text(
        "\n".join(
            [
                '<!-- claims-lint: allow-file reason="MOEXP IDS on GNI student sample; not CIM compliance" -->',
                "---",
                'title: "MOEXP IDS on a GNI student IFC"',
                f"date: {str(coverage.get('generated_at') or '')[:10]}",
                f"claim_level: {CLAIM_LEVEL}",
                "claim_boundary: >-",
                f"  {CLAIM_BOUNDARY}",
                "---",
                "",
                "# MOEXP IDS on a GNI student IFC",
                "",
                f"- sample: `{coverage.get('gni_sample')}`",
                f"- executable: **{summary.get('executable')}** pass **{summary.get('executable_pass_on_fixture')}** fail **{summary.get('executable_fail_on_fixture')}**",
                "- this is a student model, **not** CIM compliance, **not** Samolet",
                f"- content_sha256: `{coverage.get('content_sha256')}`",
                "",
                "Does not overwrite [`norm-pack-moexp-coverage-2026-08.md`](norm-pack-moexp-coverage-2026-08.md).",
                "",
                "```bash",
                "cd backend",
                "python -m aerobim.tools.run_moexp_on_gni_sample",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(coverage.get("summary"), ensure_ascii=False, indent=2))
    print("content_sha256", coverage.get("content_sha256"))
    print("claim_level", coverage.get("claim_level"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
