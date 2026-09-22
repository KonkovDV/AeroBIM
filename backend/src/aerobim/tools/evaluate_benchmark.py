"""
P1-G: Evaluation Harness — Full Benchmark Framework.

Structure:
  dataset → case → input → gold → prediction → evidence → annotation
  → adjudication → metrics

Metrics (all required; FN must NEVER be hidden in aggregate accuracy):
  precision, recall, F1, FP, FN, support
  per-rule, per-error-class, micro, macro
  abstention rate, NOT_VERIFIED rate, confidence intervals

Leakage protection (P1-J):
  - Development fixtures ≠ evaluation test cases
  - Immutable test manifest with case hashes
  - New dataset version required for any change

Corpus split (P1-I): PUBLIC / SYNTHETIC / CUSTOMER — never merged.

customer_go=false until external customer sign-off. fixture success != production claim.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class CorpusType(str, Enum):
    PUBLIC = "PUBLIC"       # External public BIM/ACC datasets
    SYNTHETIC = "SYNTHETIC" # AeroBIM-generated synthetic cases
    CUSTOMER = "CUSTOMER"   # Real customer data (not in Git)


class PredictionLabel(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_VERIFIED = "NOT_VERIFIED"  # System chose not to decide; unknown != pass
    ERROR = "ERROR"                # System error during check


@dataclass
class BenchmarkCase:
    """
    A single evaluation case.

    case_hash = sha256(input_hash + gold_label + rule_id + corpus_type).
    Immutable after inclusion in a manifest.
    Same case_hash in multiple manifest versions = same case.
    """
    case_id: str
    case_hash: str          # Computed; tampering invalidates manifest
    rule_id: str
    corpus_type: CorpusType
    input_hash: str         # sha256 of input file(s)
    gold_label: PredictionLabel  # Ground truth from annotation/adjudication
    gold_source: str        # "annotator", "adjudicator", "expert"
    description: str
    tags: list[str] = field(default_factory=list)
    is_held_out: bool = False   # True = never seen during development

    @staticmethod
    def compute_case_hash(
        input_hash: str,
        gold_label: str,
        rule_id: str,
        corpus_type: str,
    ) -> str:
        payload = f"{input_hash}|{gold_label}|{rule_id}|{corpus_type}".encode()
        return hashlib.sha256(payload).hexdigest()[:24]

    def validate_hash(self) -> bool:
        expected = self.compute_case_hash(
            self.input_hash, self.gold_label.value,
            self.rule_id, self.corpus_type.value,
        )
        return self.case_hash == expected


@dataclass
class BenchmarkDatasetManifest:
    """
    Immutable test manifest. Changes require new version.
    manifest_hash seals all case hashes — leakage detectable.
    """
    manifest_id: str
    version: str
    corpus_type: CorpusType
    created_at: str             # ISO date
    created_by: str
    cases: list[BenchmarkCase]
    manifest_hash: str = ""     # Sealed on finalise()
    change_reason: str = ""     # Required when creating new version

    def finalise(self) -> "BenchmarkDatasetManifest":
        case_hashes = sorted(c.case_hash for c in self.cases)
        payload = json.dumps(
            {"manifest_id": self.manifest_id, "version": self.version,
             "corpus_type": self.corpus_type.value, "case_hashes": case_hashes},
            sort_keys=True,
        ).encode()
        self.manifest_hash = hashlib.sha256(payload).hexdigest()
        return self

    def verify_integrity(self) -> tuple[bool, list[str]]:
        """Check manifest_hash and all case_hashes. Returns (ok, error_list)."""
        errors: list[str] = []
        for case in self.cases:
            if not case.validate_hash():
                errors.append(f"Case {case.case_id}: hash mismatch (tampered?)")
        # Re-check manifest hash
        case_hashes = sorted(c.case_hash for c in self.cases)
        payload = json.dumps(
            {"manifest_id": self.manifest_id, "version": self.version,
             "corpus_type": self.corpus_type.value, "case_hashes": case_hashes},
            sort_keys=True,
        ).encode()
        computed = hashlib.sha256(payload).hexdigest()
        if computed != self.manifest_hash:
            errors.append("Manifest hash mismatch (cases changed without new version?)")
        return len(errors) == 0, errors


@dataclass
class CasePrediction:
    """System's prediction for a single benchmark case."""
    case_id: str
    rule_id: str
    prediction: PredictionLabel
    confidence: Optional[float]   # 0-1; None if system didn't produce confidence
    engine_version: str
    norm_pack_hash: str
    run_id: str                   # Unique benchmark run ID
    is_ai_advisory: bool
    evidence_count: int


@dataclass
class RuleMetrics:
    """
    Per-rule precision/recall/F1/FP/FN.
    FN is always reported separately — never hidden in aggregate.
    """
    rule_id: str
    corpus_type: CorpusType
    n_total: int
    tp: int
    fp: int
    tn: int
    fn: int
    n_abstained: int        # NOT_VERIFIED predictions
    n_errors: int           # ERROR predictions

    @property
    def precision(self) -> Optional[float]:
        denom = self.tp + self.fp
        return self.tp / denom if denom else None

    @property
    def recall(self) -> Optional[float]:
        """Also called True Positive Rate. FN exposed explicitly."""
        denom = self.tp + self.fn
        return self.tp / denom if denom else None

    @property
    def f1(self) -> Optional[float]:
        p, r = self.precision, self.recall
        if p is None or r is None or (p + r) == 0:
            return None
        return 2 * p * r / (p + r)

    @property
    def false_negative_rate(self) -> Optional[float]:
        """FNR = FN / (FN + TP). Critical for compliance: must not be hidden."""
        denom = self.fn + self.tp
        return self.fn / denom if denom else None

    @property
    def abstention_rate(self) -> float:
        return self.n_abstained / self.n_total if self.n_total else 0.0

    @property
    def not_verified_rate(self) -> float:
        return self.abstention_rate

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "corpus_type": self.corpus_type.value,
            "n_total": self.n_total,
            "tp": self.tp, "fp": self.fp,
            "tn": self.tn, "fn": self.fn,
            "n_abstained": self.n_abstained,
            "n_errors": self.n_errors,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "false_negative_rate": self.false_negative_rate,
            "abstention_rate": self.abstention_rate,
        }


@dataclass
class BenchmarkRunResult:
    """
    Full benchmark run results.
    Always broken down by corpus_type. Never merge PUBLIC+SYNTHETIC+CUSTOMER.
    """
    run_id: str
    manifest_id: str
    manifest_version: str
    corpus_type: CorpusType
    engine_version: str
    norm_pack_hash: str
    run_at: datetime
    per_rule: list[RuleMetrics]
    n_total: int
    n_abstained: int
    n_errors: int

    # Aggregate (macro avg over rules; never used to hide FN)
    macro_precision: Optional[float] = None
    macro_recall: Optional[float] = None
    macro_f1: Optional[float] = None
    micro_precision: Optional[float] = None
    micro_recall: Optional[float] = None
    micro_f1: Optional[float] = None
    macro_fn_rate: Optional[float] = None  # Average FNR across rules

    def compute_aggregates(self) -> None:
        """Compute macro and micro aggregates from per-rule metrics."""
        rules = [r for r in self.per_rule if r.precision is not None]
        if rules:
            self.macro_precision = sum(r.precision for r in rules if r.precision) / len(rules)
            self.macro_recall = sum(r.recall for r in rules if r.recall) / len(rules)
            self.macro_f1 = sum(r.f1 for r in rules if r.f1) / len(rules)
            fnrs = [r.false_negative_rate for r in rules if r.false_negative_rate is not None]
            self.macro_fn_rate = sum(fnrs) / len(fnrs) if fnrs else None

        # Micro: global TP/FP/FN
        tp = sum(r.tp for r in self.per_rule)
        fp = sum(r.fp for r in self.per_rule)
        fn = sum(r.fn for r in self.per_rule)
        if tp + fp:
            self.micro_precision = tp / (tp + fp)
        if tp + fn:
            self.micro_recall = tp / (tp + fn)
        if self.micro_precision and self.micro_recall:
            p, r = self.micro_precision, self.micro_recall
            if p + r:
                self.micro_f1 = 2 * p * r / (p + r)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "manifest_id": self.manifest_id,
            "manifest_version": self.manifest_version,
            "corpus_type": self.corpus_type.value,
            "engine_version": self.engine_version,
            "norm_pack_hash": self.norm_pack_hash,
            "run_at": self.run_at.isoformat(),
            "n_total": self.n_total,
            "n_abstained": self.n_abstained,
            "n_errors": self.n_errors,
            "abstention_rate": self.n_abstained / self.n_total if self.n_total else 0,
            "macro_precision": self.macro_precision,
            "macro_recall": self.macro_recall,
            "macro_f1": self.macro_f1,
            "macro_fn_rate": self.macro_fn_rate,
            "micro_precision": self.micro_precision,
            "micro_recall": self.micro_recall,
            "micro_f1": self.micro_f1,
            "per_rule": [r.to_dict() for r in self.per_rule],
        }


def evaluate_predictions(
    manifest: BenchmarkDatasetManifest,
    predictions: list[CasePrediction],
    engine_version: str,
    norm_pack_hash: str,
) -> BenchmarkRunResult:
    """
    Compute per-rule and aggregate metrics.
    Enforces: leakage protection, corpus type separation, FN visibility.
    """
    import uuid

    # Verify manifest integrity before evaluation
    ok, errors = manifest.verify_integrity()
    if not ok:
        raise ValueError(
            f"Benchmark manifest integrity check failed: {errors}. "
            "Refusing to evaluate against tampered manifest."
        )

    case_map = {c.case_id: c for c in manifest.cases}
    pred_map = {p.case_id: p for p in predictions}

    # Per-rule accumulation
    rule_counters: dict[str, dict] = {}
    total_abstained = 0
    total_errors = 0

    for case in manifest.cases:
        pred = pred_map.get(case.case_id)
        if pred is None:
            # Missing prediction treated as abstention
            pred_label = PredictionLabel.NOT_VERIFIED
        else:
            pred_label = pred.prediction

        rule_id = case.rule_id
        if rule_id not in rule_counters:
            rule_counters[rule_id] = {"tp": 0, "fp": 0, "tn": 0, "fn": 0,
                                      "abstained": 0, "errors": 0, "total": 0}
        c = rule_counters[rule_id]
        c["total"] += 1

        if pred_label == PredictionLabel.NOT_VERIFIED:
            c["abstained"] += 1
            total_abstained += 1
        elif pred_label == PredictionLabel.ERROR:
            c["errors"] += 1
            total_errors += 1
        else:
            gold_is_fail = case.gold_label == PredictionLabel.FAIL
            pred_is_fail = pred_label == PredictionLabel.FAIL
            if gold_is_fail and pred_is_fail:
                c["tp"] += 1
            elif not gold_is_fail and pred_is_fail:
                c["fp"] += 1
            elif gold_is_fail and not pred_is_fail:
                c["fn"] += 1  # <-- FN must be explicitly visible
            else:
                c["tn"] += 1

    per_rule = [
        RuleMetrics(
            rule_id=rule_id,
            corpus_type=manifest.corpus_type,
            n_total=c["total"],
            tp=c["tp"], fp=c["fp"],
            tn=c["tn"], fn=c["fn"],
            n_abstained=c["abstained"],
            n_errors=c["errors"],
        )
        for rule_id, c in rule_counters.items()
    ]

    run_id = str(uuid.uuid4())
    result = BenchmarkRunResult(
        run_id=run_id,
        manifest_id=manifest.manifest_id,
        manifest_version=manifest.version,
        corpus_type=manifest.corpus_type,
        engine_version=engine_version,
        norm_pack_hash=norm_pack_hash,
        run_at=datetime.now(tz=timezone.utc),
        per_rule=per_rule,
        n_total=len(manifest.cases),
        n_abstained=total_abstained,
        n_errors=total_errors,
    )
    result.compute_aggregates()
    return result
