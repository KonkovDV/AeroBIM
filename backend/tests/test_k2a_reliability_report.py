import pytest

from aerobim.domain.eval_statistics import brier_score
from aerobim.tools.compute_reliability_report import build_reliability_report


def _data(n: int) -> tuple[list[float], list[int]]:
    s = [i / (n - 1) for i in range(n)]
    return s, [1 if x > 0.5 else 0 for x in s]


def test_brier_score_matches_the_mean_square() -> None:
    assert brier_score([1.0, 0.0], [1, 0]) == 0.0
    assert brier_score([0.5, 0.5], [1, 0]) == pytest.approx(0.25)


def test_small_n_is_uncalibrated() -> None:
    s, y = _data(20)
    r = build_reliability_report(s, y, corpus_kind="fixture")
    assert r["status"] == "uncalibrated" and r["ece"] is None and r["brier"] is None
    assert r["publishable"] is False


def test_fixture_never_publishable_and_has_bins() -> None:
    s, y = _data(200)
    r = build_reliability_report(s, y, corpus_kind="fixture")
    assert r["publishable"] is False and r["status"] == "diagnostic_only"
    assert len(r["bins"]) == 10 and all(b["count"] == 20 for b in r["bins"])
    assert all(b["wilson_lower"] <= b["accuracy"] <= b["wilson_upper"] for b in r["bins"])
    assert r["claim_boundary"] and r["ece"] is not None
    raw = sum((f - o) ** 2 for f, o in zip(s, y, strict=True)) / len(s)
    assert r["brier"] == round(raw, 6)


@pytest.mark.parametrize("split", ["hidden", "customer"])
def test_forbidden_split_fail_closed(split: str) -> None:
    s, y = _data(200)
    with pytest.raises(ValueError):
        build_reliability_report(s, y, corpus_kind="synthetic", split=split)
