"""T2 evidence integrity: hash recomputation + T1 artifact binding (Wave H).

Anchors (Jul 2026): SLSA provenance practice — an evidence claim must bind to
the verified digest of the actual artifact; evidence-driven CI attestations
(arXiv 2605.21089). Claim boundary: this hardens the *gate*; T2 itself stays
NOT_VERIFIED until a real customer CDE import pack lands (RT-008).
"""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from aerobim.tools.verify_bcf_t2_evidence import verify_bcf_t2_evidence_dir


def _write_pack(
    root: Path,
    *,
    log: bytes = b"import ok",
    shot: bytes = b"\x89PNG\r\n\x1a\n",
    bcf_sha256: str | None = None,
    tamper_log_hash: bool = False,
    extra_hash_entries: dict[str, str] | None = None,
) -> None:
    (root / "import-log.txt").write_bytes(log)
    (root / "screenshot.png").write_bytes(shot)
    log_hash = hashlib.sha256(log).hexdigest()
    if tamper_log_hash:
        log_hash = "0" * 64
    hashes: dict[str, str] = {
        "import-log.txt": log_hash,
        "screenshot.png": hashlib.sha256(shot).hexdigest(),
    }
    if bcf_sha256 is not None:
        hashes["bcf_zip_sha256"] = bcf_sha256
    if extra_hash_entries:
        hashes.update(extra_hash_entries)
    (root / "hashes.json").write_text(json.dumps(hashes), encoding="utf-8")
    (root / "STATUS.json").write_text(
        json.dumps({"status": "VERIFIED", "claim_allowed": True}),
        encoding="utf-8",
    )


def _write_structural(path: Path, *, sha_21: str, sha_30: str) -> None:
    path.write_text(
        json.dumps(
            {
                "artifact_type": "bcf_structural_handoff",
                "bcf_21": {"sha256": sha_21},
                "bcf_30": {"sha256": sha_30},
            }
        ),
        encoding="utf-8",
    )


class T2HashIntegrityTests(unittest.TestCase):
    def test_complete_pack_with_valid_hashes_is_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_pack(root)
            report = verify_bcf_t2_evidence_dir(root)
        self.assertTrue(report["hashes_verified"], msg=report["hash_mismatches"])
        self.assertEqual(report["status"], "available")
        self.assertTrue(report["claim_allowed"])

    def test_tampered_hash_entry_blocks_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_pack(root, tamper_log_hash=True)
            report = verify_bcf_t2_evidence_dir(root)
        self.assertFalse(report["hashes_verified"])
        self.assertFalse(report["claim_allowed"])
        self.assertEqual(report["status"], "not_verified")
        self.assertTrue(any("import-log.txt" in m for m in report["hash_mismatches"]))
        self.assertIn("hash verification failed", report["reason"])

    def test_hash_entry_for_absent_file_blocks_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_pack(root, extra_hash_entries={"missing-artifact.pdf": "ab" * 32})
            report = verify_bcf_t2_evidence_dir(root)
        self.assertFalse(report["hashes_verified"])
        self.assertFalse(report["claim_allowed"])

    def test_required_file_without_hash_entry_blocks_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_pack(root)
            # Drop the screenshot entry: file present, but unbound by any hash.
            hashes_path = root / "hashes.json"
            hashes = json.loads(hashes_path.read_text(encoding="utf-8"))
            del hashes["screenshot.png"]
            hashes_path.write_text(json.dumps(hashes), encoding="utf-8")
            report = verify_bcf_t2_evidence_dir(root)
        self.assertFalse(report["hashes_verified"])
        self.assertTrue(any("screenshot.png" in m for m in report["hash_mismatches"]))
        self.assertFalse(report["claim_allowed"])


class T2ArtifactBindingTests(unittest.TestCase):
    def test_bcf_digest_binds_to_t1_structural_evidence(self) -> None:
        sha = hashlib.sha256(b"real exported bcf").hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_pack(root, bcf_sha256=sha)
            structural = root / "structural.json"
            _write_structural(structural, sha_21=sha, sha_30="c" * 64)
            report = verify_bcf_t2_evidence_dir(root, structural_evidence=structural)
        self.assertTrue(report["bcf_binding"]["checked"])
        self.assertTrue(report["bcf_binding"]["matches"])
        self.assertTrue(report["claim_allowed"])

    def test_foreign_bcf_digest_blocks_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_pack(root, bcf_sha256="d" * 64)
            structural = root / "structural.json"
            _write_structural(structural, sha_21="a" * 64, sha_30="b" * 64)
            report = verify_bcf_t2_evidence_dir(root, structural_evidence=structural)
        self.assertFalse(report["bcf_binding"]["matches"])
        self.assertFalse(report["claim_allowed"])
        self.assertIn("different archive", report["reason"])

    def test_missing_bcf_digest_with_binding_requested_blocks_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_pack(root)
            structural = root / "structural.json"
            _write_structural(structural, sha_21="a" * 64, sha_30="b" * 64)
            report = verify_bcf_t2_evidence_dir(root, structural_evidence=structural)
        self.assertFalse(report["claim_allowed"])

    def test_binding_not_requested_stays_backward_compatible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_pack(root)
            report = verify_bcf_t2_evidence_dir(root)
        self.assertFalse(report["bcf_binding"]["checked"])
        self.assertTrue(report["claim_allowed"])

    def test_missing_artifacts_reason_names_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = verify_bcf_t2_evidence_dir(root)
        self.assertFalse(report["claim_allowed"])
        self.assertIn("import-log.txt", report["reason"])
        self.assertIn("screenshot.png", report["reason"])

    def test_checklist_dry_run_never_claim_allowed(self) -> None:
        from aerobim.tools.verify_bcf_t2_evidence import build_t2_checklist_report

        report = build_t2_checklist_report()
        self.assertTrue(report["dry_run"])
        self.assertFalse(report["claim_allowed"])
        self.assertEqual(len(report["checklist"]), 5)

    def test_eng_readiness_never_flips_claim(self) -> None:
        from aerobim.tools.verify_bcf_t2_evidence import build_t2_eng_readiness_report

        report = build_t2_eng_readiness_report()
        self.assertFalse(report["claim_allowed"])
        self.assertEqual(report["status"], "NOT_VERIFIED")
        self.assertTrue(report["tooling_ready"])
        self.assertTrue(report["t1_structural_evidence"])


if __name__ == "__main__":
    unittest.main()
