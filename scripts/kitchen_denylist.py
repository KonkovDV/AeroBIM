"""Kitchen denylist — tokens live outside git.

Publication gate is fail-closed: missing list, missing HMAC key, empty list,
or digest mismatch blocks the scan. Guard modules must not embed protected
literals. Hits report paths only, never the matching string.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import subprocess
from collections.abc import Iterable
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_PIN_PATH = _REPO / "audit" / "evidence" / "kitchen-denylist.pin.json"
_DEFAULT_LIST = _REPO / ".local" / "kitchen-denylist.txt"
_DEFAULT_KEY = _REPO / ".local" / "kitchen-hmac.key"

ENV_LIST_PATH = "AEROBIM_KITCHEN_DENYLIST_PATH"
ENV_HMAC_KEY = "AEROBIM_KITCHEN_HMAC_KEY"
ENV_HMAC_KEY_FILE = "AEROBIM_KITCHEN_HMAC_KEY_FILE"

SKIP_DIR_NAMES = frozenset(
    {
        ".git",
        "node_modules",
        "__pycache__",
        ".venv",
        ".venv-3.12",
        ".venv-313",
        ".venv-pilot",
        "artifacts",
        ".local",
        ".cursor",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".hypothesis",
        "htmlcov",
        "dist",
        "coverage",
        "var",
        "tmp",
    }
)

# Native authoring / solver / coordinator — never in the public tree,
# except the documented fake-byte DWG fixture (not a parser).
PACK_SUFFIXES = frozenset(
    {
        ".rvt",
        ".rfa",
        ".rte",
        ".nwd",
        ".nwc",
        ".lir",
        ".spr",
        ".dwg",
    }
)
PACK_SUFFIX_ALLOW = frozenset(
    {
        "samples/cad/placeholder-source.dwg",
    }
)
QUARANTINE_PREFIXES = (
    "files/",
    ".local/pack/",
)
# GitHub warns at 50 MiB; refuse tracked blobs at this size.
MAX_TRACKED_BYTES = 50 * 1024 * 1024
# Skip huge blobs when scanning text for tokens.
MAX_SCAN_BYTES = 2 * 1024 * 1024

GUARD_RELATIVE = (
    "scripts/lint_claims.py",
    "scripts/kitchen_denylist.py",
    "backend/tests/test_samolet_answers_2026_08_25.py",
    "backend/tests/test_kitchen_denylist_hygiene.py",
    "backend/tests/test_rt_customer_blocker_honesty_lock.py",
    "backend/src/aerobim/domain/live_tree_triage.py",
    "docs/quality/TZ_LIVE_TREE_TRIAGE_2026_08_27.md",
)


class KitchenDenylistError(RuntimeError):
    """Fail-closed publication gate."""


def repo_root() -> Path:
    return _REPO


def pin_path() -> Path:
    return _PIN_PATH


def denylist_path() -> Path:
    raw = os.environ.get(ENV_LIST_PATH, "").strip()
    if raw:
        return Path(raw)
    return _DEFAULT_LIST


def _hmac_key() -> str:
    env = os.environ.get(ENV_HMAC_KEY, "").strip()
    if env:
        return env
    key_file = os.environ.get(ENV_HMAC_KEY_FILE, "").strip()
    if key_file:
        path = Path(key_file)
        if path.is_file():
            return path.read_text(encoding="utf-8").strip()
    if _DEFAULT_KEY.is_file():
        return _DEFAULT_KEY.read_text(encoding="utf-8").strip()
    raise KitchenDenylistError("HMAC key missing")


def load_tokens() -> list[str]:
    path = denylist_path()
    if not path.is_file():
        raise KitchenDenylistError("denylist file missing")
    tokens: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        tokens.append(stripped)
    unique = sorted(set(tokens))
    if not unique:
        raise KitchenDenylistError("denylist empty")
    return unique


def hmac_digest(tokens: Iterable[str], key: str) -> str:
    payload = "\n".join(tokens).encode("utf-8")
    return hmac.new(key.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def load_pin() -> dict[str, object]:
    if not _PIN_PATH.is_file():
        raise KitchenDenylistError("denylist pin missing")
    payload = json.loads(_PIN_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise KitchenDenylistError("denylist pin is not an object")
    return payload


def verify_pin(tokens: list[str] | None = None) -> None:
    key = _hmac_key()
    pin = load_pin()
    loaded = tokens if tokens is not None else load_tokens()
    count = pin.get("token_count")
    digest = pin.get("hmac_sha256")
    if not isinstance(count, int) or not isinstance(digest, str):
        raise KitchenDenylistError("denylist pin fields missing")
    if len(loaded) != count:
        raise KitchenDenylistError(
            f"denylist count does not match pin (got {len(loaded)}, pin {count})"
        )
    actual = hmac_digest(loaded, key)
    if not hmac.compare_digest(actual, digest.lower()):
        raise KitchenDenylistError("denylist HMAC mismatch")


def _skip_dir(path: Path) -> bool:
    return any(part in SKIP_DIR_NAMES for part in path.parts)


def iter_tracked_files() -> Iterable[Path]:
    """Walk the published tree. A hand list of content roots is a class defect.

    Denylist loaders live under tools/tests, not under docs/src. Enumerating
    content directories therefore hides the next guard by construction.
    ``git ls-files`` is the published surface; skip dirs and quarantine
    prefixes are the only exclusions.
    """

    proc = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=_REPO,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise KitchenDenylistError("git ls-files failed")
    skip_resolved = {denylist_path().resolve(), _DEFAULT_KEY.resolve()}
    key_file = os.environ.get(ENV_HMAC_KEY_FILE, "").strip()
    if key_file:
        skip_resolved.add(Path(key_file).resolve())
    for raw in proc.stdout.split(b"\0"):
        if not raw:
            continue
        rel = raw.decode("utf-8", "replace").replace("\\", "/")
        if any(rel.startswith(prefix) for prefix in QUARANTINE_PREFIXES):
            continue
        path = _REPO / rel
        if not path.is_file():
            continue
        if _skip_dir(path):
            continue
        try:
            if path.resolve() in skip_resolved:
                continue
        except OSError:
            continue
        yield path


def lint_kitchen_tokens() -> list[str]:
    """Scan tracked files for denylist literals. Fail-closed on load errors."""

    try:
        tokens = load_tokens()
        verify_pin(tokens)
    except KitchenDenylistError as exc:
        return [f"[kitchen_denylist] fail-closed: {exc}"]

    hits: list[str] = []
    for path in iter_tracked_files():
        try:
            if path.stat().st_size > MAX_SCAN_BYTES:
                continue
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if any(token in text for token in tokens):
            rel = path.relative_to(_REPO).as_posix()
            hits.append(f"[kitchen_token] {rel}")
    return hits


def lint_guard_files_have_no_literals() -> list[str]:
    """Invariant: guard modules do not embed denylist literals."""

    try:
        tokens = load_tokens()
        verify_pin(tokens)
    except KitchenDenylistError as exc:
        return [f"[kitchen_denylist] fail-closed: {exc}"]

    hits: list[str] = []
    for rel in GUARD_RELATIVE:
        path = _REPO / rel
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if any(token in text for token in tokens):
            hits.append(f"[kitchen_guard] {rel}")
    return hits


def lint_pack_quarantine() -> list[str]:
    """Tracked pack extensions, quarantine prefixes, and oversized blobs."""

    proc = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=_REPO,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return [f"[pack_quarantine] git ls-files failed: {proc.returncode}"]
    hits: list[str] = []
    for raw in proc.stdout.split(b"\0"):
        if not raw:
            continue
        rel = raw.decode("utf-8", "replace").replace("\\", "/")
        lowered = rel.lower()
        suffix = Path(lowered).suffix
        if suffix in PACK_SUFFIXES and rel not in PACK_SUFFIX_ALLOW:
            hits.append(f"[pack_quarantine] tracked pack suffix: {rel}")
            continue
        if any(rel.startswith(prefix) for prefix in QUARANTINE_PREFIXES):
            hits.append(f"[pack_quarantine] tracked quarantine path: {rel}")
            continue
        path = _REPO / rel
        try:
            if path.is_file() and path.stat().st_size > MAX_TRACKED_BYTES:
                hits.append(f"[pack_quarantine] tracked file exceeds size cap: {rel}")
        except OSError:
            continue
    return hits
