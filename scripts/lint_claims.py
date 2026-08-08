#!/usr/bin/env python3
"""Claims Lock linter (WP-R10) — executable honesty gate for AeroBIM.

Rules source: docs/capability-claim-matrix-2026.md (forbidden table) + TZ matrix guard.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_MATRIX = _REPO / "docs" / "capability-claim-matrix-2026.md"
_TZ_MATRIX = _REPO / "docs" / "tz" / "TZ_COMPLIANCE_MATRIX_2026.md"

_SCAN_ROOTS = (
    _REPO / "README.md",
    _REPO / "README.ru.md",
    _REPO / "frontend" / "src",
)

_EXCLUDE_SUFFIXES = {".min.js"}
_EXCLUDE_PATH_FRAGMENTS = (
    "capability-claim-matrix-2026.md",
    "CLAIMS_LOCK",
    "pilot-claim-boundary",
    "CRITICAL_BLOCKERS.md",
    "RED_TEAM",
    "runtime-baseline-latest.json",
)

_ALLOW_RE = re.compile(
    r"claims-lint:\s*allow\s+reason=(?P<q>\"[^\"]+\"|'[^']+')",
    re.IGNORECASE,
)

# High-signal patterns (RU + EN) — matrix-derived phrases appended at runtime.
_BUILTIN_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("forbidden_accuracy_gt_90", re.compile(r"(?i)(более\s+90|>\s*90\s*%|accuracy.{0,20}9[0-9]\s*%)")),
    ("forbidden_sla_30min", re.compile(r"(?i)(до\s*30\s*мин|≤\s*30\s*(мин|minutes)|30\s*min(ute)?s?\s+SLA)")),
    ("forbidden_production_ready", re.compile(r"(?i)production[-\s]?ready")),
    ("forbidden_external_audit", re.compile(r"(?i)(внешн(ий|его)\s+аудит|external\s+academic\s+audit)")),
    ("forbidden_native_dwg", re.compile(r"(?i)(native\s+DWG|нативн\w*\s+DWG|DWG\s+поддерж)")),
    ("forbidden_cde_ready", re.compile(r"(?i)(CDE[-\s]?ready|готов\w*\s+к\s+CDE)")),
    ("forbidden_sso_ready", re.compile(r"(?i)(SSO\s+ready|OIDC\s+BFF\s+ready)")),
    ("forbidden_ukep_verified", re.compile(r"(?i)(УКЭП\s+проверен|trust\s+chain\s+verified)")),
    ("forbidden_whole_mit", re.compile(r"(?i)(весь\s+продукт.{0,20}MIT|entire\s+product.{0,20}MIT)")),
    ("forbidden_aecv_customer", re.compile(r"(?i)AECV.{0,40}(customer|заказчик|точност)")),
    ("forbidden_open_corpus_accuracy", re.compile(r"(?i)(open[-\s]?corpus.{0,30}точност|BSI.{0,20}product\s+accuracy)")),
]


def _repo_root() -> Path:
    return _REPO


def _load_forbidden_claim_phrases(matrix_path: Path) -> list[str]:
    if not matrix_path.is_file():
        return []
    text = matrix_path.read_text(encoding="utf-8")
    marker = "## Forbidden until customer evidence"
    start = text.find(marker)
    if start < 0:
        return []
    block = text[start:]
    end = block.find("\n## ", len(marker))
    if end >= 0:
        block = block[:end]
    phrases: list[str] = []
    for line in block.splitlines():
        if not line.startswith("|") or line.count("|") < 3:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not cells or cells[0].lower() in {"claim", "---"}:
            continue
        claim = cells[0]
        if len(claim) >= 8:
            phrases.append(claim)
    return phrases


def _patterns_from_matrix(matrix_path: Path) -> list[tuple[str, re.Pattern[str]]]:
    patterns = list(_BUILTIN_PATTERNS)
    for phrase in _load_forbidden_claim_phrases(matrix_path):
        token = re.sub(r"[^\wа-яА-ЯёЁ%]+", r".{0,12}", re.escape(phrase)[:80])
        if len(token) < 8:
            continue
        patterns.append((f"matrix:{phrase[:48]}", re.compile(token, re.IGNORECASE)))
    return patterns


def _iter_scan_files() -> list[Path]:
    files: list[Path] = []
    for root in _SCAN_ROOTS:
        if root.is_file():
            files.append(root)
            continue
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".md", ".tsx", ".ts", ".jsx", ".js", ".html", ".json"}:
                continue
            if any(part in {".git", "node_modules", "__pycache__"} for part in path.parts):
                continue
            files.append(path)
    return sorted(set(files))


def _should_scan(path: Path) -> bool:
    if path.suffix.lower() in _EXCLUDE_SUFFIXES:
        return False
    try:
        rel = path.relative_to(_repo_root()).as_posix()
    except ValueError:
        return True
    return not any(fragment in rel for fragment in _EXCLUDE_PATH_FRAGMENTS)


def _line_is_documented_forbidden_context(line: str) -> bool:
    lower = line.lower()
    hints = (
        "claims lock",
        "blocked",
        "not claim",
        "do not",
        "never ",
        "никогда",
        "запрещено",
        "forbidden",
        "не заяв",
        "не native",
        "not implemented",
        "no native",
        "not a ",
        "not pp",
        "нельзя",
        "≠",
        "not verified",
        "не доказано",
        "missing",
        "no_go",
        "disclosure",
        "не product accuracy",
    )
    return any(hint in lower for hint in hints)


def _line_allowed(line: str) -> bool:
    return _ALLOW_RE.search(line) is not None


def lint_claims(
    *,
    matrix_path: Path,
    roots: list[Path] | None = None,
) -> list[str]:
    patterns = _patterns_from_matrix(matrix_path)
    violations: list[str] = []
    files = []
    if roots:
        for root in roots:
            if root.is_file():
                files.append(root)
            elif root.is_dir():
                files.extend(p for p in root.rglob("*") if p.is_file())
    else:
        files = _iter_scan_files()

    for path in sorted(set(files)):
        if not _should_scan(path):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        try:
            rel = path.relative_to(_repo_root()).as_posix()
        except ValueError:
            rel = path.as_posix()
        for lineno, line in enumerate(text.splitlines(), start=1):
            if _line_allowed(line) or _line_is_documented_forbidden_context(line):
                continue
            for rule_id, pattern in patterns:
                if pattern.search(line):
                    violations.append(f"{rel}:{lineno}: [{rule_id}] {line.strip()[:160]}")
    return violations


_SAMOLET_BLOCKED_KEYWORDS = (
    "customer corpus",
    "approved norm pack",
    "mep federated",
    "cde bcf",
    "dual adjudication",
    "rt-001",
    "rt-002",
    "rt-003",
)


def matrix_guard(tz_matrix_path: Path) -> list[str]:
    if not tz_matrix_path.is_file():
        return [f"Missing TZ matrix: {tz_matrix_path.as_posix()}"]
    violations: list[str] = []
    for lineno, line in enumerate(tz_matrix_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.startswith("|"):
            continue
        lower = line.lower()
        if "| done |" not in lower and "| done" not in lower.split("|")[-2:]:
            continue
        if any(keyword in lower for keyword in _SAMOLET_BLOCKED_KEYWORDS):
            rel = tz_matrix_path.as_posix()
            try:
                rel = tz_matrix_path.relative_to(_repo_root()).as_posix()
            except ValueError:
                pass
            violations.append(f"{rel}:{lineno}: Samolet-blocked row marked done: {line.strip()}")
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--full-docs",
        action="store_true",
        help="Also scan docs/** (honesty docs may need allowlist lines)",
    )
    parser.add_argument(
        "--matrix-guard",
        action="store_true",
        help="Verify TZ compliance matrix: Samolet-blocked rows are not marked done",
    )
    parser.add_argument(
        "--matrix",
        type=Path,
        default=_MATRIX,
        help="Capability claim matrix path (rules source)",
    )
    parser.add_argument(
        "--tz-matrix",
        type=Path,
        default=_TZ_MATRIX,
        help="TZ compliance matrix path (matrix-guard source)",
    )
    args = parser.parse_args(argv)

    errors: list[str] = []
    if args.matrix_guard:
        errors.extend(matrix_guard(args.tz_matrix))
    else:
        roots = list(_SCAN_ROOTS)
        if args.full_docs:
            roots.append(_REPO / "docs")
        errors.extend(lint_claims(matrix_path=args.matrix, roots=roots))

    if errors:
        for message in errors:
            print(message, file=sys.stderr)
        return 1
    mode = "matrix-guard" if args.matrix_guard else "claims-lint"
    print(f"{mode}: OK (0 violations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
