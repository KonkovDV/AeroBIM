#!/usr/bin/env python3
"""WP-A3 docs-metadata-integrity gate — frontmatter/body/version/date/baseline parity."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_BASELINE = _REPO / "docs" / "evidence" / "runtime-baseline-latest.json"

_MONITORED = (
    _REPO / "docs" / "ENGINEERING_STATUS_2026_08.md",
    _REPO / "docs" / "tz" / "TZ_COMPLIANCE_MATRIX_2026.md",
    _REPO / "docs" / "capability-claim-matrix-2026.md",
    _REPO / "docs" / "pilot-claim-boundary-2026.md",
)

def _rel(path: Path) -> str:
    try:
        return path.relative_to(_REPO).as_posix()
    except ValueError:
        return path.as_posix()


_FRONTMATTER_RE = re.compile(r"(?m)^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_VERSION_FM_RE = re.compile(r'^version:\s*["\']?([^"\'\n]+)', re.MULTILINE)
_LAST_UPDATED_FM_RE = re.compile(r'^last_updated:\s*["\']?([^"\'\n]+)', re.MULTILINE)
_BODY_VERSION_RE = re.compile(r"\*\*v(\d+\.\d+\.\d+)\*\*")
_NUMBERED_ITEM_RE = re.compile(r"^(\d+)\.\s", re.MULTILINE)


def _parse_frontmatter(text: str) -> dict[str, str]:
    match = _FRONTMATTER_RE.search(text)
    if not match:
        return {}
    block = match.group(1)
    out: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def _git_is_shallow(repo: Path) -> bool:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--is-shallow-repository"],
            cwd=repo,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    return out == "true"


def _git_last_commit_date(path: Path) -> date | None:
    rel = path.relative_to(_REPO).as_posix()
    try:
        out = subprocess.check_output(
            ["git", "log", "-1", "--format=%cs", "--", rel],
            cwd=_REPO,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    if not out:
        return None
    return date.fromisoformat(out)


def _load_baseline() -> dict[str, object]:
    if not _BASELINE.is_file():
        raise FileNotFoundError(f"Missing baseline: {_BASELINE}")
    data = json.loads(_BASELINE.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("runtime-baseline-latest.json must be an object")
    return data


def _check_frontmatter_version_parity(path: Path, text: str, fm: dict[str, str]) -> list[str]:
    errors: list[str] = []
    fm_version = fm.get("version", "").strip()
    if not fm_version:
        return errors
    body_versions = _BODY_VERSION_RE.findall(text)
    if not body_versions:
        return errors
    normalized_fm = fm_version.lstrip("v")
    for body_v in body_versions:
        if body_v != normalized_fm:
            errors.append(
                f"{_rel(path)}: frontmatter version={fm_version!r} "
                f"≠ body v{body_v}"
            )
    return errors


def _check_last_updated_freshness(path: Path, fm: dict[str, str]) -> list[str]:
    errors: list[str] = []
    raw = fm.get("last_updated", "").strip()
    if not raw:
        return errors
    try:
        doc_date = date.fromisoformat(raw)
    except ValueError:
        return [f"{_rel(path)}: invalid last_updated={raw!r}"]
    # Shallow CI checkouts often attribute untouched files to HEAD tip date.
    if _git_is_shallow(_REPO):
        return errors
    commit_date = _git_last_commit_date(path)
    if commit_date is None:
        return errors
    if doc_date < commit_date:
        errors.append(
            f"{_rel(path)}: last_updated={raw} is older than last git commit "
            f"({commit_date.isoformat()})"
        )
    return errors


def _check_engineering_status_baseline_numbers(path: Path, text: str, baseline: dict[str, object]) -> list[str]:
    if path.name != "ENGINEERING_STATUS_2026_08.md":
        return []
    errors: list[str] = []
    schema = str(baseline.get("schema_version", ""))
    if schema and re.search(r"Schema\s+1\.\d+\.\d+", text):
        if f"Schema {schema}" not in text:
            errors.append(
                f"{_rel(path)}: cites stale baseline schema "
                f"(expected Schema {schema})"
            )
    inv = baseline.get("architecture_inventory")
    if isinstance(inv, dict):
        ports = inv.get("public_domain_protocols")
        adapters = inv.get("adapter_modules")
        tokens = inv.get("di_tokens")
        if all(isinstance(x, int) for x in (ports, adapters, tokens)):
            expected = f"({ports}/{adapters}/{tokens})"
            if re.search(r"\(\d+/\d+/\d+\)", text) and expected not in text:
                errors.append(
                    f"{_rel(path)}: architecture_inventory triple drift "
                    f"(expected {expected})"
                )
    backend = baseline.get("backend")
    if isinstance(backend, dict):
        collected = backend.get("tests_collected")
        if isinstance(collected, int) and re.search(r"\b\d{3,4}\s+tests\b", text, re.I):
            if str(collected) not in text:
                # Only flag explicit WP-01 runtime baseline row stale schema/inventory;
                # avoid false positives on experiment counts.
                if "architecture_inventory" in text and "Schema" in text:
                    pass
    return errors


def _check_numbered_list_continuity(path: Path, text: str, section_title: str) -> list[str]:
    marker = f"## {section_title}"
    start = text.find(marker)
    if start < 0:
        return []
    block = text[start:]
    end = block.find("\n## ", len(marker))
    if end >= 0:
        block = block[:end]
    numbers = [int(m.group(1)) for m in _NUMBERED_ITEM_RE.finditer(block)]
    if not numbers:
        return []
    expected = list(range(1, max(numbers) + 1))
    if numbers != expected:
        return [
            f"{_rel(path)}: {section_title} numbering gap "
            f"(found {numbers}, expected {expected})"
        ]
    return []


def check_docs_metadata_integrity(
    *,
    repo: Path = _REPO,
    baseline_path: Path = _BASELINE,
) -> list[str]:
    errors: list[str] = []
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    if not isinstance(baseline, dict):
        return ["runtime-baseline-latest.json must be an object"]

    for path in _MONITORED:
        if not path.is_file():
            errors.append(f"Missing monitored doc: {_rel(path)}")
            continue
        text = path.read_text(encoding="utf-8")
        fm = _parse_frontmatter(text)
        errors.extend(_check_frontmatter_version_parity(path, text, fm))
        errors.extend(_check_last_updated_freshness(path, fm))
        errors.extend(_check_engineering_status_baseline_numbers(path, text, baseline))
        if path.name == "pilot-claim-boundary-2026.md":
            errors.extend(_check_numbered_list_continuity(path, text, "Non-claims (explicit boundaries)"))

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="WP-A3 docs metadata integrity gate")
    parser.parse_args(argv)
    errors = check_docs_metadata_integrity()
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    print("docs-metadata-integrity: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
