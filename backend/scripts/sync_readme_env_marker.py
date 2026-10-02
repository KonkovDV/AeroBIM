#!/usr/bin/env python3
"""Sync README documented-env marker with settings.py AEROBIM_* reads."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "backend" / "src"))

from aerobim.tools.export_runtime_baseline import (  # noqa: E402
    _ENV_DOC_MARKER_BEGIN,
    _ENV_DOC_MARKER_END,
    _code_env_names,
    _documented_env_marker_names,
)


def _sync(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    begin = text.find(_ENV_DOC_MARKER_BEGIN)
    end = text.find(_ENV_DOC_MARKER_END, begin)
    if begin < 0 or end < 0:
        raise SystemExit(f"Missing env marker block in {path}")
    names = set(_documented_env_marker_names(text) or [])
    names.update(_code_env_names(_REPO))
    block = "\n".join(sorted(names)) + "\n"
    updated = (
        text[: begin + len(_ENV_DOC_MARKER_BEGIN)]
        + "\n"
        + block
        + text[end:]
    )
    path.write_text(updated, encoding="utf-8")


def main() -> None:
    for name in ("README.md", "README.ru.md"):
        _sync(_REPO / name)
    print("README env markers synced with settings.py")


if __name__ == "__main__":
    main()
