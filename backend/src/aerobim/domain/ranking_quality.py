"""Tie-aware ranking quality (nDCG) for reviewer priority ordering.

Academic grounding (Jul 2026 practice):

- **nDCG** (Jarvelin & Kekalainen 2002) with logarithmic discount — Wang et
  al. 2013 (COLT) show the log discount yields consistent distinguishability
  among ranking functions; Valcarce et al. find nDCG offers the best
  discriminative power among common IR metrics; Fuhr 2018 catalogues why
  MRR/ERR are unsound alternatives (violate basic metric requirements).
- **Exponential gain** ``2^rel - 1`` (Burges et al. 2005; MSLR/LETOR
  convention) for graded relevance 0/1/2 per the TZ v2 harness spec.
- **Tie-aware expected DCG** (McSherry & Najork, ECIR 2008): AeroBIM
  priorities are deterministic integer scores, so ties are the norm, not the
  exception. Naive sorting silently rewards arbitrary within-tie order; the
  expected-DCG closed form scores each tie group by its mean gain times the
  sum of discounts over the positions the group occupies — deterministic and
  permutation-invariant under tied scores.
- **Undefined cases fail closed**: an all-irrelevant case has IDCG = 0 and
  carries no ranking signal; scoring it 0 punishes and 1 rewards — both
  wrong — so such cases are excluded and counted explicitly (sklearn's
  silent 0 is a known pitfall).

Claim boundary: ranking quality on fixtures never upgrades to customer
evidence (RT-001); nDCG orders review effort, it never changes severities or
``summary.passed``.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

_GAIN_FNS = {
    "exponential": lambda rel: float((1 << int(rel)) - 1),
    "linear": float,
}


@dataclass(frozen=True)
class RankedItem:
    """One finding in a predicted ranking with its adjudicated grade."""

    item_id: str
    score: float
    """Predicted priority (higher = earlier in review order)."""
    relevance: int
    """Graded relevance 0/1/2 from adjudicated labels."""


@dataclass(frozen=True)
class NdcgResult:
    """Tie-aware expected nDCG@k for one case (document/package)."""

    ndcg: float
    dcg: float
    idcg: float
    k: int | None
    n_items: int
    tie_group_count: int
    defined: bool
    """False when IDCG == 0 (all-irrelevant case) — excluded from means."""
    gain: str
    method: str = "tie_aware_expected_ndcg"

    def as_dict(self) -> dict[str, object]:
        return {
            "ndcg": round(self.ndcg, 6),
            "dcg": round(self.dcg, 6),
            "idcg": round(self.idcg, 6),
            "k": self.k,
            "n_items": self.n_items,
            "tie_group_count": self.tie_group_count,
            "defined": self.defined,
            "gain": self.gain,
            "method": self.method,
        }


def _discount(position: int) -> float:
    """1 / log2(position + 1) with 1-based positions (Jarvelin & Kekalainen)."""

    return 1.0 / math.log2(position + 1)


def tie_aware_ndcg(
    items: Sequence[RankedItem],
    *,
    k: int | None = None,
    gain: str = "exponential",
) -> NdcgResult:
    """Expected nDCG@k under random within-tie permutation (McSherry-Najork).

    Items are grouped by exact predicted score (descending). A tie group
    occupying positions p..q contributes ``mean(gains) * sum(discounts p..q)``
    — the closed-form expectation over all within-group orderings. With a
    cutoff ``k`` the group straddling the cutoff contributes only the
    discounts of positions <= k (its expected gain per position is
    unchanged). IDCG uses the same gain on grades sorted descending.
    """

    if gain not in _GAIN_FNS:
        raise ValueError(f"unknown gain {gain!r}")
    if k is not None and k <= 0:
        raise ValueError("k must be positive when provided")
    if not items:
        raise ValueError("tie_aware_ndcg requires at least one item")
    for item in items:
        if item.relevance < 0:
            raise ValueError(f"negative relevance for {item.item_id!r}")
        if not math.isfinite(item.score):
            # RT-B: NaN scores break both sorting and tie-group equality,
            # silently destroying permutation invariance — fail closed.
            raise ValueError(f"non-finite score for {item.item_id!r}")

    gain_fn = _GAIN_FNS[gain]
    cutoff = len(items) if k is None else min(k, len(items))

    # Ideal DCG: grades sorted descending (tie order is irrelevant — the
    # gain multiset per position prefix is identical for any tie-break).
    ideal_gains = sorted((gain_fn(item.relevance) for item in items), reverse=True)
    idcg = sum(g * _discount(pos) for pos, g in enumerate(ideal_gains[:cutoff], start=1))

    # Predicted ranking: group by exact score, descending.
    ordered = sorted(items, key=lambda item: -item.score)
    tie_groups: list[list[RankedItem]] = []
    for item in ordered:
        if tie_groups and tie_groups[-1][0].score == item.score:
            tie_groups[-1].append(item)
        else:
            tie_groups.append([item])

    dcg = 0.0
    position = 1
    for group in tie_groups:
        group_positions = range(position, position + len(group))
        mean_gain = sum(gain_fn(item.relevance) for item in group) / len(group)
        dcg += mean_gain * sum(_discount(pos) for pos in group_positions if pos <= cutoff)
        position += len(group)

    defined = idcg > 0.0
    return NdcgResult(
        ndcg=(dcg / idcg) if defined else 0.0,
        dcg=dcg,
        idcg=idcg,
        k=k,
        n_items=len(items),
        tie_group_count=len(tie_groups),
        defined=defined,
        gain=gain,
    )
