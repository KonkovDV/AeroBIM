"""Isolated pdfminer.six text extract for drawing annotations.

Parent does not parse PDF in-process. Wall-clock timeout kills the worker.
"""

from __future__ import annotations

import json
import logging
import sys
import tempfile
from pathlib import Path
from typing import Any

from aerobim.infrastructure.adapters.pdfium_isolate.process_isolate import run_isolated_argv

_WORKER_MODULE = "aerobim.infrastructure.adapters.pdfminer_extract_worker"
_LOGGER = logging.getLogger(__name__)
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

    resolved = pdf_path.resolve()
    size = resolved.stat().st_size
    if size > max_pdf_bytes:
        raise RuntimeError("PDF drawing rejected: oversized input")

    with tempfile.TemporaryDirectory() as tmp:
        spec_path = Path(tmp) / "spec.json"
        out_path = Path(tmp) / "annotations.json"
        spec_path.write_text(
            json.dumps({"pdf": str(resolved), "sheet_id": sheet_id}),
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
        returncode, _stderr = run_isolated_argv(
            argv,
            timeout_s=timeout_s,
            timeout_message=f"PDF analysis timed out after {timeout_s:.0f}s",
        )
        if returncode != 0:
            _LOGGER.warning("pdfminer isolate failed", extra={"exit": returncode})
            raise RuntimeError("PDF drawing analysis failed")
        if not out_path.is_file():
            raise RuntimeError("PDF drawing analysis produced no output")
        payload = json.loads(out_path.read_text(encoding="utf-8"))
        annotations = payload.get("annotations") if isinstance(payload, dict) else None
        if not isinstance(annotations, list):
            raise RuntimeError("PDF drawing analysis produced invalid output")
        return annotations


__all__ = ["run_pdfminer_extract_isolated"]
