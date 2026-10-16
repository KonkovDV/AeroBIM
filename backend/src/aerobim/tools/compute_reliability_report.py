"""K2A-P1-03: reliability (calibration) report — unpublishable by default.

Equal-mass bins, per-bin Wilson CI, ECE, and the Brier score
``(1/n) Σ (f_i − o_i)²``. Fail-closed: hidden/customer
splits are rejected for a non-customer corpus; ``publishable`` is true only
for ``corpus_kind == "customer"`` with sufficient n. Small n => status
``uncalibrated`` and no ECE/thresholds are declared.

Claim boundary: never claim calibrated thresholds or product accuracy from
fixture/synthetic corpora (RT-001). Numbers are internal diagnostics only.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from aerobim.domain.eval_statistics import brier_score
from aerobim.domain.study_design import wilson_interval

CLAIM_BOUNDARY = (
    "Internal reliability diagnostic. Not a customer accuracy claim (RT-001); "
    "thresholds are NOT calibrated unless status=calibrated and publishable=true."
)
MIN_N = 100
FORBIDDEN_SPLITS = frozenset({"hidden", "customer", "holdout_customer"})
CORPUS_KINDS = frozenset({"fixture", "synthetic", "pilot", "customer"})


def build_reliability_report(
    scores: Sequence[float],
    labels: Sequence[int],
    *,
    corpus_kind: str,
    split: str = "dev",
    bins: int = 10,
) -> dict[str, Any]:
    if corpus_kind not in CORPUS_KINDS:
        raise ValueError(f"unknown corpus_kind: {corpus_kind}")
    if split in FORBIDDEN_SPLITS and corpus_kind != "customer":
        raise ValueError(f"split {split!r} is forbidden for corpus_kind={corpus_kind}")
    if len(scores) != len(labels):
        raise ValueError("scores and labels length mismatch")
    if any(not 0.0 <= s <= 1.0 for s in scores) or any(y not in (0, 1) for y in labels):
        raise ValueError("scores must be in [0,1], labels in {0,1}")
    n = len(scores)
    base: dict[str, Any] = {
        "n": n,
        "corpus_kind": corpus_kind,
        "split": split,
        "binning": "equal_mass",
        "claim_boundary": CLAIM_BOUNDARY,
        "min_n": MIN_N,
    }
    if n < MIN_N:
        return {
            **base,
            "status": "uncalibrated",
            "reason": "insufficient_data",
            "bins": [],
            "ece": None,
            "brier": None,
            "publishable": False,
        }
    pairs = sorted(zip(scores, labels, strict=True))
    k = max(1, min(bins, n))
    out_bins: list[dict[str, Any]] = []
    ece = 0.0
    for i in range(k):
        chunk = pairs[i * n // k : (i + 1) * n // k]
        if not chunk:
            continue
        m = len(chunk)
        pos = sum(y for _, y in chunk)
        conf = sum(s for s, _ in chunk) / m
        acc = pos / m
        ci = wilson_interval(pos, m)
        ece += m / n * abs(acc - conf)
        out_bins.append(
            {
                "lo": round(chunk[0][0], 6),
                "hi": round(chunk[-1][0], 6),
                "count": m,
                "mean_confidence": round(conf, 6),
                "accuracy": round(acc, 6),
                "wilson_lower": round(ci.lower, 6),
                "wilson_upper": round(ci.upper, 6),
            }
        )
    return {
        **base,
        "status": "calibrated" if corpus_kind == "customer" else "diagnostic_only",
        "bins": out_bins,
        "ece": round(ece, 6),
        "brier": round(brier_score(scores, labels), 6),
        "publishable": corpus_kind == "customer",
    }


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path, help='JSON: {"scores": [...], "labels": [...]}')
    p.add_argument("--corpus-kind", required=True)
    p.add_argument("--split", default="dev")
    p.add_argument("--out", type=Path)
    a = p.parse_args(argv)
    data = json.loads(a.input.read_text(encoding="utf-8"))
    rep = build_reliability_report(
        data["scores"], data["labels"], corpus_kind=a.corpus_kind, split=a.split
    )
    text = json.dumps(rep, ensure_ascii=False, indent=2) + "\n"
    if a.out:
        a.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
