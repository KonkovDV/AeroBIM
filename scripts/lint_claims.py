#!/usr/bin/env python3
"""Claims Lock linter (WP-R10) — executable honesty gate for AeroBIM.

Rules source: docs/capability-claim-matrix-2026.md (forbidden table) + TZ matrix guard.
Explicit allow only: ``claims-lint: allow reason="..."`` per line or
``claims-lint: allow-file reason="..."`` in the first ten lines **and** path listed in
``audit/claims_allow_file_registry.json`` (N-29: header alone is not amnesty).

HDS-SUB-02: a negation marker on a heading or list item covers following
list items until the next heading or a non-list paragraph (loose Markdown
lists with blank lines between items stay in the same run).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path

from kitchen_denylist import lint_kitchen_tokens as scan_kitchen_tokens
from kitchen_denylist import lint_pack_quarantine

_REPO = Path(__file__).resolve().parents[1]
_MATRIX = _REPO / "docs" / "capability-claim-matrix-2026.md"
_TZ_MATRIX = _REPO / "docs" / "tz" / "TZ_COMPLIANCE_MATRIX_2026.md"
_BLOCKED_REGISTRY = _REPO / "audit" / "tz_matrix_blocked_registry.json"
_ALLOW_FILE_REGISTRY = _REPO / "audit" / "claims_allow_file_registry.json"

_SCAN_ROOTS = (
    _REPO / "README.md",
    _REPO / "README.ru.md",
    _REPO / "frontend" / "src",
    _REPO / "docs" / "docs.md",
    _REPO / "docs" / "partners",
    _REPO / "docs" / "demo",
    _REPO / "docs" / "TIER0_INDEX.md",
    _REPO / "submission",
)

_EXCLUDE_SUFFIXES = {".min.js"}
_EXCLUDE_PATH_FRAGMENTS = (
    "capability-claim-matrix-2026.md",
    "CLAIMS_LOCK",
    "pilot-claim-boundary",
    "CRITICAL_BLOCKERS.md",
    "RED_TEAM",
    "runtime-baseline-latest.json",
    "ENGINEERING_STATUS_2026_08.md",
    "competitive-matrix",
    "REPO_DEEP_MAP",
    # HDX-LINT-01: no directory blinds. Quote-inventory files stay fragment-excluded.
    "FINDINGS_RECLASSIFICATION",
    "docs/evidence/local/",
    "kt2-handoff-2026-08-11/wall-guid/",
)

_ALLOW_RE = re.compile(
    r"claims-lint:\s*allow\s+reason=(?P<q>\"[^\"]+\"|'[^']+')",
    re.IGNORECASE,
)
_ALLOW_FILE_RE = re.compile(
    r"claims-lint:\s*allow-file\s+reason=(?P<q>\"[^\"]+\"|'[^']+')",
    re.IGNORECASE,
)
_MARKDOWN_MARKUP = re.compile(r"[*_`~\[\]()]")
_LIST_ITEM_RE = re.compile(r"^(?:[-*+]|\d+[.)])\s+\S")
_WORDING_SSOT = _REPO / "audit" / "claims_forbidden_wording.json"
# Heading-scoped carry only. Broad same-line markers such as "missing" must
# not amnesty an entire section (HDS-SUB-02).
_SECTION_NEGATION_MARKERS = (
    "запрещено",
    "нельзя",
    "forbidden",
    "not claimed",
    "не заявляется",
    "не утвержд",
    "out of scope",
    "вне scope",
    "until evidenced",
    "до доказательств",
)

_BUILTIN_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "forbidden_accuracy_gt_90",
        re.compile(r"(?i)(более\s+90|>\s*90\s*%|accuracy.{0,20}9[0-9]\s*%)"),
    ),
    (
        "forbidden_sla_30min",
        re.compile(r"(?i)(до\s*30\s*мин|≤\s*30\s*(мин|minutes)|30\s*min(ute)?s?\s+SLA)"),
    ),
    ("forbidden_production_ready", re.compile(r"(?i)production[-\s]?ready")),
    (
        "forbidden_external_audit",
        re.compile(r"(?i)(внешн(ий|его)\s+аудит|external\s+academic\s+audit)"),
    ),
    ("forbidden_native_dwg", re.compile(r"(?i)(native\s+DWG|нативн\w*\s+DWG|DWG\s+поддерж)")),
    ("forbidden_cde_ready", re.compile(r"(?i)(CDE[-\s]?ready|готов\w*\s+к\s+CDE)")),
    ("forbidden_sso_ready", re.compile(r"(?i)(SSO\s+ready|OIDC\s+BFF\s+ready)")),
    ("forbidden_ukep_verified", re.compile(r"(?i)(УКЭП\s+проверен|trust\s+chain\s+verified)")),
    (
        "forbidden_whole_mit",
        re.compile(r"(?i)(весь\s+продукт.{0,20}MIT|entire\s+product.{0,20}MIT)"),
    ),
    ("forbidden_aecv_customer", re.compile(r"(?i)AECV.{0,40}(customer|заказчик|точност)")),
    (
        "forbidden_open_corpus_accuracy",
        re.compile(r"(?i)(open[-\s]?corpus.{0,30}точност|BSI.{0,20}product\s+accuracy)"),
    ),
    (
        "forbidden_customer_pack_checked",
        re.compile(r"(?i)пакет\s+заказчика\s+проверен"),
    ),
    (
        "forbidden_43gb_processed",
        re.compile(r"(?i)43\s*гб\s+обработан"),
    ),
    (
        "forbidden_data_regime_agreed",
        re.compile(r"(?i)режим\s+данных\s+согласован"),
    ),
    (
        "forbidden_confidentiality_signed",
        re.compile(r"(?i)соглашение\s+о\s+конфиденциальности\s+подписано"),
    ),
    (
        "forbidden_first_in_russia_versions",
        re.compile(r"(?i)первые\s+в\s+россии\s+сравниваем\s+версии"),
    ),
    (
        "forbidden_better_than_city_normcontrol",
        re.compile(r"(?i)точнее\s+городск\w*\s+нормоконтрол"),
    ),
    (
        "forbidden_replace_foreign_checkers",
        re.compile(r"(?i)заменяем\s+зарубежн\w*\s+проверяльщик"),
    ),
    (
        "forbidden_ids_better_than_market",
        re.compile(r"(?i)машиночитаем.{0,48}лучше\s+рынка"),
    ),
    (
        "forbidden_integrated_customer_platform",
        re.compile(r"(?i)интегрированы\s+с\s+платформой\s+заказчика"),
    ),
]

_KITCHEN_PATH_PREFIXES = (
    "docs/roadmap/",
    "docs/partners/outreach/",
    "docs/research/",
    "docs/gtm/",
    "docs/customer/",
    "docs/customer-discovery/",
    "docs/plans/",
    "docs/quality/RED_TEAM",
    "docs/demo/TRACKER_MEETING",
    "docs/demo/KT2_HOSTILE_QA",
    "docs/demo/KT2_VIDEO_SCRIPT",
)


def lint_kitchen_tokens() -> list[str]:
    """Publication gate: no protected locators from the external list."""

    return scan_kitchen_tokens()


def lint_kitchen_paths() -> list[str]:
    """Tracked kitchen path prefixes must not re-enter git."""

    proc = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=_REPO,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return [f"[kitchen_path] git ls-files failed: {proc.returncode}"]
    hits: list[str] = []
    for raw in proc.stdout.split(b"\0"):
        if not raw:
            continue
        rel = raw.decode("utf-8", "replace").replace("\\", "/")
        for prefix in _KITCHEN_PATH_PREFIXES:
            if rel.startswith(prefix):
                hits.append(f"[kitchen_path] {rel}")
                break
    return hits


_BOUNDARY_MARKERS = (
    "claim_level",
    "coverage_map",
    "coverage-map",
    "NO_GO",
    "customer_go",
    "regulatory_measurement",
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
_METRIC_NUMBER = re.compile(r"(?i)(\d+[,.]?\d*\s*%|>\s*\d+\s*%|≈\s*\d+[,.]?\d*\s*%|\d+\s*/\s*\d+)")


def claim_needs_boundary_violations(path: Path, text: str) -> list[str]:
    """WP-E1 / G6: numeric metric claims require an in-paragraph boundary marker.

    N-28: Markdown table rows are checked individually (not skipped).
    """
    try:
        rel = path.relative_to(_repo_root()).as_posix()
    except ValueError:
        rel = path.as_posix()
    violations: list[str] = []

    def _check_unit(unit: str, label: str) -> None:
        if not _CLAIM_TRIGGER.search(unit) or not _METRIC_NUMBER.search(unit):
            return
        if not any(marker.lower() in unit.lower() for marker in _BOUNDARY_MARKERS):
            violations.append(
                f"{rel}:{label}: claim_needs_boundary "
                "(numeric claim near coverage/accuracy/publishable requires boundary marker)"
            )

    for para_idx, para in enumerate(re.split(r"\n\s*\n", text), start=1):
        stripped_lines = [ln for ln in para.splitlines() if ln.strip()]
        if stripped_lines and all(ln.lstrip().startswith("|") for ln in stripped_lines):
            for row_idx, row in enumerate(stripped_lines, start=1):
                _check_unit(row, f"table-row:{para_idx}.{row_idx}")
            continue
        _check_unit(para, f"paragraph:{para_idx}")
    return violations


def _repo_root() -> Path:
    return _REPO


@lru_cache(maxsize=1)
def _git_tracked_relpaths() -> frozenset[str] | None:
    """Tracked files only. None = git unavailable (temp fixtures / tarball)."""
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=_REPO,
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return frozenset(
        part.replace("\\", "/")
        for part in result.stdout.decode("utf-8", errors="replace").split("\0")
        if part.strip()
    )


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
            if any(part in {".git", "node_modules", "__pycache__", ".venv", ".local"} for part in path.parts):
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
    tracked = _git_tracked_relpaths()
    if tracked is not None and rel not in tracked:
        return False
    if any(fragment in rel for fragment in _EXCLUDE_PATH_FRAGMENTS):
        return False
    # Evidence JSON/PDF/HTML/txt quote forbidden phrases as denial/inventory
    # text (capability reasons, generated reports), not product claims.
    if "/evidence/" in f"/{rel}" and path.suffix.lower() in {".json", ".pdf", ".html", ".txt"}:
        return False
    return True


def _load_allow_file_paths(registry_path: Path = _ALLOW_FILE_REGISTRY) -> frozenset[str]:
    """N-29: allow-file header is not a blank amnesty — path must be registered."""
    if not registry_path.is_file():
        return frozenset()
    try:
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return frozenset()
    paths = payload.get("paths", []) if isinstance(payload, dict) else []
    return frozenset(str(p).replace("\\", "/").strip() for p in paths if str(p).strip())


_ALLOW_FILE_PATHS = _load_allow_file_paths()


def _file_allow_reason(text: str) -> str | None:
    for line in text.splitlines()[:10]:
        match = _ALLOW_FILE_RE.search(line)
        if match:
            return match.group("q").strip("\"'")
    return None


def _candidate_files(roots: list[Path] | None = None) -> list[Path]:
    if not roots:
        return _iter_scan_files()
    files: list[Path] = []
    for root in roots:
        if root.is_file():
            files.append(root)
            continue
        if not root.is_dir():
            continue
        files.extend(path for path in root.rglob("*") if path.is_file())
    return sorted(set(files))


def exclusion_stats(*, roots: list[Path] | None = None) -> dict[str, int]:
    """HDX-LINT-01: fragment excludes stay visible; directory blinds removed."""

    excluded_untracked = 0
    excluded_by_fragment = 0
    excluded_by_suffix = 0
    excluded_evidence = 0
    scanned = 0
    tracked = _git_tracked_relpaths()
    for path in _candidate_files(roots):
        if path.suffix.lower() in _EXCLUDE_SUFFIXES:
            excluded_by_suffix += 1
            continue
        try:
            rel = path.relative_to(_repo_root()).as_posix()
        except ValueError:
            scanned += 1
            continue
        if tracked is not None and rel not in tracked:
            excluded_untracked += 1
            continue
        if any(fragment in rel for fragment in _EXCLUDE_PATH_FRAGMENTS):
            excluded_by_fragment += 1
            continue
        if "/evidence/" in f"/{rel}" and path.suffix.lower() in {".json", ".pdf", ".html", ".txt"}:
            excluded_evidence += 1
            continue
        scanned += 1
    return {
        "scanned": scanned,
        "excluded_by_fragment": excluded_by_fragment,
        "excluded_by_suffix": excluded_by_suffix,
        "excluded_evidence": excluded_evidence,
        "excluded_untracked": excluded_untracked,
    }


def _format_exclusion_stats(stats: dict[str, int]) -> str:
    return (
        f"scanned={stats['scanned']} "
        f"excluded_by_fragment={stats['excluded_by_fragment']} "
        f"excluded_untracked={stats.get('excluded_untracked', 0)} "
        f"excluded_evidence={stats['excluded_evidence']}"
    )


def _line_allowed(line: str) -> bool:
    return _ALLOW_RE.search(line) is not None


@lru_cache(maxsize=1)
def _negation_markers() -> tuple[str, ...]:
    if not _WORDING_SSOT.is_file():
        return _SECTION_NEGATION_MARKERS
    try:
        payload = json.loads(_WORDING_SSOT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _SECTION_NEGATION_MARKERS
    raw = payload.get("negation_markers", []) if isinstance(payload, dict) else []
    markers = tuple(str(item) for item in raw if str(item).strip())
    return markers or _SECTION_NEGATION_MARKERS


def _normalized_line(line: str) -> str:
    return _MARKDOWN_MARKUP.sub("", line.lower())


def _line_has_marker(line: str, markers: Sequence[str]) -> bool:
    normalized = _normalized_line(line)
    return any(marker.lower() in normalized for marker in markers)


def _is_markdown_list_item(stripped: str) -> bool:
    return _LIST_ITEM_RE.match(stripped) is not None


def negation_coverage(
    lines: Sequence[str],
    markers: Sequence[str] | None = None,
) -> list[bool]:
    """True when a line sits in an inherited negation context (HDS-SUB-02)."""
    pool = tuple(markers) if markers is not None else _negation_markers()
    covered = [False] * len(lines)
    section_on = False
    list_on = False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#"):
            section_on = _line_has_marker(line, _SECTION_NEGATION_MARKERS)
            list_on = False
            covered[index] = _line_has_marker(line, pool)
            continue
        if not stripped:
            continue
        if _is_markdown_list_item(stripped):
            own = _line_has_marker(line, pool)
            list_on = own or list_on or section_on
            covered[index] = own or list_on
            continue
        list_on = False
        covered[index] = _line_has_marker(line, pool)
    return covered


def lint_claims(
    *,
    matrix_path: Path,
    roots: list[Path] | None = None,
) -> list[str]:
    patterns = _patterns_from_matrix(matrix_path)
    violations: list[str] = []
    for path in _candidate_files(roots):
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
        allow_file_reason = _file_allow_reason(text)
        # N-29 kill: header alone is insufficient; path must be in registry.
        if allow_file_reason and rel in _ALLOW_FILE_PATHS:
            continue
        lines = text.splitlines()
        inherited = negation_coverage(lines, _SECTION_NEGATION_MARKERS)
        for lineno, line in enumerate(lines, start=1):
            if _line_allowed(line) or inherited[lineno - 1]:
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
        violations.append(f"{rel}:{lineno}: Samolet-blocked row marked {status!r}: {line.strip()}")
    return violations


# HD4-CIT-02: fabricated Elsevier year-twins (errata 2026-08-04). Audit-trail
# docs may quote the DOI; live citations must not.
_FABRICATED_DOIS = frozenset({"10.1016/j.aei.2026.103676"})
_ELSEVIER_DOI_RE = re.compile(
    r"10\.1016/j\.(?P<journal>[a-z]+)\.(?P<year>20\d{2})\.(?P<article>\d+)",
    re.IGNORECASE,
)
_GENERIC_DOI_RE = re.compile(r"\b(10\.\d{4,9}/[^\s\]\)\"'<>]+)")
_DOI_CONTEXT_RE = re.compile(
    r"(?i)(?:doi\.org|/doi/|doi:\s*|https://doi\.org|datacite|crossref)",
)
_CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")
_SCHOLARLY_DOI_PREFIXES = (
    "10.1016/",
    "10.1109/",
    "10.1061/",
    "10.3390/",
    "10.1007/",
    "10.1080/",
    "10.1145/",
    "10.1038/",
    "10.5281/",
    "10.48550/",
    "10.35490/",
)
_OPERATOR_PATH_PARTS = frozenset({".local", ".venv", "node_modules", "site-packages"})
_CITATION_AUDIT_TRAIL_FRAGMENTS = (
    "CITATION_ERRATA",
    "SOURCE_VERIFICATION_REPORT",
    "AECV_BASELINE_COMPARE",
    "RED_TEAM",
)
_CITATION_SCAN_SUFFIXES = {".md", ".rst", ".txt"}


def _is_operator_or_vendor_path(rel: str) -> bool:
    """Skip gitignored operator dumps and vendor trees (fact-check 2026-09-02)."""
    return any(part in _OPERATOR_PATH_PARTS for part in rel.replace("\\", "/").split("/"))


def is_citation_doi_candidate(token: str, *, line: str) -> bool:
    """True only for a scholarly DOI in citation context.

    Bare ``10.3049/47868`` from calc sheets and ``10.2025/лк-цнэ-3419`` path
    fragments are not DOIs. Require ``doi.org`` / ``doi:`` nearby, or a known
    publisher prefix without Cyrillic.
    """
    cleaned = token.strip().rstrip(").,;]")
    if not cleaned.startswith("10."):
        found = _GENERIC_DOI_RE.search(cleaned)
        if not found:
            return False
        cleaned = found.group(1).rstrip(").,;]")
    if _CYRILLIC_RE.search(cleaned):
        return False
    if _DOI_CONTEXT_RE.search(line):
        return True
    lowered = cleaned.lower()
    return any(lowered.startswith(prefix) for prefix in _SCHOLARLY_DOI_PREFIXES)


def _is_citation_audit_trail(rel: str) -> bool:
    posix = rel.replace("\\", "/")
    return any(fragment in posix for fragment in _CITATION_AUDIT_TRAIL_FRAGMENTS)


def lint_citation_twins(*, roots: list[Path] | None = None) -> list[str]:
    """Reject fabricated DOI twins outside bibliography errata / audit trail."""
    scan_roots = roots if roots is not None else [_REPO / "README.md", _REPO / "README.ru.md", _REPO / "docs"]
    files: list[Path] = []
    for root in scan_roots:
        if root.is_file():
            files.append(root)
        elif root.is_dir():
            files.extend(p for p in root.rglob("*") if p.is_file())

    violations: list[str] = []
    years_by_article: dict[tuple[str, str], set[str]] = {}
    for path in sorted(set(files)):
        if path.suffix.lower() not in _CITATION_SCAN_SUFFIXES:
            continue
        if any(part in _OPERATOR_PATH_PARTS for part in path.parts):
            continue
        try:
            rel = path.relative_to(_repo_root()).as_posix()
        except ValueError:
            rel = path.as_posix()
        if _is_operator_or_vendor_path(rel):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        trail = _is_citation_audit_trail(rel)
        for lineno, line in enumerate(text.splitlines(), start=1):
            lowered = line.lower()
            for doi in _FABRICATED_DOIS:
                if doi.lower() in lowered and not trail:
                    violations.append(f"{rel}:{lineno}: [fabricated_doi] {doi}")
            if trail:
                continue
            for match in _ELSEVIER_DOI_RE.finditer(line):
                key = (match.group("journal").lower(), match.group("article"))
                years_by_article.setdefault(key, set()).add(match.group("year"))
    for (journal, article), years in sorted(years_by_article.items()):
        if len(years) < 2:
            continue
        ordered = sorted(years)
        violations.append(
            "[elsevier_year_twin] "
            f"10.1016/j.{journal}.{ordered[0]}.{article} vs year {ordered[1]} "
            "(Elsevier article numbers are not reused across years)"
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
        errors.extend(lint_kitchen_tokens())
        errors.extend(lint_kitchen_paths())
        errors.extend(lint_pack_quarantine())

    errors.extend(lint_citation_twins())

    stats: dict[str, int] | None = None
    if not args.matrix_guard and not args.claim_boundary_guard:
        scan_roots = list(_SCAN_ROOTS)
        if args.full_docs:
            scan_roots.append(_REPO / "docs")
        stats = exclusion_stats(roots=scan_roots)

    if errors:
        for message in errors:
            print(message, file=sys.stderr)
        if stats is not None:
            print(
                f"claims-lint: {_format_exclusion_stats(stats)} "
                "(directory excludes remain a manual honesty path)",
                file=sys.stderr,
            )
        return 1
    mode = "matrix-guard" if args.matrix_guard else "claims-lint"
    if args.claim_boundary_guard:
        mode = "claim-boundary-guard"
    if stats is not None:
        print(f"{mode}: OK (0 violations; {_format_exclusion_stats(stats)})")
    else:
        print(f"{mode}: OK (0 violations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
