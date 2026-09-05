"""Run pypdfium2 raster work in a child process (RT-C3PO-002).

A timeout still bounds a hung worker; isolation is the subprocess boundary,
not ThreadPoolExecutor around in-process PDFium.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

_DEFAULT_TIMEOUT_S = 30.0
_WORKER_MODULE = "aerobim.infrastructure.adapters.pdfium_isolate.render_worker"
# Address-space / process-memory cap for the isolate (Python + PDFium).
_POSIX_RLIMIT_AS_BYTES = 1024 * 1024 * 1024
_POSIX_RLIMIT_CPU_SECONDS = 30
_WINDOWS_JOB_MEMORY_BYTES = _POSIX_RLIMIT_AS_BYTES
_WINDOWS_JOB_CPU_100NS = _POSIX_RLIMIT_CPU_SECONDS * 10_000_000
_CREATE_BREAKAWAY_FROM_JOB = 0x01000000
# Win32 JobObject limit flags (PROC-01).
JOB_OBJECT_LIMIT_PROCESS_TIME = 0x00000002
JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
_LOGGER = logging.getLogger(__name__)


def _apply_posix_rlimits() -> None:
    """preexec_fn: bound AS + CPU in the child before exec."""

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


def _windows_job_create() -> Any | None:
    """Create a Job Object with 1 GiB process memory + 30s CPU (PROC-01)."""

    if sys.platform != "win32":
        return None
    try:
        import ctypes
        from ctypes import wintypes
    except ImportError:
        return None

    class _IoCounters(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_uint64),
            ("WriteOperationCount", ctypes.c_uint64),
            ("OtherOperationCount", ctypes.c_uint64),
            ("ReadTransferCount", ctypes.c_uint64),
            ("WriteTransferCount", ctypes.c_uint64),
            ("OtherTransferCount", ctypes.c_uint64),
        ]

    class _BasicLimitInformation(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_int64),
            ("PerJobUserTimeLimit", ctypes.c_int64),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class _ExtendedLimitInformation(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", _BasicLimitInformation),
            ("IoInfo", _IoCounters),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    job_object_extended_limit_information = 9

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.argtypes = [wintypes.LPVOID, wintypes.LPCWSTR]
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.SetInformationJobObject.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    ]
    kernel32.SetInformationJobObject.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    handle = kernel32.CreateJobObjectW(None, None)
    if not handle:
        _LOGGER.warning("pdfium isolate: CreateJobObjectW failed; timeout-only fallback")
        return None
    info = _ExtendedLimitInformation()
    info.BasicLimitInformation.LimitFlags = (
        JOB_OBJECT_LIMIT_PROCESS_TIME
        | JOB_OBJECT_LIMIT_PROCESS_MEMORY
        | JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    )
    info.BasicLimitInformation.PerProcessUserTimeLimit = _WINDOWS_JOB_CPU_100NS
    info.ProcessMemoryLimit = _WINDOWS_JOB_MEMORY_BYTES
    ok = kernel32.SetInformationJobObject(
        handle,
        job_object_extended_limit_information,
        ctypes.byref(info),
        ctypes.sizeof(info),
    )
    if not ok:
        kernel32.CloseHandle(handle)
        _LOGGER.warning("pdfium isolate: SetInformationJobObject failed; timeout-only fallback")
        return None
    return handle


def _windows_job_assign(job: Any, pid: int) -> bool:
    if sys.platform != "win32" or job is None:
        return False
    try:
        import ctypes
        from ctypes import wintypes
    except ImportError:
        return False

    process_set_quota = 0x0100
    process_terminate = 0x0001
    process_query_information = 0x0400
    synchronize = 0x00100000
    access = process_set_quota | process_terminate | process_query_information | synchronize

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    process = kernel32.OpenProcess(access, False, pid)
    if not process:
        return False
    try:
        return bool(kernel32.AssignProcessToJobObject(job, process))
    finally:
        kernel32.CloseHandle(process)


def _windows_job_close(job: Any) -> None:
    if sys.platform != "win32" or job is None:
        return
    try:
        import ctypes
        from ctypes import wintypes
    except ImportError:
        return
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.CloseHandle(job)


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
        argv = [
            sys.executable,
            "-m",
            _WORKER_MODULE,
            "--spec",
            str(spec_path),
            "--output",
            str(out_path),
        ]
        popen_kwargs: dict[str, Any] = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
        }
        job = None
        if sys.platform != "win32":
            popen_kwargs["preexec_fn"] = _apply_posix_rlimits
        else:
            job = _windows_job_create()

        try:
            try:
                if sys.platform == "win32":
                    proc = subprocess.Popen(  # noqa: S603 — argv is sys.executable + our module
                        argv,
                        creationflags=_CREATE_BREAKAWAY_FROM_JOB,
                        **popen_kwargs,
                    )
                else:
                    proc = subprocess.Popen(  # noqa: S603
                        argv,
                        **popen_kwargs,
                    )
            except OSError:
                if sys.platform != "win32":
                    raise
                proc = subprocess.Popen(argv, **popen_kwargs)  # noqa: S603
            if job is not None and not _windows_job_assign(job, proc.pid):
                _LOGGER.warning(
                    "pdfium isolate: AssignProcessToJobObject failed; timeout-only fallback"
                )
                _windows_job_close(job)
                job = None
            try:
                _stdout, stderr = proc.communicate(timeout=timeout_s)
            except subprocess.TimeoutExpired as exc:
                proc.kill()
                proc.communicate()
                raise RuntimeError(
                    f"pdfium isolated render timed out after {timeout_s:.0f}s"
                ) from exc
            returncode = 0 if proc.returncode is None else proc.returncode
        finally:
            _windows_job_close(job)

        err = (stderr or b"").decode("utf-8", errors="replace").strip()
        if returncode == 2:
            raise ValueError(err or "pdfium crop rejected")
        if returncode != 0:
            raise RuntimeError(f"pdfium isolated render failed (exit {returncode}): {err}")
        if not out_path.is_file():
            raise RuntimeError("pdfium isolated render produced no output")
        return out_path.read_bytes()


__all__ = ["run_pdfium_crop_isolated"]
