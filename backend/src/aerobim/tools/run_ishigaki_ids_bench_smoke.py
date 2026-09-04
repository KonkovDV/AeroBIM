"""Ishigaki-IDS-Bench gold-IDS document audit (no IFC, no LLM F1).

World practice (arXiv:2605.22079, HF ONESTRUCTION/Ishigaki-IDS-Bench, CC BY 4.0):
processability of gold IDS documents. The upstream set has **no real IFC**.
HF ships ``data/test.jsonl`` (166 rows, assistant = gold IDS XML), not a folder
of ``*.ids``. This smoke extracts that XML and audits it. It never reports
generation F1 as AeroBIM product accuracy.

Local files stay under ``.local/ishigaki-ids-bench`` (gitignored). Absent pack →
``SKIPPED``. DrawingVQA stays link-only (drawings not public; questions BY-NC-SA).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.models import Severity
from aerobim.infrastructure.adapters.xml_ids_document_auditor import XmlIdsDocumentAuditor

CLAIM_BOUNDARY = (
    "Ishigaki-IDS-Bench gold IDS document audit only (CC BY 4.0). No IFC in the "
    "upstream set. Not LLM generation F1. Not product accuracy. Does not close "
    "RT-001. Checkpoint GO (regulatory_measurement_mvp; customer_go false)."
)
ENV_ROOT = "AEROBIM_ISHIGAKI_IDS_ROOT"
DEFAULT_REL = Path(".local") / "ishigaki-ids-bench"
HF_JSONL_REL = Path("data") / "test.jsonl"
EXTRACT_REL = Path("extracted-gold-ids")
MAX_JSONL_BYTES = 5_000_000
MAX_XML_BYTES = 512_000
MAX_ROWS = 500
_ID_SAFE_RE = re.compile(r"[^A-Za-z0-9._-]+")
_FENCE_RE = re.compile(r"^```(?:xml)?\s*|\s*```$", re.IGNORECASE)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def default_dataset_root(root: Path | None = None) -> Path:
    env = (os.getenv(ENV_ROOT) or "").strip()
    if env:
        return Path(env)
    return (root or repo_root()) / DEFAULT_REL


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _repo_relative_or_redact(path: Path, *, repo: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except (OSError, ValueError):
        return "<redacted>"


def _safe_row_id(value: str, *, fallback: str) -> str:
    cleaned = _ID_SAFE_RE.sub("-", (value or "").strip()).strip(".-")
    return cleaned or fallback


def _xml_from_assistant(content: str) -> str:
    text = (content or "").strip()
    if text.startswith("```"):
        text = _FENCE_RE.sub("", text).strip()
    return text


def extract_gold_ids_from_jsonl(jsonl: Path, dest: Path) -> dict[str, Any]:
    """Write gold IDS XML from HF ``test.jsonl`` assistant turns into ``dest``."""
    size = jsonl.stat().st_size
    if size > MAX_JSONL_BYTES:
        raise ValueError(f"Ishigaki JSONL exceeds {MAX_JSONL_BYTES} bytes ({size})")
    dest.mkdir(parents=True, exist_ok=True)
    for old in dest.glob("*.ids"):
        old.unlink()
    paths: list[Path] = []
    skipped_rows = 0
    seen: set[str] = set()
    for index, line in enumerate(jsonl.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        if index > MAX_ROWS:
            raise ValueError(f"Ishigaki JSONL exceeds {MAX_ROWS} rows")
        row = json.loads(line)
        if not isinstance(row, dict):
            skipped_rows += 1
            continue
        row_id = _safe_row_id(str(row.get("id") or ""), fallback=f"row-{index:04d}")
        if row_id in seen:
            row_id = f"{row_id}-{index:04d}"
        seen.add(row_id)
        messages = row.get("messages") or []
        assistant = ""
        if isinstance(messages, list):
            for message in messages:
                if isinstance(message, dict) and message.get("role") == "assistant":
                    assistant = str(message.get("content") or "")
        xml = _xml_from_assistant(assistant)
        if "<ids" not in xml.lower() and "informationsdeliveryspecification" not in xml.lower():
            skipped_rows += 1
            continue
        encoded = xml.encode("utf-8")
        if len(encoded) > MAX_XML_BYTES:
            skipped_rows += 1
            continue
        out = dest / f"{row_id}.ids"
        out.write_bytes(encoded)
        paths.append(out)
    return {
        "jsonl_sha256": _sha256_file(jsonl),
        "jsonl_bytes": size,
        "extracted": len(paths),
        "skipped_rows": skipped_rows,
        "paths": paths,
    }


def skipped_payload(*, reason: str, dataset_root: str) -> dict[str, Any]:
    body: dict[str, Any] = {
        "artifact_type": "ishigaki_ids_bench_smoke",
        "schema_version": "1.1.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "claim_level": "open_bench_only",
        "claim_boundary": CLAIM_BOUNDARY,
        "status": "SKIPPED",
        "reason": reason,
        "dataset_root": dataset_root,
        "citation": {
            "arxiv": "2605.22079",
            "huggingface": "ONESTRUCTION/Ishigaki-IDS-Bench",
            "license": "CC BY 4.0",
            "gold_ids_published": 166,
            "real_ifc": False,
        },
        "closes_rt001": False,
        "checkpoint": CHECKPOINT,
        "summary": {
            "ids_files": 0,
            "audited": 0,
            "error_files": 0,
            "warning_files": 0,
        },
        "note": (
            "Hunt-only until a local CC BY 4.0 checkout exists. "
            "HF layout is data/test.jsonl (gold XML in assistant turns), not a "
            "folder of *.ids. Do not vendor DrawingVQA (BY-NC-SA; drawings not public)."
        ),
    }
    encoded = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    body["content_sha256"] = _sha256_bytes(encoded)
    return body


def _audit_ids_files(
    ids_files: list[Path],
    *,
    dataset_root: Path,
    repo: Path,
    auditor: XmlIdsDocumentAuditor | None,
    source: dict[str, Any],
) -> dict[str, Any]:
    checker = auditor or XmlIdsDocumentAuditor()
    rows: list[dict[str, Any]] = []
    error_files = 0
    warning_files = 0
    for path in ids_files:
        issues = checker.audit(path)
        error_n = sum(1 for issue in issues if issue.severity == Severity.ERROR)
        warn_n = sum(1 for issue in issues if issue.severity == Severity.WARNING)
        if error_n:
            error_files += 1
        elif warn_n:
            warning_files += 1
        try:
            rel = path.relative_to(dataset_root).as_posix()
        except ValueError:
            rel = path.name
        rows.append(
            {
                "path": rel,
                "issue_count": len(issues),
                "error_count": error_n,
                "warning_count": warn_n,
            }
        )
    body: dict[str, Any] = {
        "artifact_type": "ishigaki_ids_bench_smoke",
        "schema_version": "1.1.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "claim_level": "open_bench_only",
        "claim_boundary": CLAIM_BOUNDARY,
        "status": "EXECUTED",
        "dataset_root": _repo_relative_or_redact(dataset_root, repo=repo),
        "source": source,
        "citation": {
            "arxiv": "2605.22079",
            "huggingface": "ONESTRUCTION/Ishigaki-IDS-Bench",
            "license": "CC BY 4.0",
            "gold_ids_published": 166,
            "real_ifc": False,
        },
        "closes_rt001": False,
        "checkpoint": CHECKPOINT,
        "summary": {
            "ids_files": len(ids_files),
            "audited": len(rows),
            "error_files": error_files,
            "warning_files": warning_files,
            "clean_files": len(rows) - error_files - warning_files,
        },
        "files": rows,
        "note": (
            "Document processability of published gold IDS XML. Upstream has no "
            "real IFC. Not LLM IDS-generation F1 and not product accuracy."
        ),
    }
    encoded = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    body["content_sha256"] = _sha256_bytes(encoded)
    return body


def audit_gold_ids(
    dataset_root: Path,
    *,
    repo: Path,
    auditor: XmlIdsDocumentAuditor | None = None,
) -> dict[str, Any]:
    jsonl = dataset_root / HF_JSONL_REL
    if jsonl.is_file():
        extracted = extract_gold_ids_from_jsonl(jsonl, dataset_root / EXTRACT_REL)
        paths = list(extracted.pop("paths"))
        if not paths:
            return skipped_payload(
                reason="HF test.jsonl present but no gold IDS XML could be extracted",
                dataset_root=_repo_relative_or_redact(dataset_root, repo=repo),
            )
        source = {
            "kind": "hf_test_jsonl",
            "jsonl": HF_JSONL_REL.as_posix(),
            "jsonl_sha256": extracted["jsonl_sha256"],
            "jsonl_bytes": extracted["jsonl_bytes"],
            "extracted": extracted["extracted"],
            "skipped_rows": extracted["skipped_rows"],
        }
        return _audit_ids_files(
            paths,
            dataset_root=dataset_root,
            repo=repo,
            auditor=auditor,
            source=source,
        )

    ids_files = sorted(
        path for path in dataset_root.rglob("*.ids") if path.is_file() and path.name != "_probe.ids"
    )
    if not ids_files:
        return skipped_payload(
            reason=(
                "No data/test.jsonl and no *.ids under the Ishigaki checkout "
                "(gold IDS not unpacked)"
            ),
            dataset_root=_repo_relative_or_redact(dataset_root, repo=repo),
        )
    return _audit_ids_files(
        ids_files,
        dataset_root=dataset_root,
        repo=repo,
        auditor=auditor,
        source={"kind": "loose_ids"},
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--also-docs-evidence", action="store_true")
    args = parser.parse_args(argv)

    root = repo_root()
    dataset_root = (args.dataset_root or default_dataset_root(root)).resolve()
    if not dataset_root.is_dir():
        payload = skipped_payload(
            reason=(
                "Ishigaki-IDS-Bench checkout missing under .local/ishigaki-ids-bench. "
                "HF ONESTRUCTION/Ishigaki-IDS-Bench is CC BY 4.0; place data/test.jsonl "
                "locally before auditing. Do not treat this SKIPPED as a 166/166 score."
            ),
            dataset_root=DEFAULT_REL.as_posix(),
        )
    else:
        payload = audit_gold_ids(dataset_root, repo=root)

    out = args.output or (root / "artifacts" / "open-bench" / "ishigaki-ids-bench-smoke.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    out.write_text(text, encoding="utf-8")
    if args.also_docs_evidence:
        evidence = root / "docs" / "evidence" / "ishigaki-ids-bench-smoke-latest.json"
        evidence.write_text(text, encoding="utf-8")
        print(f"docs_evidence={evidence}")
    print(
        json.dumps(
            {
                "status": payload.get("status"),
                "summary": payload.get("summary"),
                "source": payload.get("source"),
                "output": str(out),
                "claim_level": "open_bench_only",
                "checkpoint": CHECKPOINT,
            }
        )
    )
    return 0 if payload.get("status") in {"SKIPPED", "EXECUTED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
