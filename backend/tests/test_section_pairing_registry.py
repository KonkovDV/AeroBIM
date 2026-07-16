from __future__ import annotations

import unittest

from aerobim.domain.section_pairing import (
    canonicalize_discipline,
    canonicalize_key,
    known_discipline_codes,
    normalize_key,
    slugify,
    transliterate,
)


class DisciplineRegistryTests(unittest.TestCase):
    def test_ru_and_en_aliases_fold_to_same_canonical_code(self) -> None:
        self.assertEqual(canonicalize_discipline("AR").code, "AR")
        self.assertEqual(canonicalize_discipline("АР").code, "AR")
        self.assertEqual(canonicalize_discipline("architecture").code, "AR")
        self.assertTrue(canonicalize_discipline("АР").recognized)

    def test_reinforced_concrete_ru_mark_resolves(self) -> None:
        info = canonicalize_discipline("КЖ")
        self.assertEqual(info.code, "KZH")
        self.assertTrue(info.recognized)

    def test_unknown_discipline_is_echoed_but_flagged_unrecognized(self) -> None:
        info = canonicalize_discipline("ZZZ-CUSTOM")
        self.assertFalse(info.recognized)
        # Deterministic, latin, slug-safe fallback code.
        self.assertEqual(info.code, "ZZZ-CUSTOM")

    def test_registry_covers_multiple_disciplines(self) -> None:
        codes = known_discipline_codes()
        for expected in ("AR", "KZH", "KM", "OV", "VK", "EOM"):
            self.assertIn(expected, codes)
        self.assertGreaterEqual(len(codes), 10)


class CanonicalKeyRegistryTests(unittest.TestCase):
    def test_ru_alias_maps_to_en_canonical_key(self) -> None:
        result = canonicalize_key("защитный_слой_бетона", "KZH")
        self.assertEqual(result.canonical, "rebar.cover")
        self.assertTrue(result.recognized)

    def test_separator_normalization_is_stable(self) -> None:
        self.assertEqual(normalize_key("Rebar / Cover"), "rebar.cover")
        self.assertEqual(normalize_key("apartment.area.total"), "apartment.area.total")

    def test_common_key_resolves_across_disciplines(self) -> None:
        self.assertEqual(canonicalize_key("этажность", "AR").canonical, "floor.count")
        self.assertEqual(canonicalize_key("floor.count", "KZH").canonical, "floor.count")

    def test_unknown_key_is_normalized_but_flagged_unrecognized(self) -> None:
        result = canonicalize_key("Custom_Vendor_Field", "AR")
        self.assertFalse(result.recognized)
        self.assertEqual(result.canonical, "custom.vendor.field")


class SlugTests(unittest.TestCase):
    def test_cyrillic_transliterates_to_stable_latin_slug(self) -> None:
        self.assertEqual(slugify("КЖ"), "KZH")
        self.assertEqual(slugify("защитный.слой"), "ZASHCHITNYJ-SLOJ")

    def test_latin_keys_are_unchanged_in_shape(self) -> None:
        self.assertEqual(slugify("building.height"), "BUILDING-HEIGHT")

    def test_transliterate_passes_latin_through(self) -> None:
        self.assertEqual(transliterate("rebar.cover"), "rebar.cover")


if __name__ == "__main__":
    unittest.main()
