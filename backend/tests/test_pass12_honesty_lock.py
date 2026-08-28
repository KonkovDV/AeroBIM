"""Pass 12 honesty lock — must fail on HEAD before the matching docs/rows exist.

Attacks: denylist pointer, manual scan roots, version-compare as advantage,
machine-readable requirements as advantage, foreign metrics as ours, missing
AI impact assessment, customer norm-pack as the only path, questionnaire/video
as a non-publication.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from aerobim.domain.live_tree_triage import TRIAGE_ROWS

_REPO = Path(__file__).resolve().parents[2]

PASS12_KILL_IDS = (
    "RT-KIT-PTR",
    "RT-KIT-ROOTS",
    "RT-POS-VERDIFF",
    "RT-POS-IDSADV",
    "RT-POS-FOREIGN-METRIC",
    "RT-AI-IMPACT",
    "RT-NORM-MARKET",
    "RT-PUB-SURFACE",
)

PASS12_FORBIDDEN_PHRASES = (
    "пакет заказчика проверен",
    "43 гб обработаны",
    "режим данных согласован",
    "соглашение о конфиденциальности подписано",
    "первые в россии сравниваем версии документации",
    "точнее городского нормоконтроля",
    "заменяем зарубежные проверяльщики моделей",
    "поддерживаем машиночитаемые требования лучше рынка",
    "интегрированы с платформой заказчика",
)

IMPACT_REL = "docs/quality/AI_SYSTEM_IMPACT_ASSESSMENT_GOST_R_72514_2026.md"
SURFACES_REL = "docs/quality/PUBLIC_SURFACES_PROTOCOL_2026.md"

IMPACT_HEADINGS = (
    "совместимость не сертификация",
    "контекст и сценарии",
    "затронутые стороны",
    "пропущенное замечание",
    "ложное замечание",
    "человек в контуре",
    "журнал решений",
    "ограничения выборки",
    "план пересмотра",
)

POINTER_CATEGORY_LEAKS = (
    "топоним",
    "фамил",
    "surname",
    "toponym",
    "tracker surname",
)


class Pass12HonestyLockTests(unittest.TestCase):
    def test_pass12_kill_ids_exist(self) -> None:
        by_id = {row["id"]: row for row in TRIAGE_ROWS}
        for row_id in PASS12_KILL_IDS:
            self.assertIn(row_id, by_id)
            self.assertEqual(by_id[row_id]["verdict"], "KILL")
            self.assertTrue(by_id[row_id]["brake"])

    def test_pass12_phrases_are_in_wording_ssot(self) -> None:
        import json

        payload = json.loads(
            (_REPO / "audit" / "claims_forbidden_wording.json").read_text(encoding="utf-8")
        )
        phrases = [str(item).lower() for item in payload["forbidden_affirmative_phrases"]]
        for phrase in PASS12_FORBIDDEN_PHRASES:
            self.assertIn(phrase, phrases)

    def test_impact_assessment_exists_with_required_headings(self) -> None:
        path = _REPO / IMPACT_REL
        self.assertTrue(path.is_file(), msg=IMPACT_REL)
        text = path.read_text(encoding="utf-8").lower()
        self.assertIn("гост р 72514-2026", text)
        self.assertIn("iso/iec 42005:2025", text)
        for heading in IMPACT_HEADINGS:
            self.assertIn(heading, text, msg=heading)
        self.assertNotIn("сертифицирован", text)

    def test_public_surfaces_protocol_exists_with_six_checks(self) -> None:
        path = _REPO / SURFACES_REL
        self.assertTrue(path.is_file(), msg=SURFACES_REL)
        text = path.read_text(encoding="utf-8").lower()
        self.assertIn("анкет", text)
        self.assertIn("кадр", text)
        for index in range(1, 7):
            self.assertRegex(text, rf"{index}[\.\)]")

    def test_pre_commit_quarantines_pack_suffixes_and_size(self) -> None:
        hook = (_REPO / ".githooks" / "pre-commit").read_text(encoding="utf-8").lower()
        for needle in (".rvt", ".nwd", ".lir", ".dwg", "files/", ".local/pack/", "52428800"):
            self.assertIn(needle, hook, msg=needle)

    def test_kitchen_scan_uses_git_ls_files_not_content_roots(self) -> None:
        source = (_REPO / "scripts" / "kitchen_denylist.py").read_text(encoding="utf-8")
        self.assertIn("git", source)
        self.assertIn("ls-files", source)
        self.assertIn("class defect", source.lower())
        self.assertNotRegex(source, r"_CONTENT_ROOTS|_KITCHEN_SCAN_ROOTS")

    def test_guard_and_kit_rows_do_not_describe_token_categories(self) -> None:
        kit = next(row for row in TRIAGE_ROWS if row["id"] == "RT-KIT-01")
        blob = "\n".join((kit["attack"], kit["brake"]))
        for row in TRIAGE_ROWS:
            if row["id"] in {"RT-KIT-PTR", "RT-KIT-ROOTS"}:
                blob += "\n" + row["attack"] + "\n" + row["brake"]
        lowered = blob.lower()
        for leak in POINTER_CATEGORY_LEAKS:
            self.assertNotIn(leak, lowered, msg=leak)

    def test_workplan_names_licensed_registry_as_alternate_path(self) -> None:
        text = (
            _REPO / "docs" / "quality" / "KT3_IN_REPO_WORKPLAN_2026_08_27.md"
        ).read_text(encoding="utf-8").lower()
        self.assertIn("licensed", text)
        self.assertIn("registry", text)


if __name__ == "__main__":
    unittest.main()
