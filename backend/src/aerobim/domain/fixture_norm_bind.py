"""Bind committed demo-TZ clauses onto known fixture IDS specs.

Source: ``samples/specifications/techlab-tz.txt`` (п. 4.1–4.5). Not SP 2.13130,
not customer class II/C0, not a signed Samolet profile.
Checkpoint GO (regulatory_measurement_mvp; customer_go false).
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

from aerobim.domain.models import ValidationIssue

_BIND_REL = Path("samples") / "ids" / "fixture-norm-bind.json"
_CLAIM = (
    "Fixture IDS implements demo TZ clauses from techlab-tz.txt. "
    "Not SP 2.13130. Not customer class II/C0. Checkpoint GO "
    "(regulatory_measurement_mvp; customer_go false)."
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def load_fixture_norm_binds(repo: Path | None = None) -> dict[str, dict[str, str]]:
    path = (repo or _repo_root()) / _BIND_REL
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {}
    raw = payload.get("by_specification_name")
    if not isinstance(raw, dict):
        return {}
    out: dict[str, dict[str, str]] = {}
    for name, bind in raw.items():
        if not isinstance(bind, dict):
            continue
        source = str(bind.get("norm_source") or "").strip()
        clause = str(bind.get("norm_clause") or "").strip()
        if source and clause:
            out[str(name)] = {"norm_source": source, "norm_clause": clause}
    return out


def stamp_issues_with_fixture_norm(
    issues: Sequence[ValidationIssue],
    *,
    binds: dict[str, dict[str, str]] | None = None,
    repo: Path | None = None,
) -> tuple[ValidationIssue, ...]:
    """Fill empty norm_source/clause for ``IDS-<spec>`` using the committed sidecar."""

    table = binds if binds is not None else load_fixture_norm_binds(repo)
    if not table:
        return tuple(issues)
    stamped: list[ValidationIssue] = []
    for issue in issues:
        if issue.norm_clause and str(issue.norm_clause).strip():
            stamped.append(issue)
            continue
        spec = _spec_name(issue)
        bind = table.get(spec) if spec else None
        if not bind:
            stamped.append(issue)
            continue
        stamped.append(
            replace(
                issue,
                norm_source=bind["norm_source"],
                norm_clause=bind["norm_clause"],
            )
        )
    return tuple(stamped)


def _spec_name(issue: ValidationIssue) -> str | None:
    rule = str(issue.rule_id or "")
    if rule.startswith("IDS-"):
        return rule[4:] or None
    return None


def fixture_norm_bind_claim() -> str:
    return _CLAIM


def fixture_norm_bind_snapshot() -> dict[str, Any]:
    return {
        "artifact_type": "fixture_norm_bind",
        "claim_boundary": _CLAIM,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "bind_count": len(load_fixture_norm_binds()),
    }
