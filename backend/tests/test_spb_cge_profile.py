"""SPb GAU CGE official IDS profile: fail-closed manifest + IDS 1.0 gates.

The profile bundles the published ЦГЭ IDS 1.0 files (ОКС 3.1.0 + РИИ 1.1.0)
byte-exact. It is OFFICIAL_PUBLISHED, never customer-signed, and never closes
RT-001/RT-002/RT-003. Corrupted, missing, undeclared, or non-IDS-1.0 files
must fail the run — silence is never success.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.official_ids_profile import (
    OfficialIdsProfileError,
    find_file_mismatches,
    parse_official_ids_profile,
)
from aerobim.tools.validate_spb_cge_profile import (
    collect_actual_files,
    load_manifest,
    parse_gate_files,
    validate_profile,
    xsd_validate_files,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PROFILE_DIR = REPO_ROOT / "samples" / "profiles" / "spb-cge"
MANIFEST_PATH = PROFILE_DIR / "manifest.json"
SCHEMA_PATH = PROFILE_DIR / "manifest.schema.json"
PACK_ROOT = REPO_ROOT / "samples" / "ids" / "spbexp" / "pack"
XSD_PATH = REPO_ROOT / "samples" / "ids-xsd" / "ids.xsd"
DATASET_MANIFEST = REPO_ROOT / "samples" / "DATASET_MANIFEST.json"
POINTER_PATH = REPO_ROOT / "samples" / "ids" / "spbexp" / "jurisdiction-profile-pointer.json"
SMALLEST_IDS_REL = "rii/ЦГЭ.ЦИМ.РИИ_ИГДИ_Рельеф_1.1.0_(IDS_1.0).ids"


def _manifest_payload() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _tmp_profile_manifest(target_dir: Path, *, files: list[dict], pack_root: Path) -> dict:
    payload = _manifest_payload()
    smallest = next(entry for entry in payload["files"] if entry["path"] == SMALLEST_IDS_REL)
    entries: list[dict] = []
    for extra in files:
        entry = dict(smallest)
        entry.update(extra)
        entries.append(entry)
    payload["files"] = entries
    payload["pack_root"] = pack_root.relative_to(target_dir).as_posix()
    (target_dir / "manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return payload


class SpbCgeProfileManifestTests(unittest.TestCase):
    def test_manifest_file_exists(self) -> None:
        self.assertTrue(MANIFEST_PATH.is_file(), MANIFEST_PATH)
        self.assertTrue(SCHEMA_PATH.is_file(), SCHEMA_PATH)

    def test_manifest_validates_against_json_schema(self) -> None:
        import jsonschema

        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        errors = sorted(
            jsonschema.Draft202012Validator(schema).iter_errors(_manifest_payload()),
            key=lambda err: list(err.path),
        )
        self.assertEqual(errors, [], [err.message for err in errors])

    def test_domain_parse_and_honesty_locks(self) -> None:
        profile = parse_official_ids_profile(_manifest_payload())
        self.assertEqual(profile.profile_id, "SPBEXP-GAU-CGE-IDS")
        self.assertEqual(profile.provenance_status, "OFFICIAL_PUBLISHED")
        self.assertEqual(profile.language, "ru")
        self.assertEqual(len(profile.files), 22)
        for field in (
            "signed_by_customer",
            "closes_rt001",
            "closes_rt002",
            "closes_rt003",
            "samolet_alias",
        ):
            self.assertIs(_manifest_payload()[field], False, field)
        self.assertIn("экспертиз", profile.disclaimer.casefold())

    def test_absolute_pack_root_is_rejected(self) -> None:
        payload = _manifest_payload()
        payload["pack_root"] = "/tmp/pack"
        with self.assertRaises(OfficialIdsProfileError) as ctx:
            parse_official_ids_profile(payload)
        self.assertIn("pack_root", str(ctx.exception))
        payload["pack_root"] = "C:/abs/pack"
        with self.assertRaises(OfficialIdsProfileError) as ctx:
            parse_official_ids_profile(payload)
        self.assertIn("pack_root", str(ctx.exception))

    def test_pack_root_escape_via_dotdot_is_rejected_at_parse(self) -> None:
        payload = _manifest_payload()
        payload["pack_root"] = "samples/ids/spbexp/pack/../../../etc"
        with self.assertRaises(OfficialIdsProfileError) as ctx:
            parse_official_ids_profile(payload)
        self.assertIn("pack_root", str(ctx.exception))

    def test_profile_index_is_not_labelled_synthetic_ids(self) -> None:
        dataset = json.loads(DATASET_MANIFEST.read_text(encoding="utf-8"))
        registry = {entry["path"]: entry for entry in dataset["files"]}
        for rel in ("profiles/spb-cge/manifest.json", "profiles/spb-cge/manifest.schema.json"):
            recorded = registry[rel]
            self.assertEqual(recorded["provenance"], "project_authored_fixture", rel)
            self.assertNotIn("synthetic content", recorded["source"], rel)
            self.assertIn("index", recorded["source"].casefold(), rel)
            self.assertIn("fixture", recorded["production_use"], rel)

    def test_subjects_are_not_mixed(self) -> None:
        profile = parse_official_ids_profile(_manifest_payload())
        oks = [entry for entry in profile.files if entry.subject == "oks"]
        rii = [entry for entry in profile.files if entry.subject == "rii"]
        self.assertEqual(len(oks), 17)
        self.assertEqual(len(rii), 5)
        self.assertTrue(all(entry.path.startswith("oks/") for entry in oks))
        self.assertTrue(all(entry.path.startswith("rii/") for entry in rii))
        edition_by_subject = {edition.subject: edition.edition for edition in profile.editions}
        self.assertEqual(edition_by_subject, {"oks": "3.1.0", "rii": "1.1.0"})
        self.assertTrue(all(entry.doc_edition == "3.1" for entry in oks))
        self.assertTrue(all(entry.doc_edition == "1.1.0" for entry in rii))

    def test_manifest_hashes_match_dataset_manifest(self) -> None:
        dataset = json.loads(DATASET_MANIFEST.read_text(encoding="utf-8"))
        registry = {entry["path"]: entry for entry in dataset["files"]}
        profile = parse_official_ids_profile(_manifest_payload())
        for entry in profile.files:
            dataset_path = f"ids/spbexp/pack/{entry.path}"
            recorded = registry.get(dataset_path)
            self.assertIsNotNone(recorded, dataset_path)
            assert recorded is not None
            self.assertEqual(recorded["sha256"], entry.sha256, dataset_path)
            self.assertEqual(recorded["bytes"], entry.size_bytes, dataset_path)

    def test_manifest_agrees_with_jurisdiction_pointer(self) -> None:
        pointer = json.loads(POINTER_PATH.read_text(encoding="utf-8"))
        self.assertEqual(pointer["profile_id"], "SPBEXP-GAU-CGE-IDS")
        self.assertIs(pointer["closes_rt002"], False)
        self.assertIs(pointer["customer_signed"], False)


class SpbCgeProfileFileGateTests(unittest.TestCase):
    def test_all_files_present_hashes_and_sizes_match(self) -> None:
        profile = load_manifest(MANIFEST_PATH)
        actual = collect_actual_files(profile, PACK_ROOT)
        self.assertEqual(find_file_mismatches(profile, actual), ())

    def test_every_file_validates_against_ids_1_0_xsd(self) -> None:
        profile = load_manifest(MANIFEST_PATH)
        self.assertEqual(xsd_validate_files(profile, PACK_ROOT, XSD_PATH), {})

    def test_ifctester_parse_gate_counts_356_specifications(self) -> None:
        profile = load_manifest(MANIFEST_PATH)
        counts = parse_gate_files(profile, PACK_ROOT)
        self.assertEqual(len(counts), 22)
        self.assertTrue(all(count > 0 for count in counts.values()))
        self.assertEqual(sum(counts.values()), 356)


class SpbCgeProfileDeterminismTests(unittest.TestCase):
    def test_full_profile_two_fixture_runs_identical(self) -> None:
        payload = validate_profile(REPO_ROOT, probe_runs=2)
        probe = payload["fixture_probe"]
        self.assertGreaterEqual(probe["runs"], 2)
        self.assertIs(probe["identical"], True)
        self.assertEqual(len(set(probe["issues_per_run"])), 1)
        self.assertEqual(probe["signature_sha256"], probe["signature_sha256"].lower())
        self.assertEqual(payload["totals"]["files"], 22)
        self.assertIs(payload["closes_rt001"], False)
        self.assertIs(payload["closes_rt002"], False)
        self.assertIs(payload["closes_rt003"], False)
        self.assertIs(payload["signed_by_customer"], False)
        self.assertEqual(payload["provenance_status"], "OFFICIAL_PUBLISHED")
        from aerobim.tools.validate_spb_cge_profile import verify_committed_evidence

        verify_committed_evidence(REPO_ROOT, live=payload)

    def test_committed_evidence_binds_to_current_manifest(self) -> None:
        from aerobim.tools.validate_spb_cge_profile import (
            DEFAULT_EVIDENCE_OUT,
            _sha256_text_ci,
        )

        evidence_path = REPO_ROOT / DEFAULT_EVIDENCE_OUT
        self.assertTrue(evidence_path.is_file(), evidence_path)
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        self.assertEqual(evidence["manifest_sha256"], _sha256_text_ci(MANIFEST_PATH))
        self.assertIs(evidence["closes_rt001"], False)
        self.assertIs(evidence["closes_rt002"], False)
        self.assertIs(evidence["closes_rt003"], False)
        self.assertIs(evidence["signed_by_customer"], False)
        dataset = json.loads(DATASET_MANIFEST.read_text(encoding="utf-8"))
        recorded = next(
            entry for entry in dataset["files"] if entry["path"] == "profiles/spb-cge/manifest.json"
        )
        self.assertEqual(recorded["sha256"], evidence["manifest_sha256"])
        from aerobim.tools.validate_spb_cge_profile import verify_committed_evidence

        verify_committed_evidence(REPO_ROOT)

    def test_stale_evidence_manifest_hash_is_rejected(self) -> None:
        from aerobim.tools.validate_spb_cge_profile import (
            DEFAULT_EVIDENCE_OUT,
            verify_committed_evidence,
        )

        raw = json.loads((REPO_ROOT / DEFAULT_EVIDENCE_OUT).read_text(encoding="utf-8"))
        raw["manifest_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as tmp:
            tampered = Path(tmp) / "evidence.json"
            tampered.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(OfficialIdsProfileError) as ctx:
                verify_committed_evidence(REPO_ROOT, evidence_path=tampered)
        self.assertIn("manifest_sha256", str(ctx.exception))

    def test_stale_evidence_xsd_hash_is_rejected(self) -> None:
        from aerobim.tools.validate_spb_cge_profile import (
            DEFAULT_EVIDENCE_OUT,
            verify_committed_evidence,
        )

        raw = json.loads((REPO_ROOT / DEFAULT_EVIDENCE_OUT).read_text(encoding="utf-8"))
        raw["ids_xsd"] = dict(raw["ids_xsd"])
        raw["ids_xsd"]["xsd_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as tmp:
            tampered = Path(tmp) / "evidence.json"
            tampered.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(OfficialIdsProfileError) as ctx:
                verify_committed_evidence(REPO_ROOT, evidence_path=tampered)
        self.assertIn("xsd_sha256", str(ctx.exception))

    def test_coverage_json_has_no_host_checkout_paths(self) -> None:
        coverage_path = REPO_ROOT / "docs" / "evidence" / "norm-pack-spbexp-coverage-2026-08.json"
        text = coverage_path.read_text(encoding="utf-8")
        self.assertNotIn("C:/plans", text)
        self.assertNotIn("Windows-11-", text)
        payload = json.loads(text)
        self.assertEqual(payload["pack_dir"], "samples/ids/spbexp/pack")
        self.assertTrue(str(payload["fixture_ifc"]["path"]).startswith("samples/"))
        self.assertTrue(str(payload["files"][0]["path"]).startswith("samples/"))
        self.assertEqual(payload["summary"]["executable_pass_on_fixture"], 195)
        self.assertEqual(payload["summary"]["executable_fail_on_fixture"], 161)

    def test_publisher_oks_folder_is_verbatim(self) -> None:
        publisher_folder = "Требования к ЦИМ ОК _V.3.1.0"
        folder = PACK_ROOT / "oks" / publisher_folder
        self.assertTrue(folder.is_dir(), folder)
        prefix = f"oks/{publisher_folder}/"
        oks_paths = [
            entry["path"]
            for entry in _manifest_payload()["files"]
            if entry["path"].startswith("oks/")
        ]
        self.assertTrue(oks_paths)
        self.assertTrue(all(path.startswith(prefix) for path in oks_paths))

    def test_source_md_states_hash_policy_and_publisher_rights(self) -> None:
        text = (REPO_ROOT / "samples" / "ids" / "spbexp" / "SOURCE.md").read_text(encoding="utf-8")
        self.assertIn("MIT license applies only to AeroBIM code", text)
        self.assertIn("raw bytes", text)
        self.assertIn("CRLF→LF", text)
        self.assertIn("Требования к ЦИМ ОК _V.3.1.0", text)
        self.assertIn("1543", text)
        self.assertIn("195 pass / 161 fail", text)


class SpbCgeProfileNegativeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.pack = self.tmp / "pack"
        self.pack.mkdir(parents=True)

    def _copy_smallest(self, *, corrupt: bool = False) -> dict:
        source = PACK_ROOT / SMALLEST_IDS_REL
        target = self.pack / SMALLEST_IDS_REL
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        if corrupt:
            data = bytearray(target.read_bytes())
            data[len(data) // 2] ^= 0xFF
            target.write_bytes(bytes(data))
        real = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        return next(entry for entry in real["files"] if entry["path"] == SMALLEST_IDS_REL)

    def test_corrupted_file_fails_hash_gate(self) -> None:
        entry = self._copy_smallest(corrupt=True)
        _tmp_profile_manifest(self.tmp, files=[{"path": entry["path"]}], pack_root=self.pack)
        with self.assertRaises(OfficialIdsProfileError) as ctx:
            validate_profile(
                self.tmp,
                manifest_path=self.tmp / "manifest.json",
                xsd_path=XSD_PATH,
            )
        self.assertIn("sha256 mismatch", str(ctx.exception))

    def test_missing_file_fails(self) -> None:
        entry = self._copy_smallest()
        _tmp_profile_manifest(self.tmp, files=[{"path": entry["path"]}], pack_root=self.pack)
        (self.pack / SMALLEST_IDS_REL).unlink()
        with self.assertRaises(OfficialIdsProfileError) as ctx:
            validate_profile(
                self.tmp,
                manifest_path=self.tmp / "manifest.json",
                xsd_path=XSD_PATH,
            )
        self.assertIn("file missing", str(ctx.exception))

    def test_undeclared_extra_file_fails(self) -> None:
        entry = self._copy_smallest()
        _tmp_profile_manifest(self.tmp, files=[{"path": entry["path"]}], pack_root=self.pack)
        extra = self.pack / "rii" / "undeclared.ids"
        extra.write_text("<?xml version='1.0'?><ids/>", encoding="utf-8")
        with self.assertRaises(OfficialIdsProfileError) as ctx:
            validate_profile(
                self.tmp,
                manifest_path=self.tmp / "manifest.json",
                xsd_path=XSD_PATH,
            )
        self.assertIn("not declared", str(ctx.exception))

    def test_wrong_declared_ids_schema_version_fails(self) -> None:
        entry = self._copy_smallest()
        manifest = _tmp_profile_manifest(
            self.tmp,
            files=[{"path": entry["path"], "ids_schema_version": "0.9.6"}],
            pack_root=self.pack,
        )
        self.assertEqual(manifest["files"][0]["ids_schema_version"], "0.9.6")
        with self.assertRaises(OfficialIdsProfileError) as ctx:
            load_manifest(self.tmp / "manifest.json")
        self.assertIn("0.9.6", str(ctx.exception))

    def test_non_ids_1_0_document_fails_xsd_gate(self) -> None:
        entry = self._copy_smallest()
        target = self.pack / SMALLEST_IDS_REL
        target.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<ids xmlns="http://example.org/not-ids"><info><title>x</title></info></ids>\n',
            encoding="utf-8",
        )
        entry = dict(entry)
        entry["sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
        entry["size_bytes"] = target.stat().st_size
        _tmp_profile_manifest(self.tmp, files=[entry], pack_root=self.pack)
        with self.assertRaises(OfficialIdsProfileError) as ctx:
            validate_profile(
                self.tmp,
                manifest_path=self.tmp / "manifest.json",
                xsd_path=XSD_PATH,
            )
        self.assertIn("XSD validation failed", str(ctx.exception))

    def test_tampered_manifest_sha256_fails(self) -> None:
        entry = self._copy_smallest()
        _tmp_profile_manifest(
            self.tmp,
            files=[{"path": entry["path"], "sha256": "0" * 64}],
            pack_root=self.pack,
        )
        with self.assertRaises(OfficialIdsProfileError) as ctx:
            validate_profile(
                self.tmp,
                manifest_path=self.tmp / "manifest.json",
                xsd_path=XSD_PATH,
            )
        self.assertIn("sha256 mismatch", str(ctx.exception))

    def test_signed_by_customer_true_rejected(self) -> None:
        payload = _manifest_payload()
        payload["signed_by_customer"] = True
        with self.assertRaises(OfficialIdsProfileError) as ctx:
            parse_official_ids_profile(payload)
        self.assertIn("signed_by_customer", str(ctx.exception))

    def test_closes_rt002_true_rejected(self) -> None:
        payload = _manifest_payload()
        payload["closes_rt002"] = True
        with self.assertRaises(OfficialIdsProfileError) as ctx:
            parse_official_ids_profile(payload)
        self.assertIn("closes_rt002", str(ctx.exception))

    def test_derived_rules_must_not_claim_official(self) -> None:
        payload = _manifest_payload()
        payload["provenance_status"] = "OFFICIAL"
        with self.assertRaises(OfficialIdsProfileError) as ctx:
            parse_official_ids_profile(payload)
        self.assertIn("provenance_status", str(ctx.exception))

    def test_broken_manifest_json_fails(self) -> None:
        broken = self.tmp / "broken.json"
        broken.write_text("{not json", encoding="utf-8")
        with self.assertRaises(OfficialIdsProfileError):
            load_manifest(broken)


if __name__ == "__main__":
    unittest.main()
