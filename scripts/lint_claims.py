#!/usr/bin/env python3
"""Claims Lock linter (WP-R10) — executable honesty gate for AeroBIM.

Rules source: docs/capability-claim-matrix-2026.md (forbidden table) + TZ matrix guard.
Explicit allow only: ``claims-lint: allow reason="..."`` per line or
``claims-lint: allow-file reason="..."`` in the first ten lines of a file.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_MATRIX = _REPO / "docs" / "capability-claim-matrix-2026.md"
_TZ_MATRIX = _REPO / "docs" / "tz" / "TZ_COMPLIANCE_MATRIX_2026.md"
_BLOCKED_REGISTRY = _REPO / "audit" / "tz_matrix_blocked_registry.json"

_SCAN_ROOTS = (
    _REPO / "README.md",
    _REPO / "README.ru.md",
    _REPO / "frontend" / "src",
    _REPO / "docs" / "docs.md",
    _REPO / "docs" / "partners",
    _REPO / "docs" / "demo-format-2026-08.md",
    _REPO / "docs" / "customer",
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
_ALLOW_FILE_RE = re.compile(
    r"claims-lint:\s*allow-file\s+reason=(?P<q>\"[^\"]+\"|'[^']+')",
    re.IGNORECASE,
)

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

_BOUNDARY_MARKERS = (
    "claim_level",
    "coverage_map",
    "coverage-map",
    "NO_GO",
    "not product accuracy",
    "не точность",
    "fixture corpus",
    "open-source",
    "open source",
    "claim boundary",
    "claim_boundary",
    "RT-001",
    "RT-002",
    "RT-003",
    "карта покрытия",
    "n=",
)

_CLAIM_TRIGGER = re.compile(
    r"(?i)\b(coverage|accuracy|precision|recall|detection|publishable|полнот[аы]|точност[ьи]|покрыти[ея])\b"
)
_METRIC_NUMBER = re.compile(
    r"(?i)(\d+[,.]?\d*\s*%|>\s*\d+\s*%|≈\s*\d+[,.]?\d*\s*%|\d+\s*/\s*\d+)"
)


def claim_needs_boundary_violations(path: Path, text: str) -> list[str]:
    """WP-E1 / G6: numeric metric claims require an in-paragraph boundary marker."""
    try:
        rel = path.relative_to(_repo_root()).as_posix()
    except ValueError:
        rel = path.as_posix()
    violations: list[str] = []
    for para_idx, para in enumerate(re.split(r"\n\s*\n", text), start=1):
        if para.lstrip().startswith("|"):
            continue
        if not _CLAIM_TRIGGER.search(para) or not _METRIC_NUMBER.search(para):
            continue
        if not any(marker.lower() in para.lower() for marker in _BOUNDARY_MARKERS):
            violations.append(
                f"{rel}:paragraph:{para_idx}: claim_needs_boundary "
                "(numeric claim near coverage/accuracy/publishable requires boundary marker)"
            )
    return violations


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


def _file_allow_reason(text: str) -> str | None:
    for line in text.splitlines()[:10]:
        match = _ALLOW_FILE_RE.search(line)
        if match:
            return match.group("q").strip("\"'")
    return None


def _line_allowed(line: str) -> bool:
    return _ALLOW_RE.search(line) is not None


def lint_claims(
    *,
    matrix_path: Path,
    roots: list[Path] | None = None,
) -> list[str]:
    patterns = _patterns_from_matrix(matrix_path)
    violations: list[str] = []
    files: list[Path] = []
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
        if _file_allow_reason(text):
            continue
        try:
            rel = path.relative_to(_repo_root()).as_posix()
        except ValueError:
            rel = path.as_posix()
        for lineno, line in enumerate(text.splitlines(), start=1):
            if _line_allowed(line):
                continue
            for rule_id, pattern in patterns:
                if pattern.search(line):
                    violations.append(f"{rel}:{lineno}: [{rule_id}] {line.strip()[:160]}")
        # G6 claim_needs_boundary stays behind --claim-boundary-guard only
    return violations


def _load_blocked_registry(registry_path: Path) -> tuple[list[re.Pattern[str]], set[str]]:
    if not registry_path.is_file():
        raise FileNotFoundError(f"Missing blocked registry: {registry_path}")
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    patterns = [
        re.compile(str(raw))
        for raw in payload.get("blocked_requirement_patterns", [])
        if str(raw).strip()
    ]
    forbidden = {str(s).strip().lower() for s in payload.get("forbidden_statuses", ["done"])}
    return patterns, forbidden


def _table_status_index(cells: list[str]) -> int | None:
    for index, cell in enumerate(cells):
        if cell.strip().lower() == "status":
            return index
    return None


def _is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(set(cell.strip()) <= {"-"} for cell in cells if cell.strip())


def matrix_guard(
    tz_matrix_path: Path,
    *,
    registry_path: Path | None = None,
) -> list[str]:
    if not tz_matrix_path.is_file():
        return [f"Missing TZ matrix: {tz_matrix_path.as_posix()}"]
    try:
        blocked_patterns, forbidden_statuses = _load_blocked_registry(
            registry_path or _BLOCKED_REGISTRY
        )
    except (OSError, json.JSONDecodeError, FileNotFoundError) as exc:
        return [f"Blocked registry error: {exc}"]

    violations: list[str] = []
    status_index: int | None = None
    rel = tz_matrix_path.as_posix()
    try:
        rel = tz_matrix_path.relative_to(_repo_root()).as_posix()
    except ValueError:
        pass

    for lineno, line in enumerate(tz_matrix_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.startswith("|"):
            status_index = None
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        header_index = _table_status_index(cells)
        if header_index is not None:
            status_index = header_index
            continue
        if _is_separator_row(cells) or status_index is None:
            continue
        if len(cells) <= status_index:
            continue
        requirement = cells[0]
        status = cells[status_index].strip().lower()
        if status not in forbidden_statuses:
            continue
        if not any(pattern.search(requirement) for pattern in blocked_patterns):
            continue
        violations.append(
            f"{rel}:{lineno}: Samolet-blocked row marked {status!r}: {line.strip()}"
        )
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--full-docs",
        action="store_true",
        help="Also scan docs/** (honesty docs need allow-file or allow reason lines)",
    )
    parser.add_argument(
        "--matrix-guard",
        action="store_true",
        help="Verify TZ compliance matrix: registry-blocked rows are not marked done",
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
    parser.add_argument(
        "--claim-boundary-guard",
        action="store_true",
        help="Verify numeric coverage/accuracy claims include in-paragraph boundary markers (G6)",
    )
    parser.add_argument(
        "--blocked-registry",
        type=Path,
        default=_BLOCKED_REGISTRY,
        help="Explicit Samolet-blocked TZ row registry (audit/tz_matrix_blocked_registry.json)",
    )
    args = parser.parse_args(argv)

    errors: list[str] = []
    if args.matrix_guard:
        errors.extend(matrix_guard(args.tz_matrix, registry_path=args.blocked_registry))
    elif args.claim_boundary_guard:
        targets = [_REPO / "docs" / "docs.md"]
        for path in targets:
            if path.is_file():
                errors.extend(
                    claim_needs_boundary_violations(path, path.read_text(encoding="utf-8"))
                )
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
