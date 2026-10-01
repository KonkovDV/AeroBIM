"""TR-223 guard (Red Team A4): the evidence bundle freezes a check-coverage snapshot
with an algorithm_version + report binding, so the historical coverage map is
reproducible even if the coverage derivation later changes."""

from __future__ import annotations

import json
from pathlib import Path

from aerobim.domain.check_coverage import COVERAGE_ALGORITHM_VERSION
from aerobim.tools.export_evidence_bundle import export_evidence_bundle


def test_bundle_writes_frozen_coverage_snapshot(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    pack = repo_root / "samples" / "benchmarks" / "project-package-techlab-demo.json"
    assert pack.is_file(), f"missing pack: {pack}"

    manifest = export_evidence_bundle(
        pack_path=pack,
        output_dir=tmp_path / "bundle",
        storage_dir=tmp_path / "storage",
    )

    snapshot_path = tmp_path / "bundle" / "check_coverage.json"
    assert snapshot_path.is_file()
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))

    assert snapshot["artifact"] == "check-coverage-snapshot"
    assert snapshot["algorithm_version"] == COVERAGE_ALGORITHM_VERSION
    assert snapshot["report_id"] == manifest["report_id"]
    assert snapshot["reproducibility_hash"] == manifest["reproducibility_hash"]
    assert snapshot["report_content_sha256"]
    assert isinstance(snapshot["coverage"], dict) and snapshot["coverage"]
    # Verdict-neutral (ADR-001): the coverage snapshot must not leak summary.passed.
    assert '"passed"' not in json.dumps(snapshot["coverage"])
    # Listed + content-hashed as a first-class bundle artifact.
    assert manifest["artifacts"]["check_coverage.json"] is True
    assert "check_coverage.json" in manifest["output_file_sha256"]
