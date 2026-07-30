"""TR-233 guard (Red Team A5): an adversarial / bad / unknown drawing scan must
never assess as auto-readable -- bad or unknown quality is not 'no violations'.

Signal-level fixtures (samples/benchmarks/drawing-quality-adversarial.json): the
system does NOT perform human-level CV (cv_human_level=MISSING). A stamp,
handwriting, or bad scan is modeled through the degraded quality signals it
produces (low dpi, skew, few recognized chars, corrupt NaN/inf, or absent
signals), never by recognizing the stamp itself.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from aerobim.domain.region_quality import (
    RegionQuality,
    RegionQualitySignals,
    assess_region_quality,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_FIXTURES = _REPO_ROOT / "samples" / "benchmarks" / "drawing-quality-adversarial.json"
_NON_FINITE = {"nan": math.nan, "inf": math.inf, "-inf": -math.inf}


def _to_float(value: object) -> float | None:
    if isinstance(value, str):
        return _NON_FINITE[value.strip().lower()]
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _int_or_none(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _signals(raw: dict[str, object]) -> RegionQualitySignals:
    has_text = raw.get("has_text")
    text_chars = raw.get("text_char_count")
    return RegionQualitySignals(
        dpi=_to_float(raw["dpi"]) if "dpi" in raw else None,
        skew_deg=_to_float(raw["skew_deg"]) if "skew_deg" in raw else None,
        has_text=has_text if isinstance(has_text, bool) else None,
        text_char_count=_int_or_none(text_chars),
    )


def _load_cases() -> list[dict[str, object]]:
    data = json.loads(_FIXTURES.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    cases = data["cases"]
    assert isinstance(cases, list) and cases
    return [case for case in cases if isinstance(case, dict)]


def test_adversarial_regions_never_auto_readable() -> None:
    failures: list[str] = []
    for case in _load_cases():
        raw = case["signals"]
        assert isinstance(raw, dict)
        result = assess_region_quality(_signals(raw))
        if result.quality is RegionQuality.READABLE or result.usable_for_auto_read():
            failures.append(
                f"{case.get('id')}: {result.quality} auto_read={result.usable_for_auto_read()}"
            )
    assert not failures, (
        "Adversarial scans assessed as auto-readable (a bad scan is not 'no violations'):\n"
        + "\n".join(failures)
    )


def test_clean_region_is_readable_positive_control() -> None:
    # Proves the guard is not trivially always-fail.
    result = assess_region_quality(
        RegionQualitySignals(dpi=300.0, skew_deg=0.5, has_text=True, text_char_count=80)
    )
    assert result.quality is RegionQuality.READABLE
    assert result.usable_for_auto_read() is True


def test_fixtures_cover_key_adversarial_modes() -> None:
    ids = {str(case.get("id")) for case in _load_cases()}
    for required in ("low-dpi-60-scan", "blank-no-text", "nan-inf-corrupt", "no-signals"):
        assert required in ids, f"missing adversarial fixture: {required}"
