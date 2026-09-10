"""WP-R7: review books classified by structure; PII stripped; no auto-match."""

from __future__ import annotations

import hashlib
import shutil
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from aerobim.domain.customer_review_book import (
    ReviewBookError,
    assert_output_path_allowed,
    classify_sheet_kind,
    dedupe_books,
    eligible_for_fn,
    parse_review_book,
    sha256_file,
)

_REPO = Path(__file__).resolve().parents[2]


def _write_book(
    path: Path,
    *,
    filled_status: bool,
    pii: bool = False,
    formula_prefix: bool = False,
) -> None:
    book = Workbook()
    sheet = book.active
    sheet.title = "КР"
    # three-level header: rounds / names / (optional blank)
    sheet.append(
        ["", "", "Первичная проверка", "", "Повторная проверка", "", "Проверка критических", ""]
    )
    headers = [
        "№№",
        "Содержание требований / Лист РД",
        "Статус проверки",
        "Комментарии (замечания)",
        "Статус проверки",
        "Комментарии (замечания)",
        "Статус проверки",
        "Комментарии (замечания)",
    ]
    if pii:
        headers.extend(["ФИО проверяющего", "e-mail"])
    if formula_prefix:
        headers = ["#NAME?", "#NAME?", "#NAME?", "#NAME?", "#NAME?", "#NAME?", *headers]
        # shift: keep requirement after formula columns
    sheet.append(headers)
    status = "не соответствует" if filled_status else ""
    comment = "ось А/1" if filled_status else ""
    data = ["1", "Наличие ИРД / лист РД", status, comment, "", "", "", ""]
    if pii:
        data.extend(["Иванов И.И.", "ivanov@example.com"])
    if formula_prefix:
        data = ["#NAME?"] * 6 + data
    sheet.append(data)
    book.save(path)


class CustomerReviewBookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_source_kind_from_structure_not_filename(self) -> None:
        review = self.tmp / "типовые-ошибки.xlsx"
        template = self.tmp / "книга-замечаний.xlsx"
        _write_book(review, filled_status=True)
        _write_book(template, filled_status=False)
        self.assertEqual(parse_review_book(review)["source_kind"], "review_book")
        self.assertEqual(parse_review_book(template)["source_kind"], "requirement_template")

    def test_empty_template_is_not_review_book(self) -> None:
        path = self.tmp / "template.xlsx"
        _write_book(path, filled_status=False)
        payload = parse_review_book(path)
        self.assertEqual(payload["source_kind"], "requirement_template")
        self.assertEqual(
            classify_sheet_kind(["Содержание требований", "Статус проверки"], [""]),
            "requirement_template",
        )

    def test_three_level_header_is_parsed(self) -> None:
        path = self.tmp / "rounds.xlsx"
        _write_book(path, filled_status=True)
        payload = parse_review_book(path)
        row = payload["rows"][0]
        self.assertEqual(len(row["observations"]), 3)
        self.assertEqual({obs["round_index"] for obs in row["observations"]}, {0, 1, 2})

    def test_formula_columns_are_ignored(self) -> None:
        path = self.tmp / "formula.xlsx"
        _write_book(path, filled_status=True, formula_prefix=True)
        payload = parse_review_book(path)
        self.assertGreaterEqual(payload["requirement_count"], 1)
        self.assertNotIn("#NAME?", payload["rows"][0]["requirement_text"])

    def test_rounds_expand_to_observations_not_remarks(self) -> None:
        path = self.tmp / "rounds.xlsx"
        _write_book(path, filled_status=True)
        payload = parse_review_book(path)
        self.assertEqual(payload["requirement_count"], 1)
        self.assertEqual(len(payload["rows"][0]["observations"]), 3)

    def test_duplicate_books_deduped_by_sha(self) -> None:
        a = self.tmp / "a.xlsx"
        b = self.tmp / "b.xlsx"
        _write_book(a, filled_status=True)
        shutil.copy(a, b)
        unique, duplicates = dedupe_books([a, b])
        self.assertEqual(len(unique), 1)
        self.assertEqual(duplicates, 1)
        self.assertEqual(sha256_file(a), hashlib.sha256(a.read_bytes()).hexdigest())

    def test_person_fields_are_stripped_on_ingest(self) -> None:
        path = self.tmp / "pii.xlsx"
        _write_book(path, filled_status=True, pii=True)
        payload = parse_review_book(path)
        blob = str(payload)
        self.assertNotIn("Иванов", blob)
        self.assertNotIn("ivanov@example.com", blob)

    def test_unknown_header_refuses_with_listing(self) -> None:
        path = self.tmp / "unknown.xlsx"
        book = Workbook()
        book.active.append(["foo", "bar"])
        book.save(path)
        with self.assertRaises(ReviewBookError) as ctx:
            parse_review_book(path)
        self.assertIn("unknown header", str(ctx.exception))
        self.assertIn("foo", str(ctx.exception))

    def test_matrix_leaves_matched_finding_id_empty(self) -> None:
        path = self.tmp / "review.xlsx"
        _write_book(path, filled_status=True)
        payload = parse_review_book(path)
        self.assertEqual(payload["rows"][0]["matched_finding_id"], "")

    def test_no_automatic_text_matching(self) -> None:
        path = self.tmp / "review.xlsx"
        _write_book(path, filled_status=True)
        payload = parse_review_book(path)
        self.assertTrue(all(row["matched_finding_id"] == "" for row in payload["rows"]))

    def test_fn_only_where_coverage_checked(self) -> None:
        self.assertTrue(eligible_for_fn(coverage_status="checked", stage_mismatch=False))
        self.assertFalse(eligible_for_fn(coverage_status="not_checked", stage_mismatch=False))
        self.assertFalse(eligible_for_fn(coverage_status="checked", stage_mismatch=True))

    def test_stage_mismatch_rows_excluded_both_ways(self) -> None:
        path = self.tmp / "rd.xlsx"
        _write_book(path, filled_status=True)
        payload = parse_review_book(path, rd_ifc_present=False)
        self.assertTrue(payload["rows"][0]["stage_mismatch"])
        self.assertFalse(
            eligible_for_fn(
                coverage_status="checked", stage_mismatch=payload["rows"][0]["stage_mismatch"]
            )
        )

    def test_refuses_when_coverage_hash_changed(self) -> None:
        path = self.tmp / "review.xlsx"
        _write_book(path, filled_status=True)
        with self.assertRaises(ReviewBookError):
            parse_review_book(path, coverage_hash="aaa", expected_coverage_hash="bbb")

    def test_refuses_to_write_into_samples_customer(self) -> None:
        with self.assertRaises(ReviewBookError):
            assert_output_path_allowed(_REPO / "samples" / "customer" / "out", repo=_REPO)


if __name__ == "__main__":
    unittest.main()
