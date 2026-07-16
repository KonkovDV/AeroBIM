"""Exact-match TP/FP/FN harness for adjudicated AeroBIM findings.

The harness measures a frozen detection run against an independent label set.  It
never treats synthetic fixtures as customer precision evidence and provides an
optional protocol gate for datasets that claim to have completed adjudication.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

_SCHEMA_VERSION = "1.0.0"
_MAX_INPUT_BYTES = 10 * 1024 * 1024
_MAX_FINDINGS = 100_000
_DATASET_STATUSES = {"synthetic", "draft", "adjudicated"}
_LABEL_STATUSES = {"confirmed", "excluded", "unresolved"}


@dataclass(frozen=True, order=True)
class FindingKey:
    """Stable identity used for exact matching; display fields do not affect equality."""

    case_id: str
    finding_class: str
    match_key: str
    rule_id: str = field(compare=False)
    target_ref: str | None = field(default=None, compare=False)
    element_guid: str | None = field(default=None, compare=False)

    def as_dict(self) -> dict[str, str | None]:
        return {
            "case_id": self.case_id,
            "finding_class": self.finding_class,
            "match_key": self.match_key,
            "rule_id": self.rule_id,
            "target_ref": self.target_ref,
            "element_guid": self.element_guid,
        }


@dataclass(frozen=True)
class MetricCounts:
    tp: int
    fp: int
    fn: int

    @property
    def precision(self) -> float:
        denominator = self.tp + self.fp
        if denominator:
            return self.tp / denominator
        return 1.0 if self.fn == 0 else 0.0

    @property
    def recall(self) -> float:
        denominator = self.tp + self.fn
        return self.tp / denominator if denominator else 1.0

    @property
    def f1(self) -> float:
        denominator = self.precision + self.recall
        return 2 * self.precision * self.recall / denominator if denominator else 0.0

    def as_dict(self) -> dict[str, int | float]:
        return {
            "tp": self.tp,
            "fp": self.fp,
            "fn": self.fn,
            "precision": round(self.precision, 6),
            "recall": round(self.recall, 6),
            "f1": round(self.f1, 6),
        }


@dataclass(frozen=True)
class ParsedLabels:
    dataset_id: str
    dataset_status: str
    scope_reference: str | None
    expected: frozenset[FindingKey]
    excluded_count: int
    unresolved_count: int
    publishable_protocol_gate: bool
    adjudicator_count: int


@dataclass(frozen=True)
class ParsedDetections:
    run_id: str
    findings: frozenset[FindingKey]


def evaluate_detection_precision(
    labels_path: Path,
    detections_path: Path,
    *,
    require_publishable: bool = False,
) -> dict[str, object]:
    """Evaluate exact finding identities and return a deterministic JSON-ready report."""

    labels_payload = _load_json(labels_path, artifact="labels")
    detections_payload = _load_json(detections_path, artifact="detections")
    labels = _parse_labels(labels_payload, require_publishable=require_publishable)
    detections = _parse_detections(detections_payload)

    true_positives = labels.expected & detections.findings
    false_positives = detections.findings - labels.expected
    false_negatives = labels.expected - detections.findings
    micro = MetricCounts(
        tp=len(true_positives),
        fp=len(false_positives),
        fn=len(false_negatives),
    )

    classes = sorted(
        {item.finding_class for item in labels.expected | detections.findings}
    )
    per_class: dict[str, dict[str, int | float]] = {}
    class_counts: list[MetricCounts] = []
    for finding_class in classes:
        counts = MetricCounts(
            tp=sum(item.finding_class == finding_class for item in true_positives),
            fp=sum(item.finding_class == finding_class for item in false_positives),
            fn=sum(item.finding_class == finding_class for item in false_negatives),
        )
        class_counts.append(counts)
        per_class[finding_class] = counts.as_dict()

    if class_counts:
        macro = {
            "precision": round(
                sum(counts.precision for counts in class_counts) / len(class_counts), 6
            ),
            "recall": round(
                sum(counts.recall for counts in class_counts) / len(class_counts), 6
            ),
            "f1": round(sum(counts.f1 for counts in class_counts) / len(class_counts), 6),
            "class_count": len(class_counts),
        }
    else:
        macro = {"precision": 1.0, "recall": 1.0, "f1": 1.0, "class_count": 0}

    warning = None
    if labels.dataset_status != "adjudicated":
        warning = (
            "Dataset is not adjudicated customer evidence; metrics are harness/fixture "
            "results and must not be published as AeroBIM product accuracy."
        )

    return {
        "artifact_type": "aerobim_detection_precision_evaluation",
        "schema_version": _SCHEMA_VERSION,
        "dataset_id": labels.dataset_id,
        "dataset_status": labels.dataset_status,
        "scope_reference": labels.scope_reference,
        "run_id": detections.run_id,
        "matching_policy": "exact-v1",
        "publishable_protocol_gate": labels.publishable_protocol_gate,
        "adjudicator_count": labels.adjudicator_count,
        "labels": {
            "confirmed": len(labels.expected),
            "excluded": labels.excluded_count,
            "unresolved": labels.unresolved_count,
        },
        "detections": len(detections.findings),
        "micro": micro.as_dict(),
        "macro": macro,
        "per_class": per_class,
        "false_positives": [item.as_dict() for item in sorted(false_positives)],
        "false_negatives": [item.as_dict() for item in sorted(false_negatives)],
        "warning": warning,
    }


def threshold_failures(
    report: dict[str, object],
    *,
    min_precision: float | None = None,
    min_recall: float | None = None,
    min_f1: float | None = None,
) -> list[str]:
    """Return stable human-readable threshold failures for CI gating."""

    micro = report.get("micro")
    if not isinstance(micro, dict):
        raise ValueError("Evaluation report is missing micro metrics")
    failures: list[str] = []
    thresholds = {
        "precision": min_precision,
        "recall": min_recall,
        "f1": min_f1,
    }
    for metric, threshold in thresholds.items():
        if threshold is None:
            continue
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"{metric} threshold must be in [0, 1]")
        actual = float(micro[metric])
        if actual < threshold:
            failures.append(f"micro {metric} {actual:.6f} < required {threshold:.6f}")
    return failures


def _load_json(path: Path, *, artifact: str) -> dict[str, Any]:
    if path.is_symlink():
        raise ValueError(f"Symlinked {artifact} input is not accepted: {path}")
    if not path.exists():
        raise FileNotFoundError(path)
    if not path.is_file():
        raise ValueError(f"{artifact.capitalize()} path is not a regular file: {path}")
    size = path.stat().st_size
    if size > _MAX_INPUT_BYTES:
        raise ValueError(
            f"{artifact.capitalize()} input exceeds {_MAX_INPUT_BYTES} bytes: {path}"
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid UTF-8 JSON {artifact} input: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{artifact.capitalize()} root must be a JSON object")
    if payload.get("schema_version") != _SCHEMA_VERSION:
        raise ValueError(
            f"{artifact.capitalize()} schema_version must be {_SCHEMA_VERSION!r}"
        )
    return payload


def _parse_labels(
    payload: dict[str, Any],
    *,
    require_publishable: bool,
) -> ParsedLabels:
    dataset_id = _required_string(payload, "dataset_id")
    dataset_status = _required_string(payload, "dataset_status").lower()
    if dataset_status not in _DATASET_STATUSES:
        raise ValueError(
            f"Unsupported dataset_status {dataset_status!r}; "
            f"expected one of {sorted(_DATASET_STATUSES)}"
        )
    scope_reference = _optional_string(payload.get("scope_reference"), "scope_reference")
    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("Labels cases must be a non-empty array")

    expected: set[FindingKey] = set()
    excluded_count = 0
    unresolved_count = 0
    total_items = 0
    seen_case_ids: set[str] = set()
    for case_index, case in enumerate(raw_cases):
        if not isinstance(case, dict):
            raise ValueError(f"labels.cases[{case_index}] must be an object")
        case_id = _required_string(case, "case_id", prefix=f"labels.cases[{case_index}].")
        if case_id in seen_case_ids:
            raise ValueError(f"Duplicate labels case_id: {case_id}")
        seen_case_ids.add(case_id)
        raw_findings = case.get("expected_findings")
        if not isinstance(raw_findings, list):
            raise ValueError(f"labels case {case_id!r} expected_findings must be an array")
        for finding_index, finding in enumerate(raw_findings):
            total_items += 1
            if total_items > _MAX_FINDINGS:
                raise ValueError(f"Labels exceed maximum of {_MAX_FINDINGS} findings")
            if not isinstance(finding, dict):
                raise ValueError(
                    f"labels case {case_id!r} finding[{finding_index}] must be an object"
                )
            status = str(finding.get("adjudication_status", "confirmed")).lower()
            if status not in _LABEL_STATUSES:
                raise ValueError(
                    f"Unsupported adjudication_status {status!r} in labels case {case_id!r}"
                )
            key = _parse_finding(finding, case_id=case_id, source="labels")
            if status == "excluded":
                excluded_count += 1
                continue
            if status == "unresolved":
                unresolved_count += 1
                continue
            if key in expected:
                raise ValueError(
                    f"Duplicate confirmed label identity in case {case_id!r}: {key.match_key}"
                )
            expected.add(key)

    publishable_gate, adjudicator_count = _validate_adjudication_protocol(
        payload,
        dataset_status=dataset_status,
        scope_reference=scope_reference,
        unresolved_count=unresolved_count,
    )
    if require_publishable and not publishable_gate:
        raise ValueError(
            "Labels do not satisfy the publishable adjudication protocol gate: "
            "status=adjudicated, scope_reference, two adjudicators, timezone-aware "
            "completion time, and zero unresolved labels are required"
        )
    return ParsedLabels(
        dataset_id=dataset_id,
        dataset_status=dataset_status,
        scope_reference=scope_reference,
        expected=frozenset(expected),
        excluded_count=excluded_count,
        unresolved_count=unresolved_count,
        publishable_protocol_gate=publishable_gate,
        adjudicator_count=adjudicator_count,
    )


def _parse_detections(payload: dict[str, Any]) -> ParsedDetections:
    run_id = _required_string(payload, "run_id")
    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, list):
        raise ValueError("Detections cases must be an array")
    findings: set[FindingKey] = set()
    total_items = 0
    seen_case_ids: set[str] = set()
    for case_index, case in enumerate(raw_cases):
        if not isinstance(case, dict):
            raise ValueError(f"detections.cases[{case_index}] must be an object")
        case_id = _required_string(
            case, "case_id", prefix=f"detections.cases[{case_index}]."
        )
        if case_id in seen_case_ids:
            raise ValueError(f"Duplicate detections case_id: {case_id}")
        seen_case_ids.add(case_id)
        raw_findings = case.get("findings")
        if not isinstance(raw_findings, list):
            raise ValueError(f"detections case {case_id!r} findings must be an array")
        for finding_index, finding in enumerate(raw_findings):
            total_items += 1
            if total_items > _MAX_FINDINGS:
                raise ValueError(f"Detections exceed maximum of {_MAX_FINDINGS} findings")
            if not isinstance(finding, dict):
                raise ValueError(
                    f"detections case {case_id!r} finding[{finding_index}] must be an object"
                )
            key = _parse_finding(finding, case_id=case_id, source="detections")
            if key in findings:
                raise ValueError(
                    f"Duplicate detection identity in case {case_id!r}: {key.match_key}"
                )
            findings.add(key)
    return ParsedDetections(run_id=run_id, findings=frozenset(findings))


def _parse_finding(
    payload: dict[str, Any],
    *,
    case_id: str,
    source: str,
) -> FindingKey:
    finding_class = _required_string(payload, "finding_class", prefix=f"{source}.").lower()
    rule_id = _required_string(payload, "rule_id", prefix=f"{source}.")
    target_ref = _optional_string(payload.get("target_ref"), f"{source}.target_ref")
    element_guid = _optional_string(payload.get("element_guid"), f"{source}.element_guid")
    explicit_match_key = _optional_string(payload.get("match_key"), f"{source}.match_key")
    if explicit_match_key is None and target_ref is None and element_guid is None:
        raise ValueError(
            f"{source} finding {rule_id!r} requires match_key, target_ref, or element_guid"
        )
    if explicit_match_key is not None:
        match_key = f"explicit:{explicit_match_key}"
    else:
        match_key = "composite:" + json.dumps(
            [rule_id, target_ref or "", element_guid or ""],
            ensure_ascii=False,
            separators=(",", ":"),
        )
    return FindingKey(
        case_id=case_id,
        finding_class=finding_class,
        match_key=match_key,
        rule_id=rule_id,
        target_ref=target_ref,
        element_guid=element_guid,
    )


def _validate_adjudication_protocol(
    payload: dict[str, Any],
    *,
    dataset_status: str,
    scope_reference: str | None,
    unresolved_count: int,
) -> tuple[bool, int]:
    raw_adjudication = payload.get("adjudication")
    if not isinstance(raw_adjudication, dict):
        return False, 0
    raw_adjudicators = raw_adjudication.get("adjudicators")
    if not isinstance(raw_adjudicators, list):
        return False, 0
    adjudicator_ids: set[str] = set()
    for item in raw_adjudicators:
        if not isinstance(item, dict):
            continue
        raw_id = item.get("id")
        if isinstance(raw_id, str) and raw_id.strip():
            adjudicator_ids.add(raw_id.strip())
    completed_at = raw_adjudication.get("completed_at")
    completed_with_timezone = False
    if isinstance(completed_at, str):
        try:
            parsed = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
            completed_with_timezone = parsed.tzinfo is not None
        except ValueError:
            completed_with_timezone = False
    method = raw_adjudication.get("method")
    return (
        dataset_status == "adjudicated"
        and scope_reference is not None
        and len(adjudicator_ids) >= 2
        and completed_with_timezone
        and method in {"consensus", "majority-with-resolution"}
        and unresolved_count == 0,
        len(adjudicator_ids),
    )


def _required_string(
    payload: dict[str, Any],
    key: str,
    *,
    prefix: str = "",
) -> str:
    value = _optional_string(payload.get(key), f"{prefix}{key}")
    if value is None:
        raise ValueError(f"{prefix}{key} must be a non-empty string")
    return value


def _optional_string(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string when provided")
    normalized = value.strip()
    if len(normalized) > 1024:
        raise ValueError(f"{field_name} exceeds 1024 characters")
    return normalized


def _write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate exact-match TP/FP/FN for labeled AeroBIM findings"
    )
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--detections", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--min-precision", type=float)
    parser.add_argument("--min-recall", type=float)
    parser.add_argument("--min-f1", type=float)
    parser.add_argument(
        "--require-publishable",
        action="store_true",
        help="Reject datasets that do not pass the two-adjudicator protocol gate",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = evaluate_detection_precision(
        args.labels,
        args.detections,
        require_publishable=args.require_publishable,
    )
    failures = threshold_failures(
        report,
        min_precision=args.min_precision,
        min_recall=args.min_recall,
        min_f1=args.min_f1,
    )
    report["gate"] = {
        "passed": not failures,
        "failures": failures,
        "thresholds": {
            "min_precision": args.min_precision,
            "min_recall": args.min_recall,
            "min_f1": args.min_f1,
        },
    }
    if args.output is not None:
        _write_json_atomic(args.output, report)
    micro = report["micro"]
    print(
        json.dumps(
            {
                "dataset_id": report["dataset_id"],
                "run_id": report["run_id"],
                "micro": micro,
                "gate_passed": not failures,
                "warning": report["warning"],
            },
            ensure_ascii=False,
        )
    )
    return 2 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
