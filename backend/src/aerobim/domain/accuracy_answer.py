"""Accuracy-answer artifact for TZ clash-accuracy criterion (methodology, not product %).

Each numeric row carries corpus_kind and n. None of the rows is product accuracy
on a customer pack. Checkpoint GO; customer_go false.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final

from aerobim.domain.checkpoint import CHECKPOINT, CUSTOMER_GO, PRECISION_PUBLISHABLE
from aerobim.domain.study_design import wilson_interval

CLAIM_BOUNDARY: Final = (
    "Numbers below are fixture, synthetic, or open-corpus measurements. "
    "Not product accuracy. Not TZ >90%. Not customer-pack recall. "
    "Checkpoint GO; customer_go false. LLM is not a rater (ADR-001)."
)

SCHEMA_VERSION: Final = "1.0.0"
ARTIFACT_TYPE: Final = "accuracy_answer"

_CLASH_PR = Path("docs/evidence/clash-measurement-slice-2026-08/precision-recall.json")
_INJECTION = Path("docs/evidence/defect-injection-recall-run-fixture-latest.json")
_KAPPA = Path("docs/evidence/rt001-dual-rater-simulation-2026-09.json")
_TYPICAL = Path("samples/benchmarks/samolet-typical-errors-catalog.json")
_SPRINT3_MD = Path("docs/evidence/sprint3-open-corpus-battery-2026-08.md")


def _load_json(repo: Path, rel: Path) -> dict[str, Any]:
    path = repo / rel
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"{rel} is not a JSON object")
    return dict(payload)


def _wilson_row(successes: int, trials: int) -> dict[str, Any]:
    interval = wilson_interval(successes, trials, alpha=0.05)
    return {
        "successes": successes,
        "n": trials,
        "point": interval.point,
        "wilson_95_lower": interval.lower,
        "wilson_95_upper": interval.upper,
        "method": "wilson_score",
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def assemble_accuracy_answer(repo: Path) -> dict[str, Any]:
    """Build the jury-facing accuracy answer from committed evidence files."""

    clash = _load_json(repo, _CLASH_PR)
    micro = _mapping(clash.get("micro"))
    clash_n = int(micro.get("support") or 0)
    clash_tp = int(micro.get("tp") or 0)
    clash_wilson = _wilson_row(clash_tp, clash_n) if clash_n else {}

    injection = _load_json(repo, _INJECTION)
    aggregate = _mapping(injection.get("aggregate"))
    inj_n = int(aggregate.get("trials") or 0)
    inj_killed = int(aggregate.get("killed") or 0)

    kappa = _load_json(repo, _KAPPA)
    catalog = _load_json(repo, _TYPICAL)
    patterns = catalog.get("patterns")
    typical_n = len(patterns) if isinstance(patterns, list) else 0
    confirmed = int(catalog.get("customer_confirmed_patterns") or 0)

    rows = [
        {
            "id": "fixture_aabb_clash",
            "metric": "precision_recall",
            "precision": micro.get("precision"),
            "recall": micro.get("recall"),
            "n": clash_n,
            "corpus_kind": "fixture",
            "corpus_id": clash.get("dataset_id"),
            "wilson_95": clash_wilson,
            "is_product_accuracy": False,
            "publishable": False,
            "not": "customer corpus; TZ clash accuracy >90%; IfcClash mesh product",
            "source": str(_CLASH_PR).replace("\\", "/"),
        },
        {
            "id": "defect_injection_recall",
            "metric": "mutation_kill_recall",
            "recall": aggregate.get("recall_point"),
            "n": inj_n,
            "killed": inj_killed,
            "corpus_kind": "synthetic",
            "wilson_95": _mapping(aggregate.get("wilson_95")),
            "is_product_accuracy": False,
            "publishable": False,
            "not": "semantic TP; customer-pack recall",
            "source": str(_INJECTION).replace("\\", "/"),
        },
        {
            "id": "open_corpus_binary_match",
            "metric": "binary_match_rate",
            "fixture_n": 7,
            "fixture_matched": 7,
            "bsi_ids_n": 290,
            "corpus_kind": "open_corpus",
            "is_product_accuracy": False,
            "publishable": False,
            "not": "TP/FP; product accuracy; summary.passed as a quality score",
            "source": str(_SPRINT3_MD).replace("\\", "/"),
        },
        {
            "id": "dual_rater_simulation",
            "metric": "agreement",
            "cohens_kappa": kappa.get("cohens_kappa"),
            "krippendorff_alpha": kappa.get("krippendorff_alpha"),
            "gwet_ac1": kappa.get("gwet_ac1"),
            "n": kappa.get("n"),
            "corpus_kind": "synthetic",
            "independent_human_raters": kappa.get("independent_human_raters"),
            "labelled": "simulation",
            "is_product_accuracy": False,
            "publishable": False,
            "not": "two human raters; LLM-as-rater; RT-001 closed",
            "source": str(_KAPPA).replace("\\", "/"),
        },
        {
            "id": "typical_error_class_coverage",
            "metric": "class_coverage",
            "n": typical_n,
            "customer_confirmed_patterns": confirmed,
            "corpus_kind": "synthetic",
            "is_product_accuracy": False,
            "publishable": False,
            "not": "precision; customer-confirmed typical-error gold",
            "source": str(_TYPICAL).replace("\\", "/"),
        },
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": ARTIFACT_TYPE,
        "checkpoint": CHECKPOINT,
        "customer_go": CUSTOMER_GO,
        "precision_claim_publishable": PRECISION_PUBLISHABLE,
        "is_accuracy": False,
        "claim_level": "coverage_map_only",
        "claim_boundary": CLAIM_BOUNDARY,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "rows": rows,
        "why_not_transferable": [
            "Customer pack has no dual-rater gold and no frozen detection labels.",
            "Their books are an RD acceptance checklist; "
            "the unit is a requirement row, not an IFC finding.",
            "Fixture n is small; Wilson lower bound must be spoken with the point estimate.",
            "Simulated raters are not humans. LLM is not a rater.",
        ],
        "needed_to_measure_on_customer_corpus": [
            "labeled customer corpus with finding-level gold",
            "two named human raters",
            "blinding / independent passes",
            "held-out split",
            "coverage map hash frozen before labels",
        ],
    }


def render_accuracy_answer_markdown(payload: Mapping[str, Any]) -> str:
    lines = [
        "<!-- claims-lint: allow-file "
        'reason="Accuracy-answer artifact; TZ 90% quoted as criterion not claim; NO_GO" -->',
        "---",
        'title: "Accuracy answer — fixture/open-corpus numbers, not product %"',
        'date: "2026-09-09"',
        "status: active",
        'version: "1.0.0"',
        "closes_rt001: false",
        "closes_rt002: false",
        "closes_rt003: false",
        "claim_level: coverage_map_only",
        "---",
        "",
        "# Ответ на критерий «точность >90 %»",
        "",
        "Это методика и числа с границей переноса, не точность продукта.",
        "На комплекте заказчика не измеряли.",
        "",
        "| id | metric | n | corpus_kind | чем не является |",
        "|---|---|---:|---|---|",
    ]
    for row in payload.get("rows") or ():
        if not isinstance(row, Mapping):
            continue
        n_cell = row.get("n") or row.get("fixture_n") or "—"
        lines.append(
            f"| {row.get('id')} | {row.get('metric')} | {n_cell} | "
            f"{row.get('corpus_kind')} | {row.get('not')} |"
        )
    lines.extend(
        [
            "",
            "## Чтобы измерить на комплекте заказчика",
            "",
        ]
    )
    for item in payload.get("needed_to_measure_on_customer_corpus") or ():
        lines.append(f"- {item}")
    lines.extend(["", "Checkpoint **GO**; `customer_go` false.", ""])
    return "\n".join(lines) + "\n"
