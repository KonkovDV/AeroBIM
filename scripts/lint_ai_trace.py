#!/usr/bin/env python3
"""AI-trace hygiene: fail on chat-fillers, tool fingerprints, agent meta-voice.

Placeholders (TODO/TBD/N/A) are inventory-only: honest matrix N/A and TZ TBD
fills are legitimate. Do not treat hyphenated ``-na-`` URL tokens as N/A.

Skip: .venv, node_modules, .local, RED_TEAM_*, errata, docs/ai prompts,
AI_TRACE_* reports (they name the scan patterns), this linter and its tests.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SKIP_DIR_PARTS = frozenset(
    {".git", ".venv", "node_modules", ".local", "__pycache__", "site-packages", "tmp"}
)
_SKIP_REL_FRAGMENTS = (
    "/docs/ai/",
    "RED_TEAM",
    "CITATION_ERRATA",
    "SOURCE_VERIFICATION_REPORT",
    "AI_TRACE_AUDIT",
    "AI_TRACE_RUN",
    "AECV_BASELINE_COMPARE",
    "lint_ai_trace.py",
    "test_lint_ai_trace.py",
)
_CHAT_FILLERS = (
    "Стоит отметить",
    "Важно отметить, что",
    "Certainly,",
    "Here is",
    "Подводя итог",
    "надеюсь, это помогает",
    "Let me know if",
    "Hope this helps",
    "Happy to help",
    "In this conversation",
)
# Space after the dash is normal Russian («Ты — научный…»).
_META_LINE_RE = re.compile(r"^(Ты —|You are )\s*\S")
_META_INLINE_RE = (
    re.compile(r"(?i)as an AI"),
    re.compile(r"(?i)I am an AI"),
    re.compile(r"(?i)as a language model"),
    # Do not match «Концепция — ассистент» (product heading; «я» is a suffix).
    re.compile(r"(?<![А-Яа-яЁё])я — ассистент"),
    re.compile(r"(?i)role:\s*system"),
)


def _tool_mark(*parts: str) -> str:
    """Build a scan needle without storing the vendor phrase in the tree."""
    return "".join(parts)


_TOOL_FINGERPRINTS = (
    _tool_mark("Cur", "sor Ag", "ent"),
    _tool_mark("Cur", "sor TE", "MP"),
)
_PLACEHOLDER_RE = re.compile(
    r"(?i)\bTODO\b|\bFIXME\b|\bTBD\b|\bN/A\b|\{journal\}|your_api_key|"
    r"\blorem ipsum\b|<placeholder>"
)


def _rel(path: Path, root: Path = _REPO) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _skip_rel(rel: str) -> bool:
    posix = "/" + rel.replace("\\", "/")
    if posix.startswith("/docs/ai/") or posix == "/docs/ai":
        return True
    return any(fragment in posix for fragment in _SKIP_REL_FRAGMENTS)


def _iter_source_files(root: Path) -> list[Path]:
    files: list[Path] = []
    scan_root = root.resolve()
    seen: set[Path] = set()
    for suffix in ("*.md", "*.py", "*.ts", "*.tsx"):
        for path in scan_root.rglob(suffix):
            if path in seen:
                continue
            seen.add(path)
            if any(part in _SKIP_DIR_PARTS for part in path.parts):
                continue
            rel = _rel(path, scan_root)
            if _skip_rel(rel):
                continue
            files.append(path)
    return files


def _iter_markdown(root: Path) -> list[Path]:
    return [path for path in _iter_source_files(root) if path.suffix.lower() == ".md"]


def lint_ai_trace_meta(*, root: Path = _REPO) -> list[str]:
    """Return violations for chat-fillers, tool fingerprints, and meta-voice."""
    hits: list[str] = []
    scan_root = root.resolve()
    for path in _iter_source_files(root):
        rel = _rel(path, scan_root)
        is_md = path.suffix.lower() == ".md"
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("```"):
                continue
            for mark in _TOOL_FINGERPRINTS:
                if mark in line:
                    hits.append(f"{rel}:{lineno}: [tool_fingerprint] {mark}")
            for meta_re in _META_INLINE_RE:
                if meta_re.search(line):
                    hits.append(f"{rel}:{lineno}: [meta_voice] {meta_re.pattern}")
            if not is_md:
                continue
            for filler in _CHAT_FILLERS:
                if filler in line:
                    hits.append(f"{rel}:{lineno}: [chat_filler] {filler}")
            if _META_LINE_RE.match(stripped):
                hits.append(f"{rel}:{lineno}: [meta_voice] prompt-line")
    return hits


def placeholder_hits(*, root: Path = _REPO) -> list[tuple[str, int, str]]:
    rows: list[tuple[str, int, str]] = []
    scan_root = root.resolve()
    for path in _iter_markdown(root):
        rel = _rel(path, scan_root)
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if _PLACEHOLDER_RE.search(line):
                rows.append((rel, lineno, line.strip()[:200]))
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inventory-placeholders",
        action="store_true",
        help="Print TODO/TBD/N/A inventory (does not fail)",
    )
    args = parser.parse_args(argv)
    hits = lint_ai_trace_meta()
    if args.inventory_placeholders:
        rows = placeholder_hits()
        print(f"placeholder inventory: {len(rows)} hit(s)")
        for rel, lineno, text in rows:
            print(f"  {rel}:{lineno}: {text}")
    if hits:
        print(f"ai-trace: {len(hits)} violation(s)", file=sys.stderr)
        for hit in hits:
            print(hit, file=sys.stderr)
        return 1
    print("ai-trace: OK (meta/chat/tool)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
