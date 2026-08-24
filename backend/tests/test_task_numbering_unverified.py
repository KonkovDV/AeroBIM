"""Fail-closed: do not attribute an unverified TechLab task number on user-facing surfaces."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]

_TASK_NUMBER_ATTR = re.compile(
    r"(?:задача|задачи|задаче|задачу|задачей)\s*(?:№|#)?\s*0?7\b"
    r"|\btask\s+0?7\b"
    r"|задач[аиеиу]\s*№\s*7\b",
    re.IGNORECASE,
)

_ALLOW_RELATIVE = frozenset(
    {
        "docs/partners/_2026_08_25.md",
        "docs/partners/outreach/LETTER_PROGRAM_OPERATOR_PROTOCOL_DRAFT.md",
        "docs/roadmap/WEEK_2026_08_25.md",
        "backend/tests/test_task_numbering_unverified.py",
    }
)

_SURFACE_FILES = (
    "README.md",
    "README.ru.md",
    "docs/docs.md",
    ".github/repository-metadata.md",
    "docs/partners/TECHLAB_FINAL_DELTA_2026_08_24.md",
    "docs/partners/TECHLAB_KT3_OSINT_2026_08_24.md",
    "docs/partners/TECHLAB_TASK_07_READINESS_2026.md",
    "docs/partners/TECHLAB_SAMOLET_APPLICATION_2026.md",
    "docs/partners/MIK_OPERATOR_ASK_2026_08_15.md",
    "docs/partners/OFFER_FOUR_AUDIENCES_2026_08_24.md",
    "docs/partners/outreach/README.md",
    "docs/partners/outreach/TARGET_LIST_2026_08_24.md",
    "docs/roadmap/MASTER_WORKPLAN_2026_07_27.md",
    "docs/roadmap/WEEK_2026_08_25.md",
)

_SURFACE_DIRS = (
    "docs/partners/outreach",
    "submission",
)


def _iter_surface_paths() -> list[Path]:
    paths: list[Path] = []
    for rel in _SURFACE_FILES:
        path = _REPO / rel
        if path.is_file():
            paths.append(path)
    for rel in _SURFACE_DIRS:
        root = _REPO / rel
        if root.is_dir():
            paths.extend(sorted(root.rglob("*.md")))
    seen: set[Path] = set()
    out: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        out.append(path)
    return out


class TaskNumberingUnverifiedTests(unittest.TestCase):
    def test_user_facing_surfaces_do_not_attribute_task_07(self) -> None:
        hits: list[str] = []
        for path in _iter_surface_paths():
            rel = path.relative_to(_REPO).as_posix()
            if rel in _ALLOW_RELATIVE:
                continue
            text = path.read_text(encoding="utf-8")
            for i, line in enumerate(text.splitlines(), start=1):
                if _TASK_NUMBER_ATTR.search(line):
                    hits.append(f"{rel}:{i}:{line.strip()[:160]}")
        self.assertEqual(
            hits,
            [],
            msg="unverified task number on user-facing surface:\n" + "\n".join(hits),
        )

    def test_canonical_phrase_on_readme_and_letter(self) -> None:
        readme_ru = (_REPO / "README.ru.md").read_text(encoding="utf-8")
        self.assertIn("автоматизированной верификации проектной и рабочей документации", readme_ru)
        self.assertIn("Самолёт", readme_ru)
        letter = (_REPO / "docs/partners/outreach/LETTER_MGSU_SPBGASU_DRAFT.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("автоматизированной верификации проектной и рабочей документации", letter)
        self.assertNotIn("задача 07", letter)
        self.assertNotIn("задача 7,", letter)

    def test_spbgasu_letter_has_it_preregistration_and_kappa_limit(self) -> None:
        letter = (_REPO / "docs/partners/outreach/LETTER_MGSU_SPBGASU_DRAFT.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Docker", letter)
        self.assertIn("WSL2", letter)
        self.assertIn("256", letter)
        self.assertIn("ADR-001", letter)
        self.assertIn("404", letter)
        self.assertIn("не 403", letter)
        self.assertIn("Предрегистрация", letter)
        self.assertIn("κ", letter)
        self.assertIn("инжектирован", letter)
        self.assertIn("Базы типовых замечаний", letter)
        self.assertIn("compscience@spbgasu.ru", letter)

    def test_agr_self_check_never_a_channel(self) -> None:
        delta = (_REPO / "docs/partners/TECHLAB_FINAL_DELTA_2026_08_24.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("никогда не канал", delta)
        ssot = (_REPO / "docs/partners/_2026_08_25.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("никогда не канал", ssot)

    def test_prize_is_paid_pilot_not_program_fund(self) -> None:
        delta = (_REPO / "docs/partners/TECHLAB_FINAL_DELTA_2026_08_24.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("платный пилот", delta)
        self.assertIn("2 млн", delta)
        self.assertNotRegex(delta, r"призов(ой|ого) фонд.{0,40}недоступ")
        week = (_REPO / "docs/roadmap/WEEK_2026_08_25.md").read_text(encoding="utf-8")
        self.assertIn("ИП", week)
        self.assertIn("платный пилот", week)


if __name__ == "__main__":
    unittest.main()
