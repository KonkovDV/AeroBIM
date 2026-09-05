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
# Address-space cap for the POSIX isolate (Python + PDFium). Windows has no RLIMIT_AS.
_POSIX_RLIMIT_AS_BYTES = 1024 * 1024 * 1024
_POSIX_RLIMIT_CPU_SECONDS = 30


def _apply_posix_rlimits() -> None:
    """preexec_fn: bound AS + CPU in the child before exec (PROC-01)."""

    if sys.platform == "win32":
        return
    try:
        import resource
    except ImportError:
        return
    setrlimit = getattr(resource, "setrlimit", None)
    as_lim = getattr(resource, "RLIMIT_AS", None)
    cpu_lim = getattr(resource, "RLIMIT_CPU", None)
    if setrlimit is None or as_lim is None or cpu_lim is None:
        return
    try:
        setrlimit(as_lim, (_POSIX_RLIMIT_AS_BYTES, _POSIX_RLIMIT_AS_BYTES))
        setrlimit(cpu_lim, (_POSIX_RLIMIT_CPU_SECONDS, _POSIX_RLIMIT_CPU_SECONDS))
    except (OSError, ValueError):
        return


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
        run_kwargs: dict[str, Any] = {
            "capture_output": True,
            "timeout": timeout_s,
            "check": False,
        }
        if sys.platform != "win32":
            run_kwargs["preexec_fn"] = _apply_posix_rlimits
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
                **run_kwargs,
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
