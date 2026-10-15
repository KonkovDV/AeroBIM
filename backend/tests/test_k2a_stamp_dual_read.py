import pytest

from aerobim.domain.stamp_dual_read import DualReadReason, DualReadStatus, dual_read_stamp_field


def test_found_and_agreed() -> None:
    r = dual_read_stamp_field("sheet_code", "АР-01  Ё", "ар-01 е", ocr_confidence=0.9)
    assert r.status is DualReadStatus.AGREED and not r.requires_hitl


def test_not_found() -> None:
    r = dual_read_stamp_field("sheet_code", None, "  ")
    assert r.status is DualReadStatus.NOT_VERIFIED and r.reason is DualReadReason.NOT_FOUND


@pytest.mark.parametrize(
    ("vec", "ocr", "conf"),
    [("АР-01", None, None), (None, "АР-01", None), ("АР-01", "АР-01", 0.2)],
)
def test_unreadable_abstains(vec: str | None, ocr: str | None, conf: float | None) -> None:
    r = dual_read_stamp_field("sheet_code", vec, ocr, ocr_confidence=conf)
    assert r.status is DualReadStatus.ABSTAIN and r.reason is DualReadReason.UNREADABLE


def test_disagreement_abstains_never_ok() -> None:
    r = dual_read_stamp_field("revision", "Изм. 2", "Изм. 3", ocr_confidence=0.99)
    assert r.status is DualReadStatus.ABSTAIN and r.requires_hitl and r.value is None
