#!/usr/bin/env python3
"""Operator NDA gate: scan tracked files for patterns in an untracked local file.

Patterns live in ``.nda/gate-patterns.local`` (gitignored). This module never
embeds protected literals. Hits report relative paths only, never the match.
Jury clones without the file skip the scan (exit 0).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_DEFAULT_PATTERNS = _REPO / ".nda" / "gate-patterns.local"
ALLOW_PREFIXES = ("samples/xsd/minstroy/",)
SKIP_DIR_NAMES = frozenset(
    {
        ".git",
        "node_modules",
        "__pycache__",
        ".venv",
        ".local",
        "out",
        ".nda",
        "artifacts",
        "var",
        "tmp",
    }
)
MAX_SCAN_BYTES = 2 * 1024 * 1024


class NdaGateError(RuntimeError):
    """Fail-closed when the operator pattern file is present but unreadable."""


def repo_root() -> Path:
    return _REPO


def patterns_path() -> Path:
    return _DEFAULT_PATTERNS


def load_patterns(path: Path | None = None) -> list[str] | None:
    """Return patterns, or None when the operator file is absent."""

    target = path or _DEFAULT_PATTERNS
    if not target.is_file():
        return None
    try:
        text = target.read_text(encoding="utf-8")
    except OSError as exc:
        raise NdaGateError(f"cannot read gate patterns: {exc}") from exc
    tokens: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        tokens.append(stripped)
    unique = sorted(set(tokens), key=str.casefold)
    if not unique:
        raise NdaGateError("gate patterns file is empty")
    return unique


def _encoded(tokens: Sequence[str]) -> tuple[bytes, ...]:
    return tuple(token.encode("utf-8") for token in tokens)


def bytes_contain_tokens(blob: bytes, encoded: Sequence[bytes]) -> bool:
    lowered = blob.lower()
    return any(token.lower() in lowered for token in encoded)


def file_contains_tokens(path: Path, encoded: Sequence[bytes]) -> bool:
    overlap = max((len(item) for item in encoded), default=64)
    overlap = max(overlap, 64)
    previous = b""
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(MAX_SCAN_BYTES)
            if not chunk:
                break
            window = previous + chunk
            if bytes_contain_tokens(window, encoded):
                return True
            previous = chunk[-overlap:] if len(chunk) >= overlap else chunk
    return False


def iter_tracked_files(repo: Path | None = None) -> Iterable[Path]:
    root = repo or _REPO
    proc = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise NdaGateError("git ls-files failed")
    for raw in proc.stdout.split(b"\0"):
        if not raw:
            continue
        rel = raw.decode("utf-8", "replace").replace("\\", "/")
        if any(rel.startswith(prefix) for prefix in ALLOW_PREFIXES):
            continue
        if any(part in SKIP_DIR_NAMES for part in Path(rel).parts):
            continue
        path = root / rel
        if path.is_file():
            yield path


def iter_scan_root(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_file():
            yield path


def scan_tracked(
    *,
    repo: Path | None = None,
    patterns: Sequence[str],
    scan_root: Path | None = None,
) -> list[str]:
    """Return relative paths that contain a pattern. Never include the match."""

    root = (scan_root or repo or _REPO).resolve()
    encoded = _encoded(patterns)
    walker = iter_scan_root(root) if scan_root is not None else iter_tracked_files(root)
    hits: list[str] = []
    scanned = 0
    for path in walker:
        scanned += 1
        try:
            if file_contains_tokens(path, encoded):
                hits.append(path.relative_to(root).as_posix())
        except OSError:
            continue
    hits.append(f"__scanned__={scanned}")
    return hits


def format_report(hits: list[str]) -> tuple[int, int, list[str]]:
    scanned = 0
    paths = [item for item in hits if not item.startswith("__scanned__=")]
    for item in hits:
        if item.startswith("__scanned__="):
            scanned = int(item.split("=", 1)[1])
    return scanned, len(paths), paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--patterns",
        type=Path,
        default=None,
        help="Override .nda/gate-patterns.local (tests only)",
    )
    parser.add_argument(
        "--require-file",
        action="store_true",
        help="Fail if the operator pattern file is missing",
    )
    parser.add_argument(
        "--scan-root",
        type=Path,
        default=None,
        help="Scan a directory instead of git ls-files (self-test)",
    )
    args = parser.parse_args(argv)
    try:
        tokens = load_patterns(args.patterns)
    except NdaGateError as exc:
        print(f"FAIL nda gate: {exc}", file=sys.stderr)
        return 1
    if tokens is None:
        if args.require_file:
            print("FAIL nda gate: .nda/gate-patterns.local missing", file=sys.stderr)
            return 1
        print("skip nda gate (no .nda/gate-patterns.local; operator-only)")
        return 0
    hits = scan_tracked(patterns=tokens, scan_root=args.scan_root)
    scanned, count, paths = format_report(hits)
    print(f"nda gate: files_scanned={scanned} hits={count} patterns={len(tokens)}")
    if paths:
        for rel in paths:
            print(rel)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
