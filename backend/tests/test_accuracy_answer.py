"""WP-R7a: accuracy-answer rows carry corpus_kind and n; none claim product %."""

from __future__ import annotations

import unittest
from pathlib import Path

from aerobim.domain.accuracy_answer import assemble_accuracy_answer, render_accuracy_answer_markdown

_REPO = Path(__file__).resolve().parents[2]


class AccuracyAnswerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = assemble_accuracy_answer(_REPO)

    def test_every_number_has_corpus_kind_and_n(self) -> None:
        rows = self.payload["rows"]
        self.assertGreaterEqual(len(rows), 4)
        for row in rows:
            self.assertTrue(row.get("corpus_kind"), row)
            n = row.get("n") if row.get("n") is not None else row.get("fixture_n")
            self.assertIsNotNone(n, row)
            self.assertGreater(int(n), 0, row)

    def test_no_row_claims_product_accuracy(self) -> None:
        self.assertFalse(self.payload["is_accuracy"])
        self.assertFalse(self.payload["precision_claim_publishable"])
        for row in self.payload["rows"]:
            self.assertFalse(row["is_product_accuracy"])
            self.assertFalse(row["publishable"])

    def test_simulated_kappa_is_labelled_simulation(self) -> None:
        kappa = next(row for row in self.payload["rows"] if row["id"] == "dual_rater_simulation")
        self.assertEqual(kappa["labelled"], "simulation")
        self.assertEqual(kappa["independent_human_raters"], 0)
        self.assertEqual(kappa["corpus_kind"], "synthetic")

    def test_artifact_lists_what_is_needed_to_measure_on_customer_corpus(self) -> None:
        needed = self.payload["needed_to_measure_on_customer_corpus"]
        blob = " ".join(needed).casefold()
        self.assertIn("two", blob)
        self.assertIn("held-out", blob)
        markdown = render_accuracy_answer_markdown(self.payload)
        self.assertIn("На комплекте заказчика не измеряли", markdown)
        self.assertNotIn("точность продукта >90", markdown)


if __name__ == "__main__":
    unittest.main()
