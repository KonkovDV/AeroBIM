"""Run pypdfium2 raster work in a child process (RT-C3PO-002).

A timeout still bounds a hung worker; isolation is the subprocess boundary,
not ThreadPoolExecutor around in-process PDFium.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

_DEFAULT_TIMEOUT_S = 30.0
_WORKER_MODULE = "aerobim.infrastructure.adapters.pdfium_isolate.render_worker"


def run_pdfium_crop_isolated(
    spec: dict[str, Any],
    *,
    timeout_s: float = _DEFAULT_TIMEOUT_S,
) -> bytes:
    """Crop a PDF region in a worker process. Parent does not import pypdfium2."""

    with tempfile.TemporaryDirectory() as tmp:
        spec_path = Path(tmp) / "spec.json"
        out_path = Path(tmp) / "out.png"
        spec_path.write_text(json.dumps(spec), encoding="utf-8")
        try:
            completed = subprocess.run(  # noqa: S603 — argv is sys.executable + our module
                [
                    sys.executable,
                    "-m",
                    _WORKER_MODULE,
                    "--spec",
                    str(spec_path),
                    "--output",
                    str(out_path),
                ],
                capture_output=True,
                timeout=timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"pdfium isolated render timed out after {timeout_s:.0f}s") from exc
        err = (completed.stderr or b"").decode("utf-8", errors="replace").strip()
        if completed.returncode == 2:
            raise ValueError(err or "pdfium crop rejected")
        if completed.returncode != 0:
            raise RuntimeError(
                f"pdfium isolated render failed (exit {completed.returncode}): {err}"
            )
        if not out_path.is_file():
            raise RuntimeError("pdfium isolated render produced no output")
        return out_path.read_bytes()


__all__ = ["run_pdfium_crop_isolated"]
