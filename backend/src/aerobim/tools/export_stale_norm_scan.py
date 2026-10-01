"""Scan citing sources against the superseded-norm catalog.

Demo 20.08: Moscow AGR CIM requirements cite GOST R 21.101-2020 after
2026-04-01. Warning only — does not rewrite a violation into a pass.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aerobim.domain.stale_norm_citations import (
    CLAIM_BOUNDARY,
    CitingSource,
    NormDocument,
    collect_stale_citation_issues,
)
from aerobim.tools.benchmark_project_package import _machine_fingerprint, repo_root

CLAIM_LEVEL = "stale_norm_citation_scan"


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_catalog(path: Path) -> tuple[NormDocument, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw = payload.get("documents") or ()
    return tuple(NormDocument.from_mapping(item) for item in raw if isinstance(item, dict))


def load_sources(path: Path) -> tuple[CitingSource, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw = payload.get("sources") or ()
    return tuple(CitingSource.from_mapping(item) for item in raw if isinstance(item, dict))


def build_payload(
    *,
    catalog_path: Path,
    sources_path: Path,
    root: Path | None = None,
) -> dict[str, Any]:
    documents = load_catalog(catalog_path)
    sources = load_sources(sources_path)
    issues = collect_stale_citation_issues(documents, sources)
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "artifact_type": "stale_norm_citation_scan",
        "claim_level": CLAIM_LEVEL,
        "claim_boundary": CLAIM_BOUNDARY,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "machine": _machine_fingerprint(),
        "source": {
            "catalog": catalog_path.resolve().relative_to(root or repo_root()).as_posix()
            if catalog_path.is_absolute()
            else catalog_path.as_posix(),
            "sources": sources_path.resolve().relative_to(root or repo_root()).as_posix()
            if sources_path.is_absolute()
            else sources_path.as_posix(),
        },
        "summary": {
            "document_count": len(documents),
            "source_count": len(sources),
            "superseded_citation_warnings": len(issues),
            "rule_id": "AEROBIM-NORM-SUPERSEDED",
        },
        "issues": [
            {
                "rule_id": issue.rule_id,
                "severity": issue.severity.value,
                "source_id": issue.source_id,
                "observed_value": issue.observed_value,
                "expected_value": issue.expected_value,
                "message": issue.message,
            }
            for issue in issues
        ],
    }
    encoded = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    body["content_sha256"] = _sha256_bytes(encoded)
    return body


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        '<!-- claims-lint: allow-file reason="Stale-norm citation scan; not product accuracy" -->',
        "---",
        'title: "Stale norm citations (GOST R 21.101-2020 superseded)"',
        f"date: {str(payload.get('generated_at') or '')[:10]}",
        f"claim_level: {payload.get('claim_level')}",
        "claim_boundary: >-",
        f"  {payload.get('claim_boundary')}",
        "---",
        "",
        "# Stale norm citations",
        "",
        "A cited document that has been replaced raises `AEROBIM-NORM-SUPERSEDED` ",
        "(warning). Demo: Moscow CIM AGR requirements cite GOST R 21.101-2020 after ",
        "GOST R 21.101-2026 entered force on 2026-04-01 ",
        "(Rosstandart 129-st, 12.02.2026).",
        "",
        "## Measured",
        "",
        f"- catalog documents: **{summary.get('document_count')}**",
        f"- citing sources: **{summary.get('source_count')}**",
        f"- superseded-citation warnings: **{summary.get('superseded_citation_warnings')}**",
        f"- content_sha256: `{payload.get('content_sha256')}`",
        "",
        "## Issues",
        "",
    ]
    for issue in payload.get("issues") or []:
        if not isinstance(issue, dict):
            continue
        lines.append(
            f"- `{issue.get('source_id')}`: {issue.get('observed_value')} → "
            f"{issue.get('expected_value')}"
        )
    lines.extend(
        [
            "",
            "```bash",
            "cd backend",
            "python -m aerobim.tools.export_stale_norm_scan",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=None)
    parser.add_argument("--sources", type=Path, default=None)
    args = parser.parse_args(argv)
    root = repo_root()
    catalog = args.catalog or (root / "samples" / "config" / "norm-citation-catalog.json")
    sources = args.sources or (root / "samples" / "config" / "norm-citation-sources.json")
    payload = build_payload(catalog_path=catalog, sources_path=sources, root=root)
    artifacts = root / "artifacts" / "stale-norm-scan"
    artifacts.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    (artifacts / "stale-norm-scan.json").write_text(text, encoding="utf-8")
    evidence_json = root / "docs" / "evidence" / "stale-norm-scan-2026-08.json"
    evidence_md = root / "docs" / "evidence" / "stale-norm-scan-2026-08.md"
    evidence_json.write_text(text, encoding="utf-8")
    evidence_md.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
