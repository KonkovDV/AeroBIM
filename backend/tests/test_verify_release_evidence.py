"""Focused tests for release evidence verifier."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.tools.verify_release_evidence import verify_release_evidence

DAY = "2026-08-06"
SHA = "d96a59ac6704357336ae46f7d61f6435be4c6a2c"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    _write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _minimal_repo(tmp: Path, *, publishable: bool = False, closes_rt: bool = False) -> Path:
    evidence = tmp / "docs" / "evidence"
    customer = tmp / "docs" / "customer"
    quality = tmp / "docs" / "quality"
    audit = tmp / "audit" / "evidence"

    sprint2 = {
        "artifact_type": "sprint2_baseline_evidence_alias",
        "canonical_artifact_type": "sprint2_synthetic_baseline",
        "claim_level": "synthetic_only",
        "customer_precision_claim_publishable": publishable,
        "precision_claim_publishable": publishable,
        "customer_accuracy_not_established": True,
        "closes_rt001": closes_rt,
        "commit_sha": SHA,
        "checkpoint": "NO_GO",
    }
    runtime = {
        "artifact_type": "aerobim_runtime_baseline",
        "commit_sha": SHA,
        "quality_gates": {
            "ruff": "PASS",
            "mypy": "PASS",
            "pytest": "PASS",
            "vitest": "PASS",
            "build": "PASS",
        },
    }
    release = {
        "artifact_type": "aerobim_release_status",
        "commit_sha": SHA,
        "checkpoint": "NO_GO",
        "claim_level": "synthetic_only",
        "verdict_candidate": "ENGINEERING_READY_CUSTOMER_BLOCKED",
        "customer_intake_gate": {"status": "BLOCKED_NO_CUSTOMER_DATA"},
    }
    intake = {
        "artifact_type": "customer_intake_gate",
        "claim_level": "not_ready",
        "gates": {"precision_claim_publishable": False},
    }

    _write_json(evidence / "sprint2-baseline-evidence.json", sprint2)
    _write_json(evidence / "runtime-baseline-latest.json", runtime)
    _write_json(evidence / f"release-status-{DAY}.json", release)
    _write_json(audit / "customer-intake-gate.json", intake)

    for name in (
        f"SPRINT2_BASELINE_REPORT_{DAY}.md",
        "sprint2-baseline-report.md",
    ):
        _write(
            evidence / name,
            "# SYNTHETIC/FIXTURE ONLY\n# CUSTOMER ACCURACY NOT ESTABLISHED\n",
        )
    for name in (
        f"SPRINT2_BASELINE_REPORT_{DAY}.pdf",
        "sprint2-baseline-report.pdf",
    ):
        # Minimal non-empty PDF-sized blob for size gate.
        (evidence / name).parent.mkdir(parents=True, exist_ok=True)
        (evidence / name).write_bytes(b"%PDF-1.4\n" + b"x" * 120)

    _write(customer / "CUSTOMER_ONE_PAGER.md", "# one pager\n")
    _write(
        customer / "CUSTOMER_OUTREACH_TRACKER.csv",
        "organization,segment,contact_role,contact_name,channel,"
        "date_contacted,response,demo_agreed,pilot_agreed,data_available,"
        "expert_available,NDA_required,next_step,owner,notes\n",
    )
    _write(customer / f"CUSTOMER_DEMO_PROTOCOL_{DAY}.md", "# demo\n")
    _write(quality / f"RELEASE_EVIDENCE_INDEX_{DAY}.md", "# index\n")
    _write(quality / f"RELEASE_STATUS_{DAY}.md", "# status\n")
    return tmp


class VerifyReleaseEvidenceTests(unittest.TestCase):
    def test_ok_on_consistent_fixture_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            repo = _minimal_repo(Path(tmp_name))
            result = verify_release_evidence(repo=repo, day=DAY, complete=True)
            self.assertTrue(result["ok"], msg=result["errors"])
            self.assertEqual(result["verification"], "passed")

    def test_fails_when_publishable_without_intake(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            repo = _minimal_repo(Path(tmp_name), publishable=True)
            result = verify_release_evidence(repo=repo, day=DAY, complete=True)
            self.assertFalse(result["ok"])
            joined = " ".join(result["errors"])
            self.assertIn("customer_precision", joined)

    def test_fails_when_closes_rt001(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            repo = _minimal_repo(Path(tmp_name), closes_rt=True)
            result = verify_release_evidence(repo=repo, day=DAY, complete=True)
            self.assertFalse(result["ok"])
            self.assertTrue(any("closes_rt001" in e for e in result["errors"]))

    def test_fails_on_commit_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            repo = _minimal_repo(Path(tmp_name))
            runtime_path = repo / "docs" / "evidence" / "runtime-baseline-latest.json"
            payload = json.loads(runtime_path.read_text(encoding="utf-8"))
            payload["commit_sha"] = "deadbeef" * 5
            runtime_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            result = verify_release_evidence(repo=repo, day=DAY, complete=True)
            self.assertFalse(result["ok"])
            self.assertTrue(any("commit_sha mismatch" in e for e in result["errors"]))

    def test_fails_on_missing_dated_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            repo = _minimal_repo(Path(tmp_name))
            (repo / "docs" / "evidence" / f"SPRINT2_BASELINE_REPORT_{DAY}.pdf").unlink()
            result = verify_release_evidence(repo=repo, day=DAY, complete=True)
            self.assertFalse(result["ok"])
            self.assertTrue(any("SPRINT2_BASELINE_REPORT" in e for e in result["errors"]))

    def test_fails_when_runtime_gate_not_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            repo = _minimal_repo(Path(tmp_name))
            runtime_path = repo / "docs" / "evidence" / "runtime-baseline-latest.json"
            payload = json.loads(runtime_path.read_text(encoding="utf-8"))
            payload["quality_gates"]["pytest"] = "FAIL"
            runtime_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            result = verify_release_evidence(repo=repo, day=DAY, complete=True)
            self.assertFalse(result["ok"])
            self.assertTrue(any("quality_gates.pytest" in e for e in result["errors"]))


if __name__ == "__main__":
    unittest.main()
