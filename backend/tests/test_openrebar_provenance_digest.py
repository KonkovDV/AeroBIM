from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.models import (
    RequirementSource,
    SourceKind,
    ValidationRequest,
)
from aerobim.infrastructure.adapters.openrebar_evidence_verifier import (
    OpenRebarEvidenceVerifier,
    build_openrebar_provenance_digest,
)
from aerobim.tools.openrebar_provenance_digest import (
    compute_openrebar_provenance_digest,
)

_COMMITTED_OPENREBAR = (
    Path(__file__).resolve().parents[2]
    / "samples"
    / "calculations"
    / "openrebar-slab-03.result.json"
)


def _fixture_payload() -> dict[str, object]:
    payload = json.loads(_COMMITTED_OPENREBAR.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("OpenRebar fixture must be a JSON object")
    return payload


class OpenRebarProvenanceDigestToolTests(unittest.TestCase):
    def test_compute_openrebar_provenance_digest_returns_expected_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "openrebar.result.json"
            payload = _fixture_payload()
            report_path.write_text(json.dumps(payload), encoding="utf-8")

            result = compute_openrebar_provenance_digest(report_path)

            self.assertEqual(result["contract_id"], "OpenRebar.reinforcement.report.v1")
            self.assertEqual(result["schema_version"], "1.0.0")
            self.assertEqual(result["project_code"], "Residential Tower Alpha")
            self.assertEqual(result["slab_id"], "SLAB-03")
            self.assertEqual(
                result["provenance_digest"],
                build_openrebar_provenance_digest(payload),
            )

    def test_compute_openrebar_provenance_digest_raises_for_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "openrebar.result.json"
            report_path.write_text("{invalid-json", encoding="utf-8")

            with self.assertRaises(ValueError):
                compute_openrebar_provenance_digest(report_path)

    def test_compute_openrebar_provenance_digest_raises_for_non_object_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "openrebar.result.json"
            report_path.write_text("[1,2,3]", encoding="utf-8")

            with self.assertRaises(ValueError):
                compute_openrebar_provenance_digest(report_path)

    def test_committed_openrebar_fixture_sverka_without_digest_mismatch(self) -> None:
        if not _COMMITTED_OPENREBAR.is_file():
            self.skipTest("committed OpenRebar fixture missing")
        payload = _fixture_payload()
        digest = build_openrebar_provenance_digest(payload)
        with tempfile.TemporaryDirectory() as tmp_dir:
            ifc = Path(tmp_dir) / "m.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            issues = OpenRebarEvidenceVerifier().verify(
                ValidationRequest(
                    request_id="openrebar-fixture",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="R|IFCWALL|P|T|1",
                        source_kind=SourceKind.STRUCTURED_TEXT,
                    ),
                    project_name="Residential Tower Alpha",
                    reinforcement_report_path=_COMMITTED_OPENREBAR,
                    reinforcement_source_digest=digest,
                )
            )
        rules = {issue.rule_id for issue in issues}
        self.assertNotIn("OPENREBAR-PROVENANCE-DIGEST", rules)
        self.assertNotIn("OPENREBAR-CONTRACT", rules)
        self.assertNotIn("OPENREBAR-OPT-FALLBACK", rules)
        self.assertNotIn("OPENREBAR-OPT-STRATEGY", rules)


if __name__ == "__main__":
    unittest.main()
