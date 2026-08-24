"""City AGR example pin: skip-safe; does not claim RT closed."""

from __future__ import annotations

import unittest

from aerobim.tools.benchmark_project_package import repo_root
from aerobim.tools.moscow_agr_city_examples import load_manifest, missing_ifc_files
from aerobim.tools.run_moscow_agr_city_examples import skipped_payload


class MoscowAgrCityExamplesTests(unittest.TestCase):
    def test_manifest_has_five_ifc_urls_and_does_not_claim_rt(self) -> None:
        manifest = load_manifest()
        files = manifest["files"]
        self.assertEqual(len(files), 5)
        for entry in files:
            self.assertTrue(str(entry["url"]).startswith("https://stroimprosto.mos.ru/"))
            self.assertTrue(str(entry["local_name"]).endswith(".ifc"))
            self.assertGreater(int(entry["expected_bytes"]), 0)
        self.assertFalse(manifest["closes_rt001"])
        self.assertFalse(manifest["closes_rt002b"])
        self.assertFalse(manifest["closes_rt003"])
        self.assertEqual(manifest["signoff_profile"], "moscow_agr_2026")
        four_field = [row for row in files if row["filename_fields"] == 4]
        five_field = [row for row in files if row["filename_fields"] == 5]
        self.assertEqual(len(four_field), 2)
        self.assertEqual(len(five_field), 3)
        pack = repo_root() / "samples" / "ids" / "moscow-agr" / "pack"
        for row in files:
            names = row.get("ids_names") or []
            self.assertTrue(names, msg=str(row.get("id")))
            for ids_name in names:
                self.assertTrue((pack / str(ids_name)).is_file(), msg=str(ids_name))

    def test_skipped_payload_keeps_rt_open(self) -> None:
        payload = skipped_payload(reason="missing")
        self.assertEqual(payload["status"], "SKIPPED")
        self.assertFalse(payload["closes_rt001"])
        self.assertFalse(payload["closes_rt002b"])
        self.assertFalse(payload["closes_rt003"])
        self.assertEqual(payload["checkpoint"], "NO_GO")
        self.assertFalse(payload["injector_ran"])
        self.assertIn("content_sha256", payload)

    def test_missing_ifc_files_when_unfetched(self) -> None:
        missing = missing_ifc_files()
        self.assertIsInstance(missing, list)
        if missing:
            self.assertTrue(all(name.endswith(".ifc") for name in missing))


if __name__ == "__main__":
    unittest.main()
