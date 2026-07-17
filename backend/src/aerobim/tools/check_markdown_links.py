"""CI markdown link checker — fail on dead relative links in docs/ + README*.md."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
_SKIP_SCHEMES = ("http://", "https://", "mailto:", "#")
# Cursor/chat transcript IDs used as markdown targets are not filesystem paths.
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _iter_markdown(root: Path) -> list[Path]:
    files: list[Path] = []
    for pattern in ("README.md", "README.ru.md", "docs/**/*.md", "audit/reports/*.md"):
        files.extend(root.glob(pattern))
    # De-dupe while preserving order
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in files:
        resolved = path.resolve()
        if resolved in seen or not path.is_file():
            continue
        seen.add(resolved)
        unique.append(path)
    return unique


def check_links(root: Path) -> list[str]:
    errors: list[str] = []
    for md_path in _iter_markdown(root):
        text = md_path.read_text(encoding="utf-8")
        for match in _LINK_RE.finditer(text):
            target = match.group(2).strip()
            if not target or target.startswith(_SKIP_SCHEMES):
                continue
            # Strip anchors and query
            path_part = target.split("#", 1)[0].split("?", 1)[0]
            if not path_part or _UUID_RE.fullmatch(path_part):
                continue
            candidate = (md_path.parent / path_part).resolve()
            if not candidate.exists():
                errors.append(f"{md_path.as_posix()}: broken link -> {target}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
        help="Repository root (default: AeroBIM/)",
    )
    args = parser.parse_args(argv)
    errors = check_links(args.root)
    if errors:
        print(f"Found {len(errors)} broken markdown link(s):")
        for error in errors[:50]:
            print(f"  - {error}")
        if len(errors) > 50:
            print(f"  ... and {len(errors) - 50} more")
        return 1
    print("Markdown link check OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
