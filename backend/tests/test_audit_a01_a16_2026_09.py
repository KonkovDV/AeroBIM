"""Regression counterexamples for static-audit items A01–A08, A13, B01.

Synthetic fixtures only. Does not claim product accuracy, SLA, or CDE import.
"""

from __future__ import annotations

import math
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from aerobim.application.services.analyze_orchestrators import _advisory_object_kind
from aerobim.application.services.cross_document_contradictions import (
    CrossDocumentContradictionDetector,
)
from aerobim.application.use_cases.analyze_project_package_jobs import (
    AnalyzeProjectPackageJobRunner,
    SubmitAnalyzeProjectPackageJobUseCase,
    _LeaseHeartbeat,
)
from aerobim.domain.analyze_job_idempotency import (
    IdempotencyPayloadConflictError,
    JobConcurrencyLimitError,
    analyze_job_payload_fingerprint,
    fingerprints_conflict,
)
from aerobim.domain.models import (
    AnalyzeProjectPackageJob,
    ComparisonOperator,
    ConflictKind,
    DrawingSource,
    FindingCategory,
    JobStatus,
    ParsedRequirement,
    RequirementSource,
    Severity,
    SourceKind,
    ToleranceConfig,
    ValidationRequest,
)
from aerobim.domain.quantity import parse_quantity, si_compare
from aerobim.infrastructure.adapters.in_memory_analyze_project_package_job_store import (
    InMemoryAnalyzeProjectPackageJobStore,
)


def _detector() -> CrossDocumentContradictionDetector:
    return CrossDocumentContradictionDetector(ToleranceConfig(), Severity.ERROR)


def _req(
    *,
    value: str,
    unit: str | None,
    kind: SourceKind,
    source: str = "",
    rule_id: str = "R1",
    target_ref: str | None = None,
    operator: ComparisonOperator = ComparisonOperator.EQUALS,
    pset: str = "Qto_WallBaseQuantities",
    prop: str = "Width",
) -> ParsedRequirement:
    return ParsedRequirement(
        rule_id=rule_id,
        ifc_entity="IFCWALL",
        property_set=pset,
        property_name=prop,
        expected_value=value,
        unit=unit,
        source=source,
        source_kind=kind,
        target_ref=target_ref,
        operator=operator,
    )


class A01QuantityStringEarlyReturnTests(unittest.TestCase):
    def test_same_digits_different_units_conflict_both_orders(self) -> None:
        detector = _detector()
        for left, right in (("1", "1"), ("1", "1")):
            self.assertTrue(detector.values_conflict(left, "m", right, "mm"))
            self.assertTrue(detector.values_conflict(right, "mm", left, "m"))

    def test_metre_vs_square_metre_is_unit_mismatch(self) -> None:
        detector = _detector()
        self.assertTrue(detector.values_conflict("1", "m", "1", "m2"))
        self.assertEqual(
            detector.classify_conflict_kind("1", "m", "1", "m²"),
            ConflictKind.UNIT_MISMATCH,
        )

    def test_metre_equals_thousand_mm_and_cyrillic_metre(self) -> None:
        detector = _detector()
        self.assertFalse(detector.values_conflict("1", "m", "1000", "mm"))
        self.assertFalse(detector.values_conflict("1000", "mm", "1", "m"))
        self.assertFalse(detector.values_conflict("1", "m", "1", "м"))

    def test_none_and_unparsed_do_not_invent_match(self) -> None:
        detector = _detector()
        self.assertFalse(detector.values_conflict(None, "m", "1", "m"))
        self.assertTrue(detector.values_conflict("REI60", None, "REI90", None))
        self.assertTrue(detector.values_conflict("1", "m", "not-a-number", "m"))

    def test_detect_emits_hard_conflict_for_1m_vs_1mm(self) -> None:
        detector = _detector()
        issues = detector.detect(
            [
                _req(value="1", unit="m", kind=SourceKind.STRUCTURED_TEXT, source="spec.txt"),
                _req(value="1", unit="mm", kind=SourceKind.CALCULATION, source="calc.txt"),
            ]
        )
        hard = [i for i in issues if i.conflict_kind is ConflictKind.HARD_CONFLICT]
        self.assertEqual(len(hard), 1)


class A02AnglePercentSiTests(unittest.TestCase):
    def test_180_deg_equals_pi_rad(self) -> None:
        deg = parse_quantity(180.0, "deg")
        rad = parse_quantity(math.pi, "rad")
        self.assertTrue(si_compare(deg, rad, epsilon=math.radians(0.1)))
        self.assertTrue(si_compare(rad, deg, epsilon=math.radians(0.1)))

    def test_percent_ratio_scale(self) -> None:
        self.assertTrue(si_compare(parse_quantity(100.0, "%"), parse_quantity(1.0, "ratio")))
        self.assertFalse(si_compare(parse_quantity(1.0, "%"), parse_quantity(1.0, "ratio")))

    def test_force_and_grouped_ru_number(self) -> None:
        self.assertTrue(si_compare(parse_quantity(1.0, "kN"), parse_quantity(1000.0, "N")))
        from aerobim.domain.quantity import parse_localized_number

        self.assertEqual(parse_localized_number("1 254,5"), 1254.5)

    def test_mm_prefix_case_is_not_megametre(self) -> None:
        unknown = parse_quantity(1.0, "Mm")
        self.assertIsNone(unknown.si_value)


class A03DocumentIdentityAndIntervalsTests(unittest.TestCase):
    def test_two_drawings_same_kind_still_compared(self) -> None:
        detector = _detector()
        issues = detector.detect(
            [
                _req(
                    value="200",
                    unit="mm",
                    kind=SourceKind.DRAWING,
                    source="AR-01.pdf",
                    rule_id="d1",
                ),
                _req(
                    value="150",
                    unit="mm",
                    kind=SourceKind.DRAWING,
                    source="AR-02.pdf",
                    rule_id="d2",
                ),
            ]
        )
        self.assertTrue(any(i.category is FindingCategory.CROSS_DOCUMENT for i in issues))

    def test_different_target_refs_are_not_paired(self) -> None:
        detector = _detector()
        issues = detector.detect(
            [
                _req(
                    value="1",
                    unit="m",
                    kind=SourceKind.STRUCTURED_TEXT,
                    target_ref="guid-a",
                    source="a",
                ),
                _req(
                    value="2",
                    unit="m",
                    kind=SourceKind.CALCULATION,
                    target_ref="guid-b",
                    source="b",
                ),
            ]
        )
        self.assertEqual(issues, [])

    def test_gte_compatible_and_empty_interval(self) -> None:
        detector = _detector()
        compatible = detector.detect(
            [
                _req(
                    value="3",
                    unit="m",
                    kind=SourceKind.STRUCTURED_TEXT,
                    operator=ComparisonOperator.GREATER_OR_EQUAL,
                    source="a",
                ),
                _req(
                    value="4",
                    unit="m",
                    kind=SourceKind.CALCULATION,
                    operator=ComparisonOperator.GREATER_OR_EQUAL,
                    source="b",
                ),
            ]
        )
        self.assertEqual(compatible, [])
        empty = detector.detect(
            [
                _req(
                    value="4",
                    unit="m",
                    kind=SourceKind.STRUCTURED_TEXT,
                    operator=ComparisonOperator.GREATER_OR_EQUAL,
                    source="a",
                ),
                _req(
                    value="3",
                    unit="m",
                    kind=SourceKind.CALCULATION,
                    operator=ComparisonOperator.LESS_OR_EQUAL,
                    source="b",
                ),
            ]
        )
        self.assertTrue(empty)

    def test_permutation_invariant(self) -> None:
        detector = _detector()
        a = _req(value="1", unit="m", kind=SourceKind.STRUCTURED_TEXT, source="a")
        b = _req(value="2", unit="m", kind=SourceKind.CALCULATION, source="b")
        first = {frozenset((i.expected_value, i.observed_value)) for i in detector.detect([a, b])}
        second = {frozenset((i.expected_value, i.observed_value)) for i in detector.detect([b, a])}
        self.assertEqual(first, second)


class A04IdempotencyFingerprintTests(unittest.TestCase):
    def _request(self, **kwargs: object) -> ValidationRequest:
        payload = dict(
            request_id="req-1",
            ifc_path=Path("sample.ifc"),
            requirement_source=RequirementSource(text="height = 3 m"),
        )
        payload.update(kwargs)
        return ValidationRequest(**payload)  # type: ignore[arg-type]

    def test_inline_text_change_conflicts(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore()
        submit = SubmitAnalyzeProjectPackageJobUseCase(store)
        first = submit.execute(self._request(), idempotency_key="k1")
        other = self._request(
            request_id="req-2",
            requirement_source=RequirementSource(text="height = 4 m"),
        )
        with self.assertRaises(IdempotencyPayloadConflictError):
            submit.execute(other, idempotency_key="k1")
        self.assertEqual(store.get(first.job_id).request_id, "req-1")  # type: ignore[union-attr]

    def test_request_id_alone_does_not_conflict(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore()
        submit = SubmitAnalyzeProjectPackageJobUseCase(store)
        first = submit.execute(self._request(request_id="a"), idempotency_key="k1")
        second = submit.execute(self._request(request_id="b"), idempotency_key="k1")
        self.assertEqual(first.job_id, second.job_id)

    def test_provenance_mode_is_in_fingerprint(self) -> None:
        a = analyze_job_payload_fingerprint(self._request())
        b = analyze_job_payload_fingerprint(self._request(reinforcement_provenance_mode="enforced"))
        self.assertNotEqual(a, b)

    def test_legacy_missing_fingerprint_conflicts(self) -> None:
        self.assertTrue(fingerprints_conflict(None, "abc"))
        self.assertFalse(fingerprints_conflict("abc", "abc"))

    def test_file_bytes_change_at_same_path(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "req.txt"
            path.write_text("one", encoding="utf-8")
            first = analyze_job_payload_fingerprint(
                ValidationRequest(
                    request_id="r",
                    ifc_path=None,
                    requirement_source=RequirementSource(path=path, text=""),
                )
            )
            path.write_text("two-longer", encoding="utf-8")
            second = analyze_job_payload_fingerprint(
                ValidationRequest(
                    request_id="r",
                    ifc_path=None,
                    requirement_source=RequirementSource(path=path, text=""),
                )
            )
            self.assertNotEqual(first, second)


class A05A06A07JobClaimTests(unittest.TestCase):
    def test_second_claim_is_rejected(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore()
        job = AnalyzeProjectPackageJob(
            job_id="job-claim",
            request_id="r",
            status=JobStatus.QUEUED,
            created_at="2026-09-16T00:00:00+00:00",
        )
        store.create(job)
        first = store.mark_running("job-claim", owner="runner-a")
        second = store.mark_running("job-claim", owner="runner-b")
        self.assertIsNotNone(first)
        self.assertIsNone(second)
        stale = store.mark_succeeded("job-claim", "report-x", owner="runner-b")
        self.assertIsNone(stale)
        ok = store.mark_succeeded("job-claim", "report-a", owner="runner-a")
        self.assertIsNotNone(ok)
        assert ok is not None
        self.assertEqual(ok.report_id, "report-a")

    def test_two_runners_only_one_analyze(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore()
        store.create(
            AnalyzeProjectPackageJob(
                job_id="job-race",
                request_id="r",
                status=JobStatus.QUEUED,
                created_at="2026-09-16T00:00:00+00:00",
            )
        )
        barrier = threading.Barrier(2)
        calls: list[int] = []
        lock = threading.Lock()

        class _Analyze:
            def execute(self, request: object) -> object:
                with lock:
                    calls.append(1)
                return SimpleNamespace(report_id="rep")

        def _run() -> None:
            barrier.wait()
            AnalyzeProjectPackageJobRunner(
                _Analyze(),
                store,
                SimpleNamespace(info=lambda *a, **k: None, error=lambda *a, **k: None),
            ).run("job-race", SimpleNamespace(request_id="r"))

        threads = [threading.Thread(target=_run) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)
        self.assertEqual(sum(calls), 1)
        self.assertEqual(store.get("job-race").status, JobStatus.SUCCEEDED)  # type: ignore[union-attr]

    def test_heartbeat_survives_lease_periods(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore(lease_seconds=1)
        store.create(
            AnalyzeProjectPackageJob(
                job_id="job-long",
                request_id="r",
                status=JobStatus.QUEUED,
                created_at="2026-09-16T00:00:00+00:00",
            )
        )
        started = threading.Event()
        release = threading.Event()

        class _Analyze:
            def execute(self, request: object) -> object:
                started.set()
                if not release.wait(timeout=4):
                    raise TimeoutError("analyze was not released")
                return SimpleNamespace(report_id="rep-long")

        def _run() -> None:
            AnalyzeProjectPackageJobRunner(
                _Analyze(),
                store,
                SimpleNamespace(info=lambda *a, **k: None, error=lambda *a, **k: None),
            ).run("job-long", SimpleNamespace(request_id="r"))

        thread = threading.Thread(target=_run)
        thread.start()
        self.assertTrue(started.wait(timeout=2))
        time.sleep(1.6)
        reclaimed = store.reclaim_stale_running()
        self.assertEqual(reclaimed, [])
        self.assertEqual(store.get("job-long").status, JobStatus.RUNNING)  # type: ignore[union-attr]
        release.set()
        thread.join(timeout=5)
        self.assertEqual(store.get("job-long").status, JobStatus.SUCCEEDED)  # type: ignore[union-attr]

    def test_lost_lease_does_not_publish(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore(lease_seconds=1)
        store.create(
            AnalyzeProjectPackageJob(
                job_id="job-dead",
                request_id="r",
                status=JobStatus.QUEUED,
                created_at="2026-09-16T00:00:00+00:00",
            )
        )
        claimed = store.mark_running("job-dead", owner="alive")
        self.assertIsNotNone(claimed)
        # Simulate a dead worker: no heartbeat, reclaim, then stale owner commit.
        time.sleep(1.1)
        reclaimed = store.reclaim_stale_running()
        self.assertTrue(reclaimed)
        self.assertIsNone(store.mark_succeeded("job-dead", "late", owner="alive"))
        self.assertEqual(store.get("job-dead").status, JobStatus.FAILED)  # type: ignore[union-attr]

    def test_heartbeat_exception_marks_lease_lost(self) -> None:
        class _BoomStore:
            def heartbeat(self, job_id: str, *, lease_seconds: int = 120, owner: str | None = None):
                raise RuntimeError("redis unavailable")

        keeper = _LeaseHeartbeat(
            _BoomStore(),  # type: ignore[arg-type]
            "job-boom",
            owner="worker-1",
            interval_seconds=0.05,
            lease_seconds=1,
        )
        keeper.start()
        deadline = time.time() + 2.0
        while time.time() < deadline and not keeper.lost():
            time.sleep(0.05)
        try:
            self.assertTrue(keeper.lost())
        finally:
            keeper.stop()

    def test_concurrent_submit_respects_limit(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore()
        submit = SubmitAnalyzeProjectPackageJobUseCase(store)
        errors: list[BaseException] = []
        barrier = threading.Barrier(4)

        def _one(index: int) -> None:
            barrier.wait()
            try:
                submit.execute(
                    ValidationRequest(
                        request_id=f"r-{index}-{uuid4().hex}",
                        ifc_path=Path(f"m-{index}.ifc"),
                        requirement_source=RequirementSource(text="x"),
                        tenant_id="tenant-a",
                    ),
                    max_concurrent_per_tenant=2,
                )
            except JobConcurrencyLimitError as exc:
                errors.append(exc)

        threads = [threading.Thread(target=_one, args=(i,)) for i in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)
        active = store.count_active_for_tenant("tenant-a")
        self.assertLessEqual(active, 2)
        self.assertGreaterEqual(len(errors), 1)

    def test_failed_replay_returns_terminal_job(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore()
        submit = SubmitAnalyzeProjectPackageJobUseCase(store)
        request = ValidationRequest(
            request_id="r-fail",
            ifc_path=Path("m.ifc"),
            requirement_source=RequirementSource(text="x"),
            tenant_id="t1",
        )
        job = submit.execute(request, idempotency_key="fail-key")
        store.mark_running(job.job_id)
        store.mark_failed(job.job_id, "boom")
        again = submit.execute(request, idempotency_key="fail-key")
        self.assertEqual(again.job_id, job.job_id)
        self.assertEqual(again.status, JobStatus.FAILED)


class A08SinglePersistTests(unittest.TestCase):
    def test_execute_saves_once(self) -> None:
        from aerobim.application.use_cases.analyze_project_package import (
            AnalyzeProjectPackageUseCase,
        )
        from aerobim.domain.models import ValidationReport
        from aerobim.infrastructure.adapters.template_remark_generator import (
            TemplateRemarkGenerator,
        )

        class _Extractor:
            def extract(self, _source):
                return [
                    ParsedRequirement(
                        rule_id="R-m",
                        ifc_entity="IFCWALL",
                        property_set="Qto_WallBaseQuantities",
                        property_name="Width",
                        expected_value="1",
                        unit="m",
                        source_kind=SourceKind.STRUCTURED_TEXT,
                    )
                ]

            def synthesize(self, _source):
                return [
                    ParsedRequirement(
                        rule_id="R-mm",
                        ifc_entity="IFCWALL",
                        property_set="Qto_WallBaseQuantities",
                        property_name="Width",
                        expected_value="1",
                        unit="mm",
                        source_kind=SourceKind.CALCULATION,
                    )
                ]

            def analyze(self, _source):
                return []

        class _Store:
            def __init__(self) -> None:
                self.saves = 0
                self._reports: dict[str, ValidationReport] = {}

            def save(self, report: ValidationReport) -> str:
                self.saves += 1
                self._reports[report.report_id] = report
                return report.report_id

            def get(self, report_id: str) -> ValidationReport | None:
                return self._reports.get(report_id)

            def list_reports(self) -> list:
                return []

        store = _Store()
        use_case = AnalyzeProjectPackageUseCase(
            requirement_extractor=_Extractor(),
            narrative_rule_synthesizer=_Extractor(),
            drawing_analyzer=_Extractor(),
            ifc_validator=SimpleNamespace(validate=lambda *a, **k: []),
            remark_generator=TemplateRemarkGenerator(),
            audit_report_store=store,
        )
        report = use_case.execute(
            ValidationRequest(
                request_id="persist-1",
                ifc_path=Path("sample.ifc"),
                requirement_source=RequirementSource(text="Width 1 m"),
                calculation_source=RequirementSource(
                    text="Width 1 mm",
                    source_kind=SourceKind.CALCULATION,
                ),
            )
        )
        self.assertEqual(store.saves, 1)
        self.assertIsNotNone(store.get(report.report_id))
        cross = [i for i in report.issues if i.category is FindingCategory.CROSS_DOCUMENT]
        self.assertTrue(cross, "1 m vs 1 mm must survive report persist")


class A13PassportSourcesTests(unittest.TestCase):
    def test_text_only_lists_inline_sources(self) -> None:
        from aerobim.application.use_cases.analyze_project_package import (
            AnalyzeProjectPackageUseCase,
        )

        use_case = AnalyzeProjectPackageUseCase.__new__(AnalyzeProjectPackageUseCase)
        request = ValidationRequest(
            request_id="p",
            ifc_path=None,
            requirement_source=RequirementSource(text="inline requirement"),
            technical_spec_source=RequirementSource(
                text="spec", source_kind=SourceKind.TECHNICAL_SPECIFICATION
            ),
            calculation_source=RequirementSource(text="calc", source_kind=SourceKind.CALCULATION),
            drawing_sources=(DrawingSource(text="wall 200 mm", format="txt"),),
        )
        ingested = SimpleNamespace(raster_issues=())
        rows = use_case._passport_sources(request, ingested)
        names = {row["name"] for row in rows}
        self.assertIn("requirement.inline.txt", names)
        self.assertIn("technical-spec.inline.txt", names)
        self.assertIn("calculation.inline.txt", names)
        self.assertTrue(
            all("/" not in str(row["name"]) and "\\" not in str(row["name"]) for row in rows)
        )


class B01MixedPackageKindTests(unittest.TestCase):
    def test_public_ifc_plus_tenant_drawing_is_confidential(self) -> None:
        request = ValidationRequest(
            request_id="mix",
            ifc_path=Path("samples/ifc/wall.ifc"),
            requirement_source=RequirementSource(text="x"),
            drawing_sources=(
                DrawingSource(path=Path("var/tenants/acme/uploads/secret.pdf"), format="pdf"),
            ),
        )
        self.assertEqual(_advisory_object_kind(request), "ifc")


if __name__ == "__main__":
    unittest.main()
