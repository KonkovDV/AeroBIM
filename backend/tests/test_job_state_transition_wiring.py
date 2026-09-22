"""Verify that AnalyzeProjectPackageJobRunner wires JobRecord.transition() and
stage tracking correctly.

These tests focus exclusively on the state-machine / stage-progress layer that
was added in feat/p0-job-state-transition.  Job-store behaviour and
cancellation semantics are covered by test_analyze_project_package_job_store.py
and test_analyze_job_recovery.py.
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import Any

from aerobim.application.use_cases.analyze_project_package_jobs import (
    AnalyzeProjectPackageJobRunner,
)
from aerobim.domain.models import (
    AnalyzeProjectPackageJob,
    JobStatus,
    RequirementSource,
    ValidationRequest,
)
from aerobim.infrastructure.adapters.in_memory_analyze_project_package_job_store import (
    InMemoryAnalyzeProjectPackageJobStore,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _request(request_id: str = "req-1") -> ValidationRequest:
    return ValidationRequest(
        request_id=request_id,
        ifc_path=None,
        requirement_source=RequirementSource(text="REQ"),
    )


def _queued_job(job_id: str, request_id: str = "req-1") -> AnalyzeProjectPackageJob:
    return AnalyzeProjectPackageJob(
        job_id=job_id,
        request_id=request_id,
        status=JobStatus.QUEUED,
        created_at="2026-01-01T00:00:00+00:00",
    )


class _CapturingLogger:
    """Collect all log calls for later assertion."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def _record(self, level: str, msg: str, **kwargs: object) -> None:
        self.calls.append({"level": level, "msg": msg, **kwargs})

    def info(self, msg: str, **kwargs: object) -> None:
        self._record("info", msg, **kwargs)

    def error(self, msg: str, **kwargs: object) -> None:
        self._record("error", msg, **kwargs)

    def warning(self, msg: str, **kwargs: object) -> None:
        self._record("warning", msg, **kwargs)

    def by_msg(self, fragment: str) -> list[dict[str, Any]]:
        return [c for c in self.calls if fragment in c["msg"]]


class _SuccessAnalyze:
    """Always succeeds and returns a deterministic report."""

    def __init__(self, report_id: str = "report-ok") -> None:
        self._report_id = report_id
        self.calls = 0

    def execute(self, request: ValidationRequest) -> SimpleNamespace:
        self.calls += 1
        return SimpleNamespace(report_id=self._report_id, request_id=request.request_id)


class _FailingAnalyze:
    """Always raises."""

    def execute(self, request: ValidationRequest) -> SimpleNamespace:
        raise RuntimeError("synthetic analyze failure")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class JobRecordTransitionWiringTests(unittest.TestCase):
    # ------------------------------------------------------------------
    # 1. Happy path — all stages complete, SUCCEEDED transition fires
    # ------------------------------------------------------------------
    def test_successful_run_logs_all_three_stages_and_100_pct(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore()
        job_id = "a" * 32
        store.create(_queued_job(job_id))

        logger = _CapturingLogger()
        runner = AnalyzeProjectPackageJobRunner(_SuccessAnalyze(), store, logger)
        runner.run(job_id, _request())

        stage_started = logger.by_msg("stage started")
        stage_finished = logger.by_msg("stage finished")
        completed = logger.by_msg("async job completed")

        # Three stages started.
        started_names = {c["stage"] for c in stage_started}
        self.assertEqual(
            started_names,
            {"ingestion", "deterministic_validation", "evidence_assembly"},
        )

        # All three finished with success=True.
        for entry in stage_finished:
            self.assertTrue(
                entry.get("success", False),
                f"stage {entry.get('stage')} should have succeeded",
            )

        # Completion log carries progress_pct=100 and full stages list.
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0]["progress_pct"], 100)
        self.assertIn("stages", completed[0])
        stage_names_in_log = {s["stage_name"] for s in completed[0]["stages"]}
        self.assertIn("evidence_assembly", stage_names_in_log)

    # ------------------------------------------------------------------
    # 2. Failure path — analyze raises, stages marked failed, error logged
    # ------------------------------------------------------------------
    def test_failed_run_marks_open_stages_failed_and_logs_them(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore()
        job_id = "b" * 32
        store.create(_queued_job(job_id))

        logger = _CapturingLogger()
        runner = AnalyzeProjectPackageJobRunner(_FailingAnalyze(), store, logger)
        runner.run(job_id, _request())

        # Job in store must be FAILED.
        final = store.get(job_id)
        assert final is not None
        self.assertEqual(final.status, JobStatus.FAILED)

        # Error log must include stages dict so ops can identify which stage failed.
        error_logs = logger.by_msg("async job failed")
        self.assertEqual(len(error_logs), 1)
        self.assertIn("stages", error_logs[0])
        stages = error_logs[0]["stages"]
        # At least ingestion and deterministic stages were opened before failure.
        stage_names = {s["stage_name"] for s in stages}
        self.assertIn("ingestion", stage_names)
        self.assertIn("deterministic_validation", stage_names)
        # All open stages must have status FAILED (not RUNNING).
        for s in stages:
            self.assertNotEqual(
                s["status"],
                "RUNNING",
                f"stage {s['stage_name']} was left RUNNING after failure",
            )

    # ------------------------------------------------------------------
    # 3. Stage order — ingestion starts before deterministic
    # ------------------------------------------------------------------
    def test_stage_start_order_ingestion_before_deterministic(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore()
        job_id = "c" * 32
        store.create(_queued_job(job_id))

        logger = _CapturingLogger()
        runner = AnalyzeProjectPackageJobRunner(_SuccessAnalyze(), store, logger)
        runner.run(job_id, _request())

        starts = logger.by_msg("stage started")
        names_in_order = [c["stage"] for c in starts]
        self.assertIn("ingestion", names_in_order)
        self.assertIn("deterministic_validation", names_in_order)
        self.assertLess(
            names_in_order.index("ingestion"),
            names_in_order.index("deterministic_validation"),
            "ingestion must start before deterministic_validation",
        )

    # ------------------------------------------------------------------
    # 4. progress_pct rises monotonically through the run
    # ------------------------------------------------------------------
    def test_progress_pct_never_decreases_through_the_run(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore()
        job_id = "d" * 32
        store.create(_queued_job(job_id))

        logger = _CapturingLogger()
        runner = AnalyzeProjectPackageJobRunner(_SuccessAnalyze(), store, logger)
        runner.run(job_id, _request())

        pcts = [
            c["progress_pct"]
            for c in logger.calls
            if "progress_pct" in c
        ]
        self.assertTrue(len(pcts) >= 2, "expected at least two progress_pct log entries")
        for i in range(1, len(pcts)):
            self.assertGreaterEqual(
                pcts[i],
                pcts[i - 1],
                f"progress_pct decreased from {pcts[i-1]} to {pcts[i]} at log index {i}",
            )

    # ------------------------------------------------------------------
    # 5. Not-claimable job — runner returns early, no stage logs emitted
    # ------------------------------------------------------------------
    def test_not_claimable_job_emits_no_stage_logs(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore()
        job_id = "e" * 32
        # Job is never created: mark_running returns None.

        logger = _CapturingLogger()
        runner = AnalyzeProjectPackageJobRunner(_SuccessAnalyze(), store, logger)
        runner.run(job_id, _request())

        self.assertEqual(logger.by_msg("stage started"), [])
        self.assertEqual(logger.by_msg("stage finished"), [])

    # ------------------------------------------------------------------
    # 6. Job store sees SUCCEEDED after successful run
    # ------------------------------------------------------------------
    def test_store_job_is_succeeded_with_correct_report_id(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore()
        job_id = "f" * 32
        store.create(_queued_job(job_id))

        runner = AnalyzeProjectPackageJobRunner(
            _SuccessAnalyze(report_id="rpt-xyz"),
            store,
            _CapturingLogger(),
        )
        runner.run(job_id, _request())

        final = store.get(job_id)
        assert final is not None
        self.assertEqual(final.status, JobStatus.SUCCEEDED)
        self.assertEqual(final.report_id, "rpt-xyz")


if __name__ == "__main__":
    unittest.main()
