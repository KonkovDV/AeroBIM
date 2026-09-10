"""WP-R8 / WP-R14: run passport timings and format coverage. Not an SLA."""

from __future__ import annotations

import copy
import unittest
from datetime import UTC, datetime
from pathlib import Path

from aerobim.core.di.container import Container
from aerobim.domain.finding_provenance import ensure_finding_provenance
from aerobim.domain.models import (
    FindingCategory,
    Severity,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
)
from aerobim.domain.run_passport import (
    SPF_CAP_BYTES,
    build_run_passport,
    classify_submitted_source,
    format_coverage_table,
    passport_from_traces,
    passport_trace,
    stages_are_monotonic,
)
from aerobim.presentation.http.context import ApiContext
from aerobim.presentation.http.report_html import render_report_html


class RunPassportTests(unittest.TestCase):
    def test_stage_timings_present_and_monotonic(self) -> None:
        passport = build_run_passport(
            stage_timings_ms={
                "ingest": 10,
                "ifc": 40,
                "ids": 20,
                "drawing": 5,
                "cross-doc": 8,
                "clash": 12,
                "report": 3,
            }
        )
        self.assertEqual(len(passport["stages"]), 7)
        self.assertTrue(stages_are_monotonic(passport))
        self.assertEqual(passport["stages"][-1]["cumulative_ms"], 98)
        self.assertEqual(passport["stage_timing_basis"], "sources_only")

    def test_per_engine_basis_is_recorded(self) -> None:
        passport = build_run_passport(
            stage_timings_ms={"ifc": 4, "ids": 1},
            timing_basis="per_engine",
        )
        self.assertEqual(passport["stage_timing_basis"], "per_engine")

    def test_passport_trace_roundtrip_survives_without_singleton(self) -> None:
        passport = build_run_passport(
            stage_timings_ms={"ingest": 2, "ifc": 9, "report": 1},
            report_id="a" * 32,
            timing_basis="per_engine",
        )
        recovered = passport_from_traces([passport_trace(passport)])
        self.assertIsNotNone(recovered)
        assert recovered is not None
        self.assertEqual(recovered["report_id"], "a" * 32)
        self.assertEqual(recovered["stage_timing_basis"], "per_engine")
        self.assertEqual(recovered["stages"][1]["duration_ms"], 9)

    def test_serialize_prefers_persisted_passport_trace(self) -> None:
        issue = ensure_finding_provenance(
            ValidationIssue(
                rule_id="REQ-FIRE-001",
                severity=Severity.ERROR,
                message="mismatch",
                category=FindingCategory.IDS_VALIDATION,
                element_guid="guid-1",
            )
        )
        passport = build_run_passport(
            stage_timings_ms={"ingest": 11, "ifc": 22, "ids": 3, "report": 4},
            report_id="d" * 32,
            timing_basis="per_engine",
        )
        report = ValidationReport(
            report_id="d" * 32,
            request_id="hash",
            ifc_path=Path("m.ifc"),
            created_at="2026-09-09T00:00:00+00:00",
            requirements=(),
            issues=(issue,),
            summary=ValidationSummary(0, 1, 1, 0, False),
            tool_traces=(passport_trace(passport),),
        )
        ctx = object.__new__(ApiContext)
        ctx.container = Container()
        payload = ctx.serialize_public_report(report)
        self.assertEqual(payload["run_passport"]["stage_timing_basis"], "per_engine")
        self.assertEqual(payload["run_passport"]["stages"][1]["duration_ms"], 22)
        self.assertNotIn("IfcReinforcingBar = 0", str(payload["calculation_section"]))

    def test_passport_does_not_change_integrity_hash(self) -> None:
        issue = ensure_finding_provenance(
            ValidationIssue(
                rule_id="REQ-FIRE-001",
                severity=Severity.ERROR,
                message="mismatch",
                category=FindingCategory.IDS_VALIDATION,
                element_guid="guid-1",
            )
        )
        report = ValidationReport(
            report_id="c" * 32,
            request_id="hash",
            ifc_path=Path("m.ifc"),
            created_at="2026-09-09T00:00:00+00:00",
            requirements=(),
            issues=(issue,),
            summary=ValidationSummary(0, 1, 1, 0, False),
        )
        before = copy.deepcopy(report.issues)
        ctx = object.__new__(ApiContext)
        ctx.container = Container()
        payload = ctx.serialize_public_report(report)
        self.assertEqual(report.issues, before)
        self.assertIn("run_passport", payload)
        self.assertFalse(hasattr(report.issues[0], "run_passport"))

    def test_passport_states_it_is_not_an_sla(self) -> None:
        passport = build_run_passport(stage_timings_ms={"ingest": 1})
        self.assertFalse(passport["is_sla"])
        self.assertIn("не SLA", passport["disclaimer"])
        html = render_report_html(
            "r" * 32,
            {
                "summary": {
                    "passed": False,
                    "issue_count": 0,
                    "error_count": 0,
                    "warning_count": 0,
                    "requirement_count": 0,
                },
                "issues": [],
                "run_passport": passport,
                "created_at": datetime.now(tz=UTC).isoformat(),
            },
        )
        self.assertIn("не SLA", html)


class FormatCoverageTests(unittest.TestCase):
    def test_rejected_native_formats_are_counted_not_hidden(self) -> None:
        table = format_coverage_table(
            [
                {"name": "model.ifc", "size_bytes": 1024},
                {"name": "federated.nwd", "size_bytes": 2048},
                {"name": "arch.rvt", "size_bytes": 4096},
            ]
        )
        self.assertEqual(table["submitted"], 3)
        self.assertEqual(table["read"], 1)
        self.assertEqual(table["rejected"], 2)
        reasons = {row["suffix"]: row["reason"] for row in table["rows"]}
        self.assertIn("closed format", reasons[".nwd"])
        self.assertIn("closed format", reasons[".rvt"])

    def test_size_limit_rejection_has_reason(self) -> None:
        row = classify_submitted_source(name="huge.ifc", size_bytes=300 * 1024 * 1024)
        self.assertEqual(row["disposition"], "rejected")
        self.assertIn("size limit", row["reason"])
        self.assertIn("SPF cap", row["reason"])

    def test_opened_over_spf_cap_is_read_not_rejected(self) -> None:
        row = classify_submitted_source(
            name="huge.ifc",
            size_bytes=SPF_CAP_BYTES + 1,
            disposition="read",
            reason="opened on disk (RocksDB); over SPF RAM cap; not a silent skip",
        )
        self.assertEqual(row["disposition"], "read")
        self.assertIn("RocksDB", row["reason"])

    def test_sources_from_report_marks_on_disk_over_spf(self) -> None:
        import tempfile

        import aerobim.domain.run_passport as rp

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "huge.ifc"
            path.write_bytes(b"ISO-10303-21;")
            original = rp.SPF_CAP_BYTES
            rp.SPF_CAP_BYTES = 4
            try:
                report = ValidationReport(
                    report_id="e" * 32,
                    request_id="spf",
                    ifc_path=path,
                    created_at="2026-09-09T00:00:00+00:00",
                    requirements=(),
                    issues=(),
                    summary=ValidationSummary(0, 0, 0, 0, False),
                )
                items = rp.sources_from_report(report)
            finally:
                rp.SPF_CAP_BYTES = original
            self.assertEqual(items[0]["disposition"], "read")
            self.assertIn("RocksDB", str(items[0]["reason"]))

    def test_read_formats_match_sources_in_report(self) -> None:
        table = format_coverage_table(
            [
                {"name": "a.ifc", "size_bytes": 10},
                {"name": "ids.xml", "size_bytes": 20},
            ]
        )
        self.assertEqual(table["read"], 2)
        self.assertEqual({row["suffix"] for row in table["rows"]}, {".ifc", ".xml"})


if __name__ == "__main__":
    unittest.main()
