from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.domain.models import ReportListFilters
from aerobim.infrastructure.adapters.filesystem_audit_store import FilesystemAuditStore
from aerobim.tools.seed_smoke_report import (
    SMOKE_REPORT_ID,
    SMOKE_TENANT_ID,
    seed_smoke_report,
)

pytest.importorskip("pymupdf", reason="optional pdf-agpl extra")


def preview_dir(storage_dir: Path, report_id: str, tenant_id: str | None) -> Path:
    root = storage_dir if tenant_id is None else storage_dir / "tenants" / tenant_id
    return root / "drawing-assets" / report_id


class SeedSmokeReportTests(unittest.TestCase):
    def test_seed_smoke_report_materializes_runtime_review_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir)

            report = seed_smoke_report(storage_dir)

            self.assertEqual(report.report_id, SMOKE_REPORT_ID)
            self.assertTrue(report.ifc_path.exists())
            self.assertTrue(report.ifc_path.is_relative_to(storage_dir.resolve()))
            self.assertEqual(len(report.issues), 1)
            self.assertEqual(report.issues[0].rule_id, "SMOKE-DRAW-001")
            self.assertIsNotNone(report.issues[0].element_guid)
            self.assertIsNotNone(report.issues[0].problem_zone)
            self.assertEqual(len(report.clash_results), 1)
            self.assertEqual(len(report.drawing_assets), 2)
            previews = preview_dir(storage_dir, report.report_id, SMOKE_TENANT_ID)
            self.assertTrue(previews.exists())
            self.assertEqual(len(list(previews.glob("*.png"))), 2)

    def test_seed_smoke_report_is_idempotent_for_same_storage_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir)

            first = seed_smoke_report(storage_dir)
            second = seed_smoke_report(storage_dir)

            self.assertEqual(first.report_id, second.report_id)
            previews = preview_dir(storage_dir, second.report_id, SMOKE_TENANT_ID)
            self.assertEqual(len(list(previews.glob("*.png"))), 2)

    def test_seeded_report_is_listed_for_the_matching_tenant_only(self) -> None:
        """GET /v1/reports scopes to the principal tenant, so the stamp matters."""

        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir)
            report = seed_smoke_report(storage_dir)
            self.assertEqual(report.tenant_id, SMOKE_TENANT_ID)

            store = FilesystemAuditStore(storage_dir)
            matching = store.list_reports(ReportListFilters(tenant_id=SMOKE_TENANT_ID))
            other = store.list_reports(ReportListFilters(tenant_id="some-other-tenant"))

            self.assertEqual([entry.report_id for entry in matching], [SMOKE_REPORT_ID])
            self.assertEqual(other, [])

    def test_explicit_none_tenant_keeps_the_untenanted_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir)

            report = seed_smoke_report(storage_dir, tenant_id=None)

            self.assertIsNone(report.tenant_id)
            self.assertTrue(preview_dir(storage_dir, report.report_id, None).exists())

    def test_reseed_discards_prior_hitl_journal(self) -> None:
        """Re-running the seed must not leave an accepted finding in the journal."""

        from aerobim.domain.review_event_append import ReviewEventAppendSpec
        from aerobim.infrastructure.adapters.filesystem_review_event_store import (
            FilesystemReviewEventStore,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir)
            report = seed_smoke_report(storage_dir)
            events = FilesystemReviewEventStore(storage_dir)
            events.append_api_event(
                ReviewEventAppendSpec(
                    report_id=report.report_id,
                    event_type="opened",
                    created_at="2026-09-09T00:00:00+00:00",
                    issue_rule_id="SMOKE-DRAW-001",
                    actor="seed-test",
                    note="prior run",
                    latency_ms=1,
                    finding_id=None,
                    previous_state=None,
                    idempotency_key="prior-open",
                    event_id=None,
                )
            )
            self.assertEqual(len(events.list_for_report(report.report_id)), 1)

            seed_smoke_report(storage_dir)

            self.assertEqual(events.list_for_report(report.report_id), [])
