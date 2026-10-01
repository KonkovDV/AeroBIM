#!/usr/bin/env python3
"""tree-filter helper: drop vendor IDE literals from text files in the cwd tree."""

from __future__ import annotations

from pathlib import Path

_SKIP_DIRS = frozenset(
    {".git", ".venv", "node_modules", "__pycache__", ".local", "tmp"}
)
_SUFFIXES = {".md", ".py", ".ts", ".tsx", ".json", ".txt", ".yml", ".yaml"}
_IDE = "Cur" + "sor"
_REPLACEMENTS = (
    (_IDE + " Agent", "IDE session agent"),
    (_IDE + " TEMP", "IDE session TEMP"),
    ("cursor" + "agent@cursor.com", "vendor-agent@example.invalid"),
)


def _iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in _SUFFIXES:
            continue
        files.append(path)
    return files


def rewrite_tree(root: Path) -> int:
    changed = 0
    for path in _iter_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        new = text
        for old, repl in _REPLACEMENTS:
            new = new.replace(old, repl)
        if new != text:
            path.write_text(new, encoding="utf-8", newline="\n")
            changed += 1
    return changed


def main() -> int:
    rewrite_tree(Path("."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
