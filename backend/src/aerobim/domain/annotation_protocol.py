"""
P1-H: Double Annotation Protocol.

Annotator A + Annotator B → Disagreement → Adjudicator → Gold.

Raw labels are never deleted. Disagreement is preserved.
Cohen's kappa calculated where applicable.
Protocol document is SSOT (see docs/evaluation/annotation-protocol.md).

Reduces: evaluation gap, audit risk.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class AnnotationLabel(StrEnum):
    """Compliance verdict label from a human annotator."""

    PASS = "PASS"  # noqa: S105
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_VERIFIABLE = "NOT_VERIFIABLE"  # Insufficient info in provided materials
    AMBIGUOUS = "AMBIGUOUS"  # Annotator uncertain; flags for adjudicator


class AdjudicationOutcome(StrEnum):
    AGREED_WITH_A = "agreed_with_a"
    AGREED_WITH_B = "agreed_with_b"
    NEW_GOLD = "new_gold"  # Adjudicator reached independent conclusion
    UNRESOLVABLE = "unresolvable"  # Flagged for protocol committee


@dataclass
class Annotation:
    """Single annotator's label for one evaluation case."""

    annotation_id: str
    case_id: str  # Evaluation case identifier
    annotator_id: str  # Anonymised or named reviewer ID
    label: AnnotationLabel
    confidence: float  # 0-1; required
    reasoning: str  # Brief justification (stored, never deleted)
    evidence_refs: list[str]  # Which materials were examined
    timestamp: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    session_id: str | None = None  # Annotation session for reproducibility

    def to_dict(self) -> dict[str, Any]:
        return {
            "annotation_id": self.annotation_id,
            "case_id": self.case_id,
            "annotator_id": self.annotator_id,
            "label": self.label.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "evidence_refs": self.evidence_refs,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
        }


@dataclass
class Adjudication:
    """Resolution of a disagreement between two annotators."""

    adjudication_id: str
    case_id: str
    annotation_a_id: str
    annotation_b_id: str
    adjudicator_id: str
    outcome: AdjudicationOutcome
    gold_label: AnnotationLabel
    reasoning: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(tz=UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "adjudication_id": self.adjudication_id,
            "case_id": self.case_id,
            "annotation_a_id": self.annotation_a_id,
            "annotation_b_id": self.annotation_b_id,
            "adjudicator_id": self.adjudicator_id,
            "outcome": self.outcome.value,
            "gold_label": self.gold_label.value,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class AnnotationPair:
    """
    Paired annotations for one case from two independent annotators.
    Disagreement is always preserved — never silently merged.
    """

    case_id: str
    annotation_a: Annotation
    annotation_b: Annotation
    adjudication: Adjudication | None = None

    @property
    def is_agreement(self) -> bool:
        return self.annotation_a.label == self.annotation_b.label

    @property
    def gold_label(self) -> AnnotationLabel | None:
        if self.adjudication:
            return self.adjudication.gold_label
        if self.is_agreement:
            return self.annotation_a.label
        return None  # Unresolved disagreement

    @property
    def needs_adjudication(self) -> bool:
        return not self.is_agreement and self.adjudication is None


def compute_cohen_kappa(pairs: list[AnnotationPair]) -> float | None:
    """
    Cohen's kappa for inter-annotator agreement.
    Returns None if fewer than 2 pairs or all same label (kappa undefined).

    Formula: kappa = (p_o - p_e) / (1 - p_e)
      p_o = observed agreement
      p_e = expected agreement by chance
    """
    if len(pairs) < 2:
        return None

    labels = list(AnnotationLabel)
    label_to_idx = {label: index for index, label in enumerate(labels)}
    n = len(pairs)
    n_labels = len(labels)

    # Confusion matrix
    matrix = [[0] * n_labels for _ in range(n_labels)]
    for pair in pairs:
        i = label_to_idx[pair.annotation_a.label]
        j = label_to_idx[pair.annotation_b.label]
        matrix[i][j] += 1

    # Observed agreement
    p_o = sum(matrix[k][k] for k in range(n_labels)) / n

    # Expected agreement
    row_sums = [sum(matrix[i][j] for j in range(n_labels)) for i in range(n_labels)]
    col_sums = [sum(matrix[i][j] for i in range(n_labels)) for j in range(n_labels)]
    p_e = sum(row_sums[k] * col_sums[k] for k in range(n_labels)) / (n * n)

    if p_e >= 1.0:
        return None  # Kappa undefined
    return (p_o - p_e) / (1.0 - p_e)


@dataclass
class AnnotationBatchMetrics:
    """Summary metrics for a batch of annotation pairs."""

    batch_id: str
    corpus_type: str  # PUBLIC / SYNTHETIC / CUSTOMER
    n_cases: int
    n_agreements: int
    n_disagreements: int
    n_adjudicated: int
    n_unresolvable: int
    agreement_rate: float
    cohen_kappa: float | None
    adjudication_rate: float
    disagreement_categories: dict[str, int] = field(default_factory=dict)
    computed_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "corpus_type": self.corpus_type,
            "n_cases": self.n_cases,
            "n_agreements": self.n_agreements,
            "n_disagreements": self.n_disagreements,
            "n_adjudicated": self.n_adjudicated,
            "n_unresolvable": self.n_unresolvable,
            "agreement_rate": self.agreement_rate,
            "cohen_kappa": self.cohen_kappa,
            "adjudication_rate": self.adjudication_rate,
            "disagreement_categories": self.disagreement_categories,
            "computed_at": self.computed_at.isoformat(),
        }


def compute_batch_metrics(
    batch_id: str, corpus_type: str, pairs: list[AnnotationPair]
) -> AnnotationBatchMetrics:
    n = len(pairs)
    agreements = [p for p in pairs if p.is_agreement]
    disagreements = [p for p in pairs if not p.is_agreement]
    adjudicated = [p for p in disagreements if p.adjudication is not None]
    unresolvable = [
        p
        for p in adjudicated
        if p.adjudication and p.adjudication.outcome == AdjudicationOutcome.UNRESOLVABLE
    ]

    # Disagreement categories: label_a vs label_b
    disagree_cats: dict[str, int] = {}
    for p in disagreements:
        key = f"{p.annotation_a.label.value}_vs_{p.annotation_b.label.value}"
        disagree_cats[key] = disagree_cats.get(key, 0) + 1

    return AnnotationBatchMetrics(
        batch_id=batch_id,
        corpus_type=corpus_type,
        n_cases=n,
        n_agreements=len(agreements),
        n_disagreements=len(disagreements),
        n_adjudicated=len(adjudicated),
        n_unresolvable=len(unresolvable),
        agreement_rate=len(agreements) / n if n else 0.0,
        cohen_kappa=compute_cohen_kappa(pairs),
        adjudication_rate=len(adjudicated) / len(disagreements) if disagreements else 1.0,
        disagreement_categories=disagree_cats,
    )
