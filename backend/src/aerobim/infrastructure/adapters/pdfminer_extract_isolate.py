"""Isolated pdfminer.six text extract for drawing annotations.

Parent does not parse PDF in-process. Wall-clock timeout kills the worker.
"""

from __future__ import annotations

import json
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from aerobim.infrastructure.adapters.pdfium_isolate.process_isolate import run_isolated_argv

_WORKER_MODULE = "aerobim.infrastructure.adapters.pdfminer_extract_worker"
_DEFAULT_TIMEOUT_S = 30.0
_MAX_PDF_BYTES = 64 * 1024 * 1024


def run_pdfminer_extract_isolated(
    pdf_path: Path,
    sheet_id: str,
    *,
    timeout_s: float = _DEFAULT_TIMEOUT_S,
    max_pdf_bytes: int = _MAX_PDF_BYTES,
) -> list[dict[str, Any]]:
    """Extract drawing-annotation payloads in a child process.

    Raises ``TimeoutError`` when the worker exceeds ``timeout_s``. Raises
    ``RuntimeError`` on spawn/worker failure. Does not fall back to an
    in-process pdfminer parse.
    """

    outcome = run_pdfminer_extract_isolated_many(
        [(pdf_path, sheet_id)],
        timeout_s=timeout_s,
        max_pdf_bytes=max_pdf_bytes,
    )[0]
    if isinstance(outcome, BaseException):
        raise outcome
    return outcome


def run_pdfminer_extract_isolated_many(
    items: Sequence[tuple[Path, str]],
    *,
    timeout_s: float = _DEFAULT_TIMEOUT_S,
    max_pdf_bytes: int = _MAX_PDF_BYTES,
) -> list[list[dict[str, Any]] | BaseException]:
    """Extract many PDFs in one worker. The parent still does not parse them.

    One hung file stops the worker. Files already written stay. The timeout
    is ``timeout_s`` times the number of files sent to the worker.
    """

    results: list[list[dict[str, Any]] | BaseException] = [
        RuntimeError("PDF drawing analysis failed") for _ in items
    ]
    pending: list[tuple[int, Path, str]] = []
    for index, (pdf_path, sheet_id) in enumerate(items):
        resolved = pdf_path.resolve()
        try:
            size = resolved.stat().st_size
        except OSError as exc:
            results[index] = exc
            continue
        if size > max_pdf_bytes:
            results[index] = RuntimeError("PDF drawing rejected: oversized input")
            continue
        pending.append((index, resolved, sheet_id))
    if not pending:
        return results

    with tempfile.TemporaryDirectory() as tmp:
        spec_path = Path(tmp) / "spec.json"
        out_path = Path(tmp) / "annotations.jsonl"
        spec_path.write_text(
            json.dumps(
                {
                    "files": [
                        {"pdf": str(path), "sheet_id": sheet_id}
                        for _index, path, sheet_id in pending
                    ]
                }
            ),
            encoding="utf-8",
        )
        argv = [
            sys.executable,
            "-m",
            _WORKER_MODULE,
            "--spec",
            str(spec_path),
            "--output",
            str(out_path),
        ]
        timed_out = False
        returncode = 1
        try:
            returncode, _stderr = run_isolated_argv(
                argv,
                timeout_s=timeout_s * len(pending),
                timeout_message=f"PDF analysis timed out after {timeout_s:.0f}s",
            )
        except TimeoutError:
            timed_out = True
        seen: set[int] = set()
        for record in _read_jsonl(out_path):
            slot = record.get("index")
            if not isinstance(slot, int) or not 0 <= slot < len(pending):
                continue
            origin = pending[slot][0]
            seen.add(slot)
            annotations = record.get("annotations")
            if isinstance(annotations, list):
                results[origin] = annotations
            else:
                results[origin] = RuntimeError("PDF drawing analysis failed")
        for slot, (origin, _path, _sheet_id) in enumerate(pending):
            if slot in seen:
                continue
            if timed_out:
                results[origin] = TimeoutError(f"PDF analysis timed out after {timeout_s:.0f}s")
            elif returncode != 0:
                results[origin] = RuntimeError("PDF drawing analysis failed")
    return results


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            records.append(payload)
    return records


__all__ = ["run_pdfminer_extract_isolated", "run_pdfminer_extract_isolated_many"]
