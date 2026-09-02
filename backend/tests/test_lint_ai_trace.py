"""AI-trace: prompts live in docs/ai/; public reviews must not start with agent voice."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]


class AcademicLitPromptHomeTests(unittest.TestCase):
    def test_review_does_not_embed_operator_prompt(self) -> None:
        review = (_REPO / "docs" / "quality" / "ACADEMIC_LIT_REVIEW_2026_09.md").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("Ты — научный со-автор", review)
        self.assertIn("ACADEMIC_LIT_RADAR.md", review)
        prompt = (_REPO / "docs" / "ai" / "ACADEMIC_LIT_RADAR.md").read_text(encoding="utf-8")
        self.assertIn("Ты — научный со-автор", prompt)
        self.assertIn("ACADEMIC_LIT_REVIEW_2026_09.md", prompt)


class LintAiTraceTests(unittest.TestCase):
    def test_public_tree_has_no_meta_or_chat_filler(self) -> None:
        sys.path.insert(0, str(_REPO / "scripts"))
        try:
            from lint_ai_trace import lint_ai_trace_meta  # type: ignore[import-not-found]
        finally:
            if sys.path and sys.path[0] == str(_REPO / "scripts"):
                sys.path.pop(0)
        self.assertEqual(lint_ai_trace_meta(root=_REPO), [])

    def test_hyphenated_na_in_url_is_not_placeholder(self) -> None:
        sys.path.insert(0, str(_REPO / "scripts"))
        try:
            from lint_ai_trace import _PLACEHOLDER_RE  # type: ignore[import-not-found]
        finally:
            if sys.path and sys.path[0] == str(_REPO / "scripts"):
                sys.path.pop(0)
        url = "https://new.etu.ru/ru/home/nauka/konkursy-i-granty-na-provedenie-niokr"
        self.assertIsNone(_PLACEHOLDER_RE.search(url))
        self.assertIsNotNone(_PLACEHOLDER_RE.search("| status | N/A |"))

    def test_chat_filler_outside_ai_dir_is_flagged(self) -> None:
        sys.path.insert(0, str(_REPO / "scripts"))
        try:
            from lint_ai_trace import lint_ai_trace_meta  # type: ignore[import-not-found]
        finally:
            if sys.path and sys.path[0] == str(_REPO / "scripts"):
                sys.path.pop(0)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs" / "quality"
            docs.mkdir(parents=True)
            (docs / "noise.md").write_text("Стоит отметить, что gate зелёный.\n", encoding="utf-8")
            hits = lint_ai_trace_meta(root=root)
        self.assertTrue(any("chat_filler" in h for h in hits))

    def test_product_heading_assistant_is_not_meta_voice(self) -> None:
        sys.path.insert(0, str(_REPO / "scripts"))
        try:
            from lint_ai_trace import lint_ai_trace_meta  # type: ignore[import-not-found]
        finally:
            if sys.path and sys.path[0] == str(_REPO / "scripts"):
                sys.path.pop(0)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs" / "quality"
            docs.mkdir(parents=True)
            (docs / "tz.md").write_text(
                "## 2. Концепция — ассистент, а не замена эксперта\n",
                encoding="utf-8",
            )
            hits = lint_ai_trace_meta(root=root)
        self.assertEqual(hits, [])

    def test_operator_prompt_line_is_flagged_outside_ai_dir(self) -> None:
        sys.path.insert(0, str(_REPO / "scripts"))
        try:
            from lint_ai_trace import lint_ai_trace_meta  # type: ignore[import-not-found]
        finally:
            if sys.path and sys.path[0] == str(_REPO / "scripts"):
                sys.path.pop(0)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs" / "quality"
            docs.mkdir(parents=True)
            (docs / "review.md").write_text(
                "Ты — научный со-автор проекта AeroBIM.\n",
                encoding="utf-8",
            )
            hits = lint_ai_trace_meta(root=root)
        self.assertTrue(any("meta_voice" in h for h in hits))


if __name__ == "__main__":
    unittest.main()
