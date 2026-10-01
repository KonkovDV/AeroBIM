"""P-003 guard: adversarial extraction signals must never yield trusted evidence.

'Text not extracted' != 'text absent'; hidden/invisible text never enters the
evidence base unmarked. Signal-level core (no PDF parsing here); fixtures:
samples/benchmarks/extraction-integrity-adversarial.json.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from aerobim.domain.extraction_integrity import (
    ExtractionIntegritySignals,
    ExtractionIntegrityStatus,
    assess_extraction_integrity,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_FIXTURES = _REPO_ROOT / "samples" / "benchmarks" / "extraction-integrity-adversarial.json"
_NON_FINITE = {"nan": math.nan, "inf": math.inf, "-inf": -math.inf}


def _num(value: object) -> int | float | None:
    if isinstance(value, str):
        return _NON_FINITE[value.strip().lower()]
    if isinstance(value, bool) or value is None:
        return None
    assert isinstance(value, int | float)
    return value


def _signals(raw: dict[str, object]) -> ExtractionIntegritySignals:
    rendered = raw.get("rendered_text_present")
    text_digits = raw.get("extracted_digit_runs")
    ocr_digits = raw.get("ocr_digit_runs")
    return ExtractionIntegritySignals(
        extracted_char_count=_num(raw.get("extracted_char_count")),  # type: ignore[arg-type]
        rendered_text_present=rendered if isinstance(rendered, bool) else None,
        ocr_char_count=_num(raw.get("ocr_char_count")),  # type: ignore[arg-type]
        hidden_text_char_count=_num(raw.get("hidden_text_char_count")),  # type: ignore[arg-type]
        offpage_text_char_count=_num(raw.get("offpage_text_char_count")),  # type: ignore[arg-type]
        duplicated_layer_count=_num(raw.get("duplicated_layer_count")),  # type: ignore[arg-type]
        extracted_digit_runs=tuple(text_digits) if isinstance(text_digits, list) else None,
        ocr_digit_runs=tuple(ocr_digits) if isinstance(ocr_digits, list) else None,
    )


def _cases() -> list[dict[str, object]]:
    data = json.loads(_FIXTURES.read_text(encoding="utf-8"))
    cases = data["cases"]
    assert isinstance(cases, list) and cases
    return [case for case in cases if isinstance(case, dict)]


def test_adversarial_cases_never_trusted_as_evidence() -> None:
    failures: list[str] = []
    for case in _cases():
        raw = case["signals"]
        assert isinstance(raw, dict)
        result = assess_extraction_integrity(_signals(raw))
        if result.status is ExtractionIntegrityStatus.OK or result.trusted_as_evidence():
            failures.append(f"{case.get('id')}: {result.status}")
    assert not failures, "Adversarial extraction assessed as trusted evidence:\n" + "\n".join(
        failures
    )


def test_rendered_but_empty_extraction_is_failed_not_absent() -> None:
    result = assess_extraction_integrity(
        ExtractionIntegritySignals(extracted_char_count=0, rendered_text_present=True)
    )
    assert result.status is ExtractionIntegrityStatus.FAILED


def test_clean_extraction_is_ok_positive_control() -> None:
    # Not trivially always-fail: a consistent extraction reads OK.
    result = assess_extraction_integrity(
        ExtractionIntegritySignals(
            extracted_char_count=800,
            rendered_text_present=True,
            ocr_char_count=780,
            hidden_text_char_count=0,
            offpage_text_char_count=0,
            duplicated_layer_count=0,
            extracted_digit_runs=("200", "3000"),
            ocr_digit_runs=("200", "3000"),
        )
    )
    assert result.status is ExtractionIntegrityStatus.OK
    assert result.trusted_as_evidence() is True


def test_same_length_digit_spoof_is_failed() -> None:
    # Visual «3000» vs text-layer «3300» — char counts match; digit collision fails.
    result = assess_extraction_integrity(
        ExtractionIntegritySignals(
            extracted_char_count=40,
            ocr_char_count=40,
            rendered_text_present=True,
            extracted_digit_runs=("3300",),
            ocr_digit_runs=("3000",),
        )
    )
    assert result.status is ExtractionIntegrityStatus.FAILED
    assert result.trusted_as_evidence() is False
    assert any("digit-run" in reason for reason in result.reasons)


def test_no_signals_is_review_required_never_silent_ok() -> None:
    result = assess_extraction_integrity(ExtractionIntegritySignals())
    assert result.status is ExtractionIntegrityStatus.REVIEW_REQUIRED


def test_verdict_neutral_serialization_has_no_passed_key() -> None:
    payload = json.dumps(
        assess_extraction_integrity(ExtractionIntegritySignals(extracted_char_count=10)).to_dict()
    )
    assert '"passed"' not in payload
